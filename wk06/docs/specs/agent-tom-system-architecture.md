# System Architecture Spec — FOI Multi-Agent CLI

**Author:** Agent-Tom  
**Date:** 2026-06-24  
**Status:** Draft (agent-prefixed — not yet consolidated)

---

## 1. Solution Directory Layout

```
solution/
├── main.py              # CLI entry: `index` and `process` commands
├── pipeline.py          # Supervisor: orchestrates triage → compliance → draft → HITL
├── models.py            # All Pydantic schemas (single source of truth for data contracts)
├── rag.py               # Document indexing and retrieval (ChromaDB + embeddings)
├── cost_tracker.py      # Per-agent cost tracking via get_usage_metadata_callback
├── config.py            # Constants: model IDs, token costs, paths, env var names
├── agents/
│   ├── __init__.py
│   ├── triage.py        # Classify request topic/complexity (Haiku)
│   ├── compliance.py    # Exemption check via RAG retrieval (Sonnet)
│   └── response.py      # Draft FOI response letter (Sonnet)
├── hitl.py              # Human-in-the-loop checkpoint, display, and audit trail writer
├── documents/
│   ├── foi_requests/    # Input: .txt FOI request files
│   └── policies/        # Input: .txt policy documents for RAG indexing
├── output/              # Per-request JSON result files (auto-created)
├── chroma_db/           # ChromaDB persistent store (auto-created on index)
├── .env                 # ANTHROPIC_API_KEY, OPERATOR_ID, EMBEDDING_PROVIDER
├── requirements.txt
└── AI_LOG.md
```

**Key design decision:** One module per concern. Agents do not import from each other —
they only take Pydantic models in and return Pydantic models out. `pipeline.py` wires
them together. This makes each agent independently testable.

---

## 2. Pipeline Data Flow

```
FOI Request File (.txt)
       │
       │  read_text()
       ▼
 ┌─────────────┐
 │ triage.py   │  Model: claude-haiku-4-5-20251001
 │             │  Input:  request_text: str
 │             │  Output: TriageResult
 └──────┬──────┘
        │
        │  TriageResult + request_text
        ▼
 ┌─────────────────┐
 │  rag.py         │  retrieve top-k chunks from ChromaDB
 │  (retrieval)    │  Query: request_text (+ topic from triage)
 │                 │  Output: list[PolicyChunk]
 └────────┬────────┘
          │
          │  request_text + TriageResult + list[PolicyChunk]
          ▼
 ┌────────────────┐
 │ compliance.py  │  Model: claude-sonnet-4-6
 │                │  Input:  request_text, triage, chunks
 │                │  Output: ComplianceResult
 └───────┬────────┘
         │
         │  request_text + TriageResult + ComplianceResult
         ▼
 ┌───────────────┐
 │ response.py   │  Model: claude-sonnet-4-6
 │               │  Input:  request_text, triage, compliance
 │               │  Output: DraftResult
 └──────┬────────┘
        │
        │  TriageResult + list[PolicyChunk] + ComplianceResult + DraftResult
        ▼
 ┌──────────────┐
 │  hitl.py     │  Display evidence; prompt operator; write audit entry
 │              │  Input:  all above + request metadata
 │              │  Output: AuditEntry
 └──────┬───────┘
        │
        │  RequestResult (all stages + cost)
        ▼
  output/<request_id>-result.json
```

Each agent call wraps its LLM invocation in a `get_usage_metadata_callback` context
manager. The `CostTracker` accumulates per-agent records; `pipeline.py` calls
`tracker.summary()` at the end of each request to populate `RequestResult.cost`.

---

## 3. Agent Interface Contracts (Pydantic Models)

These live in `models.py` and are shared by all modules. Agents always return a
typed Pydantic model, never a plain dict — this enables `with_structured_output()`
and validates LLM responses at runtime.

```python
from pydantic import BaseModel, Field
from typing import Literal


class TriageResult(BaseModel):
    topic: str = Field(description="Primary subject area, e.g. 'procurement', 'staffing'")
    complexity: Literal["high", "medium", "low"]
    summary: str = Field(description="One-sentence summary of what is being requested")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence")


class PolicyChunk(BaseModel):
    text: str
    source: str          # filename (e.g. 'foi-exemptions-guide.txt')
    chunk_id: str        # e.g. 'foi-exemptions-guide.txt:chunk-017'
    similarity_score: float


class ComplianceResult(BaseModel):
    exemptions_found: list[str] = Field(description="E.g. ['s43', 's40']")
    reasoning: str = Field(description="Explanation of why each exemption applies or not")
    policy_sources: list[str] = Field(description="Source filenames cited")
    chunk_ids: list[str] = Field(description="IDs of retrieved chunks used as evidence")
    recommendation: Literal["release", "partial_release", "withhold"]


class DraftResult(BaseModel):
    draft_letter: str = Field(description="Full text of the FOI response letter")
    evidence_summary: str = Field(description="Short summary of evidence for the reviewer")


class Modification(BaseModel):
    before: str
    after: str


class AuditEntry(BaseModel):
    timestamp: str           # ISO 8601 UTC, e.g. "2026-06-24T14:32:07Z"
    request_id: str          # From the FOI request reference field
    request_file: str        # Filename
    operator: str            # From OPERATOR_ID env var or prompted at runtime
    decision: Literal["approved", "rejected", "modified"]
    evidence_refs: list[str] # chunk_ids displayed to the reviewer
    exemptions_applied: list[str]
    compliance_recommendation: str
    modification: Modification | None = None


class AgentCost(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float


class RequestCost(BaseModel):
    triage: AgentCost
    compliance: AgentCost
    response: AgentCost
    total_usd: float


class RequestResult(BaseModel):
    request_file: str
    request_id: str
    triage: TriageResult
    retrieved_chunks: list[PolicyChunk]
    compliance: ComplianceResult
    draft: DraftResult
    audit: AuditEntry
    cost: RequestCost
```

---

## 4. Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| LLM — triage | `claude-haiku-4-5-20251001` | High-volume, well-defined classification; lowest cost |
| LLM — compliance, response | `claude-sonnet-4-6` | Complex reasoning; higher accuracy on exemption analysis |
| LLM framework | `langchain-anthropic` (`ChatAnthropic`) | Structured output, retry, callbacks — avoids boilerplate |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface` | Local; no API cost; adequate for policy doc similarity |
| Vector store | `langchain-chroma` (`Chroma`) | Lightweight; embedded (no separate server); persistent |
| Text splitting | `RecursiveCharacterTextSplitter` (built-in LangChain) | Handles paragraph/sentence boundaries in policy docs |
| Cost tracking | `langchain_core.callbacks.get_usage_metadata_callback` | Built-in context manager; no custom handler needed |
| Structured I/O | Pydantic v2 + `llm.with_structured_output(Model)` | Runtime validation of LLM responses |
| Retry / backoff | `tenacity` | `@retry(wait=wait_exponential(multiplier=2))` for rate limits |
| Logging | Python `logging` + JSON formatter | Structured; zero cost; audit-compliant |
| Config | `python-dotenv` | Load `.env` secrets; no hardcoded keys |

### Token Cost Reference

> These are estimated costs for reference. Confirm against Anthropic pricing page before
> committing. The `config.py` module holds the authoritative values for cost calculation.

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| `claude-haiku-4-5-20251001` | $0.00025 | $0.00125 |
| `claude-sonnet-4-6` | $0.003 | $0.015 |

Typical cost per FOI request (rough estimate):
- Triage (haiku): ~500 tokens → ~$0.0003
- Compliance (sonnet): ~2000 tokens → ~$0.008
- Response (sonnet): ~2500 tokens → ~$0.010
- Total: ~$0.018 per request

---

## 5. Configuration (`.env` and `config.py`)

**`.env` variables:**

```
ANTHROPIC_API_KEY=sk-ant-...
OPERATOR_ID=tom.farley@dept.gov.uk   # Logged in every audit entry
EMBEDDING_PROVIDER=huggingface       # or 'openai' if HuggingFace blocked
OPENAI_API_KEY=                      # Only needed if EMBEDDING_PROVIDER=openai
```

**`config.py` constants:**

```python
TRIAGE_MODEL = "claude-haiku-4-5-20251001"
COMPLIANCE_MODEL = "claude-sonnet-4-6"
RESPONSE_MODEL = "claude-sonnet-4-6"

TOKEN_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4-6":         {"input": 0.003,   "output": 0.015},
}

EMBEDDING_MODEL_HF = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_COLLECTION = "foi_policies"
RAG_TOP_K = 5
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
```

---

## 6. Open Questions / Gaps (for research phase)

1. Does `langchain-anthropic` `with_structured_output()` use tool-calling or JSON mode
   under the hood? This affects prompt design.
2. What is the exact `on_llm_end` callback signature for Claude via LangChain — does it
   include input/output token counts separately?
3. Can `ChatAnthropic` be configured with `max_retries` natively, or does `tenacity`
   always need to be added?
4. Confirm `langchain-chroma` API: is it `Chroma.from_documents()` or
   `Chroma.add_documents()` for adding to an existing collection?

These are resolved in `learning_materials/` and the answers fed back into
`docs/plans/agent-tom-tooling.md`.

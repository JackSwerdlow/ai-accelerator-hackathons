# MVP Spec — FOI Multi-Agent CLI

**Status:** Consolidated — gates implementation  
**Consolidates:** `system-architecture-agent-tom.md`, `supervisor-hitl-agent-tom.md`  
**Date:** 2026-06-24  
**Scope:** Everything required for "Excellent" on all four rubric axes. Anything not in this document is either in `stretch-agent-tom.md` or `production-agent-tom.md`.

---

## What Is In Scope

| Rubric axis | What this spec delivers |
|-------------|------------------------|
| **Automation value** | Full triage → RAG → compliance → response pipeline; evidence-backed exemption analysis |
| **Reliability** | Structured fallbacks per step; tenacity retry; circuit breaker; no crashes on API errors or malformed input |
| **Governance** | HITL gate with rich evidence display; mandatory operator decision; append-only audit trail with operator identity and evidence refs |
| **Cost awareness** | Per-agent token + cost tracking; per-request breakdown in output JSON; end-of-run cost summary |

## What Is Explicitly Out of Scope for MVP

- Citation verification after compliance → **`stretch-agent-tom.md` S1**
- Triage override with pipeline re-run at HITL → **`stretch-agent-tom.md` S2**
- Policy staleness warning → **`stretch-agent-tom.md` S3**
- Duplicate/similar request detection → **`stretch-agent-tom.md` S4**
- Extended vexatious/malformed flagging → **`stretch-agent-tom.md` S5**
- ATRS record generation → **`stretch-agent-tom.md` S6**
- Bias monitoring, drift detection, precedent store, multi-department routing → **`production-agent-tom.md`**

---

## 1. Solution Directory Layout

```
solution/
├── main.py              # CLI entry: `index` and `process` commands
├── pipeline.py          # Supervisor: orchestrates triage → RAG → compliance → response → HITL
├── models.py            # All Pydantic schemas (single source of truth for data contracts)
├── rag.py               # Document indexing and retrieval (ChromaDB + embeddings)
├── cost_tracker.py      # Per-agent cost tracking via get_usage_metadata_callback
├── config.py            # Constants: model IDs, token costs, paths, env var names
├── agents/
│   ├── __init__.py
│   ├── triage.py        # Classify request topic/complexity/clarity (Haiku)
│   ├── compliance.py    # Exemption check via RAG retrieval (Sonnet)
│   └── response.py      # Draft FOI response letter (Sonnet)
├── hitl.py              # Human-in-the-loop checkpoint, display, and audit trail writer
├── documents/
│   ├── foi_requests/    # Input: .txt FOI request files
│   └── policies/        # Input: .txt policy documents for RAG indexing
├── output/              # Per-request JSON + append-only audit_trail.jsonl (auto-created)
├── chroma_db/           # ChromaDB persistent store (auto-created on index)
├── tests/
│   ├── unit/            # Zero-cost tests using FakeListChatModel
│   └── integration/     # Low-cost tests using real Haiku on sample requests
├── .env                 # ANTHROPIC_API_KEY, OPERATOR_ID, EMBEDDING_PROVIDER
├── .env.example         # Template — commit this, never commit .env
└── requirements.txt
```

**Key design principle:** One module per concern. Agents only exchange Pydantic models — they never import from each other. `pipeline.py` wires them together. This makes each agent independently testable and replaceable.

---

## 2. Pipeline Data Flow

```
FOI Request File (.txt)
       │
       │  read_text()
       ▼
 ┌─────────────┐
 │ triage.py   │  Model: claude-haiku-4-5-20251001
 │             │  In:  request_text: str
 │             │  Out: TriageResult
 └──────┬──────┘
        │
        │  TriageResult + request_text
        ▼
 ┌─────────────────┐
 │  rag.py         │  retrieve top-k chunks from ChromaDB
 │  (retrieval)    │  Query: request_text + triage.topic
 │                 │  Out: list[PolicyChunk]
 └────────┬────────┘
          │
          │  request_text + TriageResult + list[PolicyChunk]
          ▼
 ┌────────────────┐
 │ compliance.py  │  Model: claude-sonnet-4-6
 │                │  In:  request_text, triage, chunks
 │                │  Out: ComplianceResult
 └───────┬────────┘
         │
         │  request_text + TriageResult + ComplianceResult
         ▼
 ┌───────────────┐
 │ response.py   │  Model: claude-sonnet-4-6
 │               │  In:  request_text, triage, compliance
 │               │  Out: DraftResult
 └──────┬────────┘
        │
        │  TriageResult + list[PolicyChunk] + ComplianceResult + DraftResult
        ▼
 ┌──────────────┐
 │  hitl.py     │  Display evidence; prompt operator; write audit entry
 │              │  In:  all above + request_file path
 │              │  Out: AuditEntry
 └──────┬───────┘
        │
        │  RequestResult (all stages + cost)
        ▼
  output/<request_id>-result.json
  output/audit_trail.jsonl        (appended)
```

Each agent call wraps its LLM invocation in a `get_usage_metadata_callback` context manager. The `CostTracker` in `cost_tracker.py` accumulates per-agent records; `pipeline.py` calls `tracker.summary()` to populate `RequestResult.cost`.

---

## 3. Data Models (`models.py`)

All Pydantic v2. These are the authoritative schemas — any discrepancy in other documents defers to this.

```python
from pydantic import BaseModel, Field
from typing import Literal


class TriageResult(BaseModel):
    topic: str = Field(description="Primary subject area, e.g. 'procurement', 'staffing'")
    complexity: Literal["high", "medium", "low"]
    summary: str = Field(description="One-sentence summary of what is being requested")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence 0–1")
    clarification_recommended: bool = Field(
        default=False,
        description="True if the request is ambiguous, misquotes legislation, or is of "
                    "unclear scope — operator should seek clarification before processing"
    )
    clarification_reason: str | None = Field(
        default=None,
        description="If clarification_recommended, brief explanation of why"
    )


class PolicyChunk(BaseModel):
    text: str
    source: str        # e.g. 'foi-exemptions-guide.txt'
    chunk_id: str      # e.g. 'foi-exemptions-guide.txt:chunk-017'
    similarity_score: float


class ComplianceResult(BaseModel):
    exemptions_found: list[str] = Field(description="E.g. ['s43', 's40']")
    reasoning: str = Field(description="Explanation of why each exemption applies or not")
    policy_sources: list[str] = Field(description="Source filenames cited")
    chunk_ids: list[str] = Field(description="IDs of retrieved chunks used as evidence")
    recommendation: Literal["release", "partial_release", "withhold"]
    third_party_notification_required: bool = Field(
        default=False,
        description="True if s.41 (confidence) or s.40(2) exemptions require notifying "
                    "a third party before disclosure"
    )


class DraftResult(BaseModel):
    draft_letter: str = Field(description="Full text of the FOI response letter")
    evidence_summary: str = Field(description="Short summary of evidence for the reviewer")


class Modification(BaseModel):
    before: str
    after: str


class AuditEntry(BaseModel):
    timestamp: str              # ISO 8601 UTC e.g. "2026-06-24T14:32:07Z"
    request_id: str             # From the FOI request reference field
    request_file: str
    operator: str               # From OPERATOR_ID env var or runtime prompt
    decision: Literal["approved", "rejected", "modified"]
    evidence_refs: list[str]    # chunk_ids shown to the reviewer
    exemptions_applied: list[str]
    compliance_recommendation: str
    triage_topic: str           # Captured for audit; may differ from final if overridden
    triage_confidence: float
    modification: Modification | None = None
    rejection_reason: str | None = None   # present when decision == "rejected"
    cost_usd: float = 0.0                 # total pipeline cost for this request


class AgentCost(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
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

## 4. Supervisor Orchestration (`pipeline.py`)

The supervisor is a **plain function, not an LLM agent**. It sequences deterministic calls and enforces the HITL gate.

### 4.1 Call sequence

```
process_request(request_file, request_text, llm_haiku, llm_sonnet, rag, tracker)
    │
    ├─ [1] triage_agent(request_text, llm_haiku, tracker)
    │       → TriageResult  OR  fallback TriageResult on failure
    │
    ├─ [2] rag.retrieve(request_text, triage.topic)
    │       → list[PolicyChunk]  OR  [] on failure
    │
    ├─ [3] compliance_agent(request_text, triage, chunks, llm_sonnet, tracker)
    │       → ComplianceResult  OR  fallback ComplianceResult on failure
    │
    ├─ [4] response_agent(request_text, triage, compliance, llm_sonnet, tracker)
    │       → DraftResult  OR  fallback DraftResult on failure
    │
    ├─ [5] hitl_gate(triage, chunks, compliance, draft, request_file)
    │       → AuditEntry  (MANDATORY — never skipped or auto-approved)
    │
    └─ [6] assemble RequestResult → write output/<id>-result.json
                                  → append to output/audit_trail.jsonl
```

### 4.2 Error handling per step

| Step | Failure | Fallback |
|------|---------|----------|
| Triage | API error / parse error | `TriageResult(topic="unknown", complexity="high", summary="Classification failed — manual review required", confidence=0.0, clarification_recommended=True, clarification_reason="Triage agent failed")` |
| RAG retrieve | ChromaDB not indexed / error | `[]` — compliance proceeds with empty context |
| Compliance | API error / parse error | `ComplianceResult(exemptions_found=[], reasoning="Compliance check failed — manual exemption review required", policy_sources=[], chunk_ids=[], recommendation="withhold", third_party_notification_required=False)` |
| Response | API error / parse error | `DraftResult(draft_letter="[DRAFT GENERATION FAILED — officer must draft manually]", evidence_summary="See classification and compliance results above")` |
| HITL gate | `KeyboardInterrupt` / broken stdin | Re-raise — **never auto-approve** |

### 4.3 Retry and circuit breaker

- **Rate limits (HTTP 429):** `tenacity` `@retry(wait=wait_exponential(multiplier=2, min=1, max=60), stop=stop_after_attempt(5))` on each agent function.
- **Circuit breaker:** After 3 consecutive failures for the same agent across requests in a single run, mark that agent as "degraded", skip it for remaining requests, substitute its fallback, and log `WARNING`.

---

## 5. HITL Gate (`hitl.py`)

### 5.1 Display format

```
══════════════════════════════════════════════════════════════════════
  FOI REVIEW: request-001.txt  [FOI-2025-001]
══════════════════════════════════════════════════════════════════════

CLASSIFICATION
  Topic:      procurement
  Complexity: HIGH
  Confidence: 0.94
  Summary:    Request for IT consultancy contract names, values, and
              descriptions for financial years 2022-23 and 2023-24.

[⚠ CLARIFICATION RECOMMENDED: Request scope is ambiguous — no time
   period specified. Consider seeking clarification before processing.]
   (shown only when clarification_recommended == True)

POLICY EVIDENCE  (top 5 RAG chunks)
  ┌─ [1]  foi-exemptions-guide.txt  (similarity: 0.82)
  │       "Section 43 -- Commercial interests. Information is exempt
  │        if disclosure would prejudice the commercial interests..."
  ├─ [2]  data-handling-policy.txt  (similarity: 0.79)
  │       ...
  └─ [5]  foi-exemptions-guide.txt  (similarity: 0.68)
          ...

COMPLIANCE ANALYSIS
  Recommendation: PARTIAL RELEASE
  Exemptions:     s43 (commercial interests)
  Reasoning:      Contract names and total values are generally releasable.
                  Evaluation criteria and scoring are protected under s43.

[⚠ THIRD-PARTY NOTIFICATION MAY BE REQUIRED before disclosure.
   Verify s.41/s.40(2) obligations with your legal team.]
   (shown only when third_party_notification_required == True)

DRAFT RESPONSE  [AI-generated — review before approving]
──────────────────────────────────────────────────────────────────────
Dear Requester,
Thank you for your Freedom of Information request...
──────────────────────────────────────────────────────────────────────

DECISION
  [A] Approve — send draft as shown
  [R] Reject  — request will not proceed
  [M] Modify  — edit the draft before approving

>
```

### 5.2 Interaction flow

```
Decision prompt: A / R / M  (case-insensitive; re-prompts on invalid input)

If M (modify):
  "Enter the full revised response text. Submit an empty line to finish."
  > [multiline input until blank line]
  "Preview your modified response? [Y/n]: "
  [show modified text]
  "Confirm modification? [Y/n]: "
  If Y → decision = "modified"; record before/after in Modification
  If N → return to decision prompt

If R:
  "Enter rejection reason (optional, press Enter to skip): "
  [record in AuditEntry.rejection_reason]
```

### 5.3 Operator identity

`OPERATOR_ID` is read from `.env`. If absent, the gate prompts at runtime:
```
Operator ID not configured. Enter your name/email for the audit record:
```
This ensures every audit entry is attributed even in unconfigured environments.

### 5.4 Audit trail

Every decision is appended to `output/audit_trail.jsonl` (one JSON object per line, never overwritten). Rejected requests also write a result JSON — rejection is a decision on record.

Example entry (modified decision):
```json
{
  "timestamp": "2026-06-24T14:32:07Z",
  "request_id": "FOI-2025-001",
  "request_file": "request-001.txt",
  "operator": "tom.farley@dept.gov.uk",
  "decision": "modified",
  "triage_topic": "procurement",
  "triage_confidence": 0.94,
  "compliance_recommendation": "partial_release",
  "exemptions_applied": ["s43"],
  "evidence_refs": [
    "foi-exemptions-guide.txt:chunk-017",
    "data-handling-policy.txt:chunk-004"
  ],
  "modification": {
    "before": "...original draft...",
    "after":  "...operator's revised text..."
  },
  "rejection_reason": null,
  "cost_usd": 0.0182
}
```

### 5.5 End-of-run cost summary

```
══════════════════════════════════════════════════════════════════════
  COST SUMMARY — 3 requests processed
══════════════════════════════════════════════════════════════════════

  Agent        Model                        Calls  Tokens    Cost USD
  ────────────────────────────────────────────────────────────────────
  triage       claude-haiku-4-5-20251001       3    1,080    $0.0003
  compliance   claude-sonnet-4-6               3    6,165    $0.0261
  response     claude-sonnet-4-6               3    7,440    $0.0360
  ────────────────────────────────────────────────────────────────────
  TOTAL                                        9   14,685    $0.0624

  Results written to: output/
  Audit trail:        output/audit_trail.jsonl
══════════════════════════════════════════════════════════════════════
```

---

## 6. s.40 Personal Data Handling

When `"s40" in compliance_result.exemptions_found`, the response agent **must** receive an additional instruction in its prompt:

> "The compliance analysis has identified that this request engages the personal data exemption (s.40 FOIA 2000 / UK GDPR). Do not include any names, job titles, or details that could identify a specific individual in the response letter. Where personal data is relevant, refer to it in aggregate or anonymised terms only (e.g. 'staff members' not named individuals)."

This is not optional — a draft that names individuals whose data is protected under s.40 could constitute a data breach.

---

## 7. Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| LLM — triage | `claude-haiku-4-5-20251001` | Low cost; well-defined classification task |
| LLM — compliance, response | `claude-sonnet-4-6` | Complex legal reasoning; accuracy matters |
| LLM framework | `langchain-anthropic` (`ChatAnthropic`) | Structured output, callbacks, retry |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface` | Local; no API cost; adequate for policy doc similarity |
| Vector store | `langchain-chroma` (`Chroma`) | Embedded (no separate server); persistent on disk |
| Text splitting | `RecursiveCharacterTextSplitter` | Respects paragraph/sentence boundaries |
| Cost tracking | `langchain_core.callbacks.get_usage_metadata_callback` | Built-in; no custom handler needed |
| Structured I/O | Pydantic v2 + `llm.with_structured_output(Model)` | Runtime LLM response validation |
| Retry | `tenacity` | Exponential backoff for rate limits |
| Logging | Python `logging` + JSON formatter | Structured; zero cost; audit-compliant |
| Config | `python-dotenv` | Load `.env` secrets; no hardcoded keys |

**Note:** `with_structured_output()` uses **tool-calling** under the hood for Anthropic models (not JSON mode). This means the Pydantic field `description` strings are sent to the model as tool parameter descriptions — write them clearly, as they guide output quality.

### Token cost reference

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| `claude-haiku-4-5-20251001` | $0.00025 | $0.00125 |
| `claude-sonnet-4-6` | $0.003 | $0.015 |

Verify against https://www.anthropic.com/pricing before committing to `config.py`. Rough estimate per FOI request: ~$0.018–$0.025 depending on request length and policy doc coverage.

---

## 8. Configuration

**`.env` (never committed — provide `.env.example`):**
```
ANTHROPIC_API_KEY=sk-ant-...
OPERATOR_ID=officer@dept.gov.uk
EMBEDDING_PROVIDER=huggingface       # or 'openai' if HuggingFace download blocked
OPENAI_API_KEY=                      # only needed if EMBEDDING_PROVIDER=openai
```

**`config.py`:**
```python
TRIAGE_MODEL    = "claude-haiku-4-5-20251001"
COMPLIANCE_MODEL = "claude-sonnet-4-6"
RESPONSE_MODEL  = "claude-sonnet-4-6"

TOKEN_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4-6":         {"input": 0.003,   "output": 0.015},
}

EMBEDDING_MODEL_HF = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_COLLECTION  = "foi_policies"
RAG_TOP_K          = 5
CHUNK_SIZE         = 500
CHUNK_OVERLAP      = 100
```

---

## 9. Testing Approach

See `docs/plans/tooling-agent-tom.md §5` for full detail. Summary:

**Unit tests (zero API cost):** Use `FakeListChatModel` from `langchain_core.language_models.fake` to inject fixed responses. Test each agent's parsing logic, fallback behaviour, and cost tracker call.

**Integration tests (low cost):** Run the full pipeline against real `claude-haiku-4-5-20251001` on the 3 sample requests. Total cost < $0.01. Assert on broad correctness (topic in expected set, exemption section numbers present).

**Do not use `claude-sonnet-4-6` in automated tests.** Run Sonnet manually for end-to-end quality checks only.

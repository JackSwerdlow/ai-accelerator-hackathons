# Implementation Plan — FOI Multi-Agent CLI

**Author:** agent-tom
**Date:** 2026-06-24
**Status:** Active plan — single source of truth for all implementation detail.

**Specs:**
- `docs/specs/mvp-spec-agent-tom.md` — functional requirements, acceptance criteria, pipeline overview
- `docs/specs/stretch-spec-agent-tom.md` — post-MVP goals (not implemented here)
- `docs/specs/production-spec-agent-tom.md` — real-deployment requirements (not implemented here)

**Architecture:**
- `docs/architecture/system-design-agent-tom.md` — data model decisions, supervisor design, HITL design
- `docs/architecture/tooling-agent-tom.md` — LLM, embedding, vector store, and library choices

**Project management:**
- `docs/RAID-log-agent-tom.md` — risks, assumptions, issues, dependencies; pre-implementation blockers I7 and I8 must be resolved before `rag.py` is coded

**Research:**
- `docs/research/foi-landscape-synthesis.md` — FOI domain landscape, key risks and mitigations
- `docs/research/cache-atrs-requirements.md` — ATRS registration requirements
- `docs/research/cache-uk-ai-playbook-governance.md` — UK AI Playbook governance principles
- `docs/research/cache-ico-ai-foi-guidance-2026.md` — ICO guidance on AI use in FOI (May 2026)
- `docs/research/cache-ai-redaction-uk-authorities-arxiv.md` — AI redaction research findings
- `docs/research/cache-vidizmo-foi-triage.md` — FOI triage AI findings

---

## 1. Solution directory layout

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

**Key design principle:** One module per concern. Agents only exchange Pydantic models — they
never import from each other. `pipeline.py` wires them together. This makes each agent
independently testable and replaceable.

---

## 2. `requirements.txt`

```
# LLM integration
langchain-anthropic>=0.3.0
langchain-core>=0.3.0

# Vector store + RAG
langchain-chroma>=0.1.0
chromadb>=1.0.0

# Embeddings (local, no API cost)
langchain-huggingface>=0.1.0
sentence-transformers>=3.0.0

# Text splitting (built into langchain)
langchain-text-splitters>=0.3.0

# Structured I/O
pydantic>=2.0.0

# Retry / backoff
tenacity>=8.0.0

# Config
python-dotenv>=1.0.0
```

**OpenAI fallback** (only if `EMBEDDING_PROVIDER=openai`):
```
langchain-openai>=0.2.0  # optional; omit if not using OpenAI embeddings
```

> Pin exact versions after `pip install -r requirements.txt` succeeds in the target
> environment: `pip freeze > requirements.txt`. Do not ship unpinned minimum versions.

---

## 3. `config.py`

```python
import os

TRIAGE_MODEL     = "claude-haiku-4-5-20251001"
COMPLIANCE_MODEL = "claude-sonnet-4-6"
RESPONSE_MODEL   = "claude-sonnet-4-6"

TOKEN_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4-6":         {"input": 0.003,   "output": 0.015},
}

EMBEDDING_MODEL_HF = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_COLLECTION  = "foi_policies"
RAG_TOP_K          = 5
CHUNK_SIZE         = 500
CHUNK_OVERLAP      = 100

CHROMA_PATH = "chroma_db"
OUTPUT_PATH = "output"
AUDIT_TRAIL_FILE = "output/audit_trail.jsonl"

# Staleness threshold for policy index (stretch goal S3)
STALE_INDEX_DAYS = int(os.getenv("STALE_INDEX_DAYS", "30"))
```

> Verify TOKEN_COSTS against https://www.anthropic.com/pricing before committing.

---

## 4. `.env.example`

```
ANTHROPIC_API_KEY=sk-ant-...
OPERATOR_ID=officer@dept.gov.uk
EMBEDDING_PROVIDER=huggingface       # or 'openai' if HuggingFace download blocked
OPENAI_API_KEY=                      # only needed if EMBEDDING_PROVIDER=openai
```

Never commit `.env`. Always commit `.env.example`.

---

## 5. Pydantic data models (`models.py`)

All Pydantic v2. These are the authoritative schemas — any discrepancy in other documents
defers to this section.

```python
from pydantic import BaseModel, Field
from typing import Literal


class TriageResult(BaseModel):
    topic: str = Field(
        description="Primary subject area of the FOI request. One of: "
                    "finance_spending, staffing_hr, procurement_commercial, "
                    "internal_deliberations, personal_data, other"
    )
    complexity: Literal["high", "medium", "low"] = Field(
        description="Handling effort and risk level. high = qualified exemption needing "
                    "PIT, s41 confidence/third-party, s12 cost-limit risk, or broad scope. "
                    "medium = multi-part or one likely exemption. low = single clear ask."
    )
    summary: str = Field(description="One-sentence summary of what is being requested")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Classification confidence 0–1"
    )
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
    exemptions_found: list[str] = Field(
        description="FOIA exemption sections that apply, e.g. ['s43', 's40']"
    )
    reasoning: str = Field(
        description="Explanation of why each exemption applies or does not apply, "
                    "with a verbatim quote from a retrieved policy chunk for each claimed exemption"
    )
    policy_sources: list[str] = Field(
        description="Source document filenames cited"
    )
    chunk_ids: list[str] = Field(
        description="IDs of retrieved chunks used as evidence (format: filename:chunk-NNN)"
    )
    recommendation: Literal["release", "partial_release", "withhold"] = Field(
        description="Disclosure recommendation based on exemption analysis"
    )
    third_party_notification_required: bool = Field(
        default=False,
        description="True if s.41 (confidence) or s.40(2) exemptions require notifying "
                    "a third party before disclosure"
    )


class DraftResult(BaseModel):
    draft_letter: str = Field(description="Full text of the FOI response letter")
    evidence_summary: str = Field(
        description="Short summary of the evidence basis for the reviewer"
    )


class Modification(BaseModel):
    before: str = Field(description="The AI-generated draft text before operator modification")
    after: str = Field(description="The operator's revised text")


class AuditEntry(BaseModel):
    timestamp: str              # ISO 8601 UTC e.g. "2026-06-24T14:32:07Z"
    request_id: str             # From the FOI request reference field
    request_file: str
    operator: str               # From OPERATOR_ID env var or runtime prompt
    decision: Literal["approved", "rejected", "modified"]
    evidence_refs: list[str]    # chunk_ids shown at the HITL gate
    exemptions_applied: list[str]
    compliance_recommendation: str   # AI's original recommendation before operator decision
    triage_topic: str           # Captured for audit; enables performance monitoring
    triage_confidence: float
    modification: Modification | None = None   # present when decision == "modified"
    rejection_reason: str | None = None        # present when decision == "rejected"
    cost_usd: float = 0.0                      # total pipeline cost for this request


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

## 6. Supervisor call sequence (`pipeline.py`)

The supervisor is a **plain function, not an LLM agent**. It sequences deterministic calls
and enforces the HITL gate.

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

---

## 7. Error handling table

| Step | Failure condition | Fallback value |
|------|-------------------|----------------|
| Triage | API error / parse error | `TriageResult(topic="unknown", complexity="high", summary="Classification failed — manual review required", confidence=0.0, clarification_recommended=True, clarification_reason="Triage agent failed")` |
| RAG retrieve | ChromaDB not indexed / error | `[]` — compliance proceeds with empty context |
| Compliance | API error / parse error | `ComplianceResult(exemptions_found=[], reasoning="Compliance check failed — manual exemption review required", policy_sources=[], chunk_ids=[], recommendation="withhold", third_party_notification_required=False)` |
| Response | API error / parse error | `DraftResult(draft_letter="[DRAFT GENERATION FAILED — officer must draft manually]", evidence_summary="See classification and compliance results above")` |
| HITL gate | `KeyboardInterrupt` / broken stdin | Re-raise — **never auto-approve** |

---

## 8. Retry and circuit breaker config

**Rate limits (HTTP 429):** Apply `tenacity` decorator to each agent function:

```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=2, min=1, max=60),
    stop=stop_after_attempt(5)
)
def triage_agent(request_text, llm, tracker):
    ...
```

**Circuit breaker:** After 3 consecutive failures for the same agent across requests in a
single run, mark that agent as "degraded", skip it for remaining requests, substitute its
fallback, and log `WARNING`.

Track consecutive failures per agent in a dict in the supervisor:
```python
failures = {"triage": 0, "compliance": 0, "response": 0}
CIRCUIT_BREAKER_THRESHOLD = 3
```

---

## 9. HITL display format

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

---

## 10. HITL interaction flow

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

**Operator identity capture:**

`OPERATOR_ID` is read from `.env`. If absent, the gate prompts at runtime:
```
Operator ID not configured. Enter your name/email for the audit record:
```
This ensures every audit entry is attributed even in unconfigured environments.

---

## 11. Audit trail JSONL example entry

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
    "before": "...original AI-generated draft...",
    "after":  "...operator's revised text..."
  },
  "rejection_reason": null,
  "cost_usd": 0.0182
}
```

---

## 12. End-of-run cost summary display format

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

## 13. s.40 exact prompt instruction

When `"s40" in compliance_result.exemptions_found`, the response agent **must** receive
this additional instruction appended to its system prompt or user message:

> "The compliance analysis has identified that this request engages the personal data
> exemption (s.40 FOIA 2000 / UK GDPR). Do not include any names, job titles, or details
> that could identify a specific individual in the response letter. Where personal data is
> relevant, refer to it in aggregate or anonymised terms only (e.g. 'staff members' not
> named individuals)."

This is not optional — a draft that names individuals whose data is protected under s.40
could constitute a data breach.

---

## 14. `CostTracker` class (`cost_tracker.py`)

```python
from langchain_core.callbacks import get_usage_metadata_callback
from config import TOKEN_COSTS


class CostTracker:
    def __init__(self):
        self.records: list[dict] = []

    def track(self, agent_name: str, model: str, llm_call_fn, *args, **kwargs):
        with get_usage_metadata_callback() as cb:
            result = llm_call_fn(*args, **kwargs)
        usage = cb.usage_metadata.get(model, {})
        rates = TOKEN_COSTS.get(model, {"input": 0.0, "output": 0.0})
        cost = (
            usage.get("input_tokens", 0) / 1000 * rates["input"] +
            usage.get("output_tokens", 0) / 1000 * rates["output"]
        )
        self.records.append({
            "agent": agent_name,
            "model": model,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost_usd": cost,
        })
        return result

    def summary(self) -> dict:
        by_agent = {}
        for r in self.records:
            ag = r["agent"]
            if ag not in by_agent:
                by_agent[ag] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                }
            by_agent[ag]["calls"] += 1
            by_agent[ag]["input_tokens"] += r["input_tokens"]
            by_agent[ag]["output_tokens"] += r["output_tokens"]
            by_agent[ag]["cost_usd"] += r["cost_usd"]
        return {
            "by_agent": by_agent,
            "total_usd": sum(r["cost_usd"] for r in self.records),
        }
```

Full primer on the LangChain callback system: `learning_materials/langchain-callbacks.md`.

---

## 15. Logging config (`main.py`)

```python
import logging
import json


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        })


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
```

All agent LLM calls emit a structured `INFO` log with `event`, `agent`, `model`,
`input_tokens`, `output_tokens`, `cost_usd` fields.

---

## 16. Testing approach

**Two-tier strategy:**

### Unit tests (zero API cost)

Use `FakeListChatModel` from `langchain_core.language_models.fake` to inject fixed
responses. Test each agent's:
- Parsing logic (LLM response → correct Pydantic model)
- Fallback behaviour (malformed response or exception → correct fallback)
- Cost tracker call (called exactly once per agent invocation)

```python
from langchain_core.language_models.fake import FakeListChatModel

fake_llm = FakeListChatModel(responses=['{"topic":"procurement","complexity":"high",...}'])
result = triage_agent("...request text...", fake_llm, tracker)
assert result.topic == "procurement"
```

### Integration tests (low cost)

Run the full pipeline against real `claude-haiku-4-5-20251001` on the 3 sample requests
in `documents/foi_requests/`. Haiku is cheap enough that 3 requests cost < $0.01 total.
Assert on broad correctness: topic in expected set, exemption section numbers present in
compliance output.

**Do not use `claude-sonnet-4-6` in automated tests.** Run Sonnet only in manual
end-to-end quality checks.

---

## 17. Build order

### Phase 1 — Foundation (no LLM calls)

1. `requirements.txt` + `.env.example` — pin all dependencies
2. `config.py` — all constants in one place; nothing hardcoded elsewhere
3. `models.py` — all data schemas upfront; agents exchange these, never raw dicts
4. `rag.py` — index policy docs into ChromaDB; retrieve top-k chunks by query
5. `cost_tracker.py` — wrap the LangChain usage callback; accumulate per-agent records

Gate: index runs cleanly against the two policy docs before moving on.

### Phase 2 — Agents

6. `agents/triage.py` — classify topic, complexity, summary; conservative fallback on
   failure (topic=unknown, complexity=high)
7. `agents/compliance.py` — takes triage output + retrieved chunks; identifies exemptions
   with citations; s40 flag triggers additional privacy instruction to downstream agents
8. `agents/response.py` — takes triage + compliance; drafts formal FOI letter grounded
   only in compliance findings

Each agent wraps its LLM call in retry logic and returns a structured fallback on error
rather than raising.

### Phase 3 — Supervisor + HITL

9. `pipeline.py` — sequences the four steps (triage → retrieve → compliance → response →
   gate) over a shared case record; circuit breaker disables a failing agent after 3
   consecutive errors; batch mode logs per-request status and running cost
10. `hitl.py` — displays evidence (retrieved chunks, classification, exemption reasoning,
    draft) before prompting; accept/reject/modify with operator identity captured; appends
    decision to append-only audit trail
11. `main.py` — `index` and `process` CLI entry points

### Phase 4 — Tests + polish

12. Unit tests — inject fake LLM responses to test each agent's parse logic and fallback
    paths without API calls
13. Integration test — run full pipeline on one sample request against real Haiku; assert
    topic and exemption sections present
14. `AI_LOG.md` — minimum 3 entries covering at least one doc/process task and two code
    tasks

---

## 18. Project initialisation checklist

Before writing any implementation code:

- [ ] Copy sample documents from `starter/documents/` to `solution/documents/`
- [ ] Create `solution/.env` from `solution/.env.example` template
- [ ] Confirm `ANTHROPIC_API_KEY` is set and valid
- [ ] Create and activate a Python virtual environment
- [ ] Run `pip install -r requirements.txt` — verify no errors
- [ ] Run `python main.py index` — verify ChromaDB is created and chunk count > 0
- [ ] Run `python main.py process documents/foi_requests/request-001.txt` — verify
      pipeline runs end-to-end (stubs fine at this point; confirm no import errors)

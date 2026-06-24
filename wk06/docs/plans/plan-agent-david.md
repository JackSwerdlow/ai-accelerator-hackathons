# Implementation Plan — FOI Multi-Agent CLI

**Author:** agent-david  
**Date:** 2026-06-24  
**Status:** Draft  
**Synthesises:** `docs/specs/Agent-Jack-SPEC.md`, `docs/specs/mvp-agent-tom.md`, `docs/plans/tooling-agent-tom.md`

---

## What we're building

A CLI tool that takes a folder of FOI request `.txt` files and for each one: triages it, retrieves relevant policy chunks via RAG, checks for exemptions, drafts a response, then holds for human approval. Nothing is finalised without an explicit operator decision. Every LLM call is cost-tracked and every decision goes into an audit trail.

---

## File layout

```
solution/
├── main.py           # CLI: `index` and `process` commands
├── pipeline.py       # Supervisor: sequences agents, enforces HITL gate
├── models.py         # Pydantic schemas — single source of truth for data contracts
├── rag.py            # ChromaDB indexing + retrieval
├── cost_tracker.py   # Per-agent token + cost logging
├── config.py         # Model IDs, token costs, paths, env var names
├── hitl.py           # Human review display, decision capture, audit trail writer
├── agents/
│   ├── triage.py     # Topic/complexity classification (Haiku)
│   ├── compliance.py # Exemption analysis over RAG chunks (Sonnet)
│   └── response.py   # Draft response letter (Sonnet)
├── documents/
│   ├── foi_requests/ # Input: .txt FOI request files
│   └── policies/     # Input: .txt policy documents
├── output/           # Per-request JSON + audit_trail.jsonl (auto-created)
├── chroma_db/        # ChromaDB persistent store (auto-created on index)
├── tests/
│   ├── unit/         # Zero-cost tests using FakeListChatModel
│   └── integration/  # Low-cost tests against real Haiku
├── .env.example
└── requirements.txt
```

---

## Tech stack

| Concern | Choice |
|---------|--------|
| LLM — triage | `claude-haiku-4-5-20251001` |
| LLM — compliance, response | `claude-sonnet-4-6` |
| LLM framework | `langchain-anthropic` (`ChatAnthropic`) |
| Structured output | Pydantic v2 + `llm.with_structured_output()` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` via `langchain-huggingface` |
| Vector store | `langchain-chroma` (persistent on disk) |
| Text splitting | `RecursiveCharacterTextSplitter` |
| Cost tracking | `langchain_core.callbacks.get_usage_metadata_callback` |
| Retry | `tenacity` — exponential backoff, max 5 attempts |
| Config | `python-dotenv` |

### Key parameters (`config.py`)

```python
TRIAGE_MODEL     = "claude-haiku-4-5-20251001"
COMPLIANCE_MODEL = "claude-sonnet-4-6"
RESPONSE_MODEL   = "claude-sonnet-4-6"

TOKEN_COSTS = {
    "claude-haiku-4-5-20251001": {"input": 0.00025, "output": 0.00125},
    "claude-sonnet-4-6":         {"input": 0.003,   "output": 0.015},
}

CHUNK_SIZE       = 500
CHUNK_OVERLAP    = 100
RAG_TOP_K        = 5
CHROMA_COLLECTION = "foi_policies"
```

---

## Build order

### Phase 1 — Foundation (no LLM calls)
1. `requirements.txt` + `.env.example`
2. `config.py` — constants only
3. `models.py` — all Pydantic schemas (see `mvp-agent-tom.md §3` for full definitions)
4. `rag.py` — `index_policies()` and `retrieve()` over the policy corpus
5. `cost_tracker.py` — wraps `get_usage_metadata_callback`, accumulates per-agent records

Verify: `python main.py index` indexes the two policy docs without error.

### Phase 2 — Agents
6. `agents/triage.py` — `with_structured_output(TriageResult)`, fallback on parse error
7. `agents/compliance.py` — takes triage + chunks, returns `ComplianceResult`; s40 prompt injection when flagged
8. `agents/response.py` — takes triage + compliance, returns `DraftResult`

Each agent: wrapped in `tenacity` retry, structured fallback on failure.

### Phase 3 — Supervisor + HITL
9. `pipeline.py` — sequences agents over a shared case record; circuit breaker after 3 consecutive failures per agent; batch mode with per-request status and cost display
10. `hitl.py` — structured review display (see `mvp-agent-tom.md §5.1`); approve/reject/modify flow; operator identity from `OPERATOR_ID` env var or runtime prompt; appends to `output/audit_trail.jsonl`
11. `main.py` — `index` and `process` CLI commands

### Phase 4 — Tests + polish
12. Unit tests using `FakeListChatModel` — cover parse logic and fallback paths for each agent
13. Integration test — full pipeline on `request-001.txt` against real Haiku (`< $0.01`)
14. `AI_LOG.md` — minimum 3 entries (at least one doc/process task, at least two code tasks)

---

## Key design decisions (from specs)

- **Supervisor is a plain function, not an LLM agent.** No dynamic routing.
- **HITL gate is never skipped.** `KeyboardInterrupt` re-raises rather than auto-approving.
- **Compliance fallback recommendation is `withhold`**, not `release` — fails safe.
- **s40 triggers an additional instruction** injected into the response agent prompt — do not name or describe identifiable individuals.
- **`with_structured_output()` uses tool-calling** for Anthropic models — write Pydantic field `description` strings carefully, they guide the model.
- **Audit trail is append-only** across runs — never overwrite `audit_trail.jsonl`.
- **Rejected requests still write a result JSON** — rejection is a decision on record.

---

## Open questions before implementation

1. **Operator identity CLI flag** — add `--operator` flag to `main.py` as override for non-interactive use? (currently falls back to runtime prompt)
2. **Audit trail reset policy** — confirm: append-only across all runs (recommended), not reset per run
3. **Integration test scope** — run all 3 sample requests or just `request-001.txt` to keep cost low?

---

## References

- `docs/specs/mvp-agent-tom.md` — authoritative for Pydantic schemas, HITL display format, pipeline call sequence, tech stack
- `docs/specs/Agent-Jack-SPEC.md` — authoritative for agent behavioural contracts, governance requirements, scope boundaries
- `docs/plans/tooling-agent-tom.md` — dependency versions, cost tracking pattern, testing strategy detail

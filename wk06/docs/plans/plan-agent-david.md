# Implementation Plan — FOI Multi-Agent CLI

**Author:** agent-david  
**Date:** 2026-06-24  
**Status:** Draft  
**Synthesises:** `docs/specs/Agent-Jack-SPEC.md`, `docs/specs/mvp-spec-agent-tom.md`, `docs/architecture/tooling-agent-tom.md`, `docs/plans/implementation-agent-tom.md`

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

- Triage uses Haiku, compliance and response use Sonnet
- Token costs per model stored as input/output rates per 1K tokens (verify against Anthropic pricing before committing)
- Chunk size 500 chars, overlap 100, retrieve top 5 chunks per query
- ChromaDB collection name and paths defined here so nothing is hardcoded elsewhere

---

## Build order

### Phase 1 — Foundation (no LLM calls)
1. `requirements.txt` + `.env.example` — pin all dependencies
2. `config.py` — all constants in one place; nothing hardcoded elsewhere
3. `models.py` — all data schemas upfront; agents exchange these, never raw dicts (see `implementation-agent-tom.md §5` for definitions)
4. `rag.py` — index policy docs into ChromaDB; retrieve top-k chunks by query
5. `cost_tracker.py` — wrap the LangChain usage callback; accumulate per-agent records

Gate: index runs cleanly against the two policy docs before moving on.

### Phase 2 — Agents
6. `agents/triage.py` — classify topic, complexity, summary; conservative fallback on failure (topic=unknown, complexity=high)
7. `agents/compliance.py` — takes triage output + retrieved chunks; identifies exemptions with citations; s40 flag triggers additional privacy instruction to downstream agents
8. `agents/response.py` — takes triage + compliance; drafts formal FOI letter grounded only in compliance findings

Each agent wraps its LLM call in retry logic and returns a structured fallback on error rather than raising.

### Phase 3 — Supervisor + HITL
9. `pipeline.py` — sequences the four steps (triage → retrieve → compliance → response → gate) over a shared case record; circuit breaker disables a failing agent after 3 consecutive errors; batch mode logs per-request status and running cost
10. `hitl.py` — displays evidence (retrieved chunks, classification, exemption reasoning, draft) before prompting; accept/reject/modify with operator identity captured; appends decision to append-only audit trail
11. `main.py` — `index` and `process` CLI entry points

### Phase 4 — Tests + polish
12. Unit tests — inject fake LLM responses to test each agent's parse logic and fallback paths without API calls
13. Integration test — run full pipeline on one sample request against real Haiku; assert topic and exemption sections present
14. `AI_LOG.md` — minimum 3 entries covering at least one doc/process task and two code tasks

---

## Key design decisions (from specs)

- **Supervisor is a plain function, not an LLM agent.** No dynamic routing.
- **HITL gate is never skipped.** If the terminal is interrupted the process exits rather than auto-approving.
- **Compliance fallback recommendation is withhold**, not release — fails safe.
- **s40 triggers an additional instruction** passed to the response agent — do not name or describe identifiable individuals.
- **Structured output uses tool-calling** under the hood for Anthropic models — field descriptions in schemas guide model output quality, so write them carefully.
- **Audit trail is append-only** across runs — never overwrite or reset it.
- **Rejected requests still write a result JSON** — rejection is a decision on record.

---

## Open questions before implementation

1. **Operator identity CLI flag** — add `--operator` flag to `main.py` as override for non-interactive use? (currently falls back to runtime prompt)
2. **Audit trail reset policy** — confirm: append-only across all runs (recommended), not reset per run
3. **Integration test scope** — run all 3 sample requests or just `request-001.txt` to keep cost low?

---

## References

- `docs/plans/implementation-agent-tom.md` — authoritative for Pydantic schemas, HITL display format, pipeline call sequence, requirements.txt, CostTracker, testing strategy
- `docs/specs/mvp-spec-agent-tom.md` — MVP requirements (what to build, not how)
- `docs/specs/Agent-Jack-SPEC.md` — authoritative for agent behavioural contracts, governance requirements, scope boundaries
- `docs/architecture/tooling-agent-tom.md` — technology choices and research findings (LangChain, embeddings, ChromaDB)

# RAID Log — Agent-Tom

**Project:** wk06 FOI Intelligent Automation System  
**Agent:** Agent-Tom  
**Last updated:** 2026-06-24  
**Status key:** Open · In progress · Resolved · Closed · Accepted

---

## Risks

| ID | Description | Likelihood | Impact | Status | Mitigation / notes |
|----|-------------|-----------|--------|--------|--------------------|
| R1 | **LLM citation hallucination** — Research (arXiv 2606.00898) documents 13–21% legal citation hallucination even with RAG. An incorrect exemption section number in a draft letter is legally indefensible. | Medium | High | Open | Stretch goal S-R1 (citation verification) mitigates. MVP mitigation: require compliance agent to include verbatim quotes from retrieved chunks alongside each exemption citation. Display chunk text at HITL gate for operator spot-check. |
| R2 | **Triage errors cascade** — A wrong topic classification sends the wrong RAG query → wrong compliance analysis → wrong draft. Errors amplified not corrected downstream (VIDIZMO finding). | Medium | High | Open | Triage fallback defaults to `complexity=high` (forces careful review). Stretch S-R2 adds triage override at HITL gate. Triage confidence score (open question OQ1) would surface low-confidence classifications for operator attention. |
| R3 | **s.40 personal data in draft responses** — Compliance identifies s.40 but without an explicit instruction, the response agent could paraphrase retrieved text containing identifiable individuals, constituting a DPA 2018 breach. | Medium | High | Resolved | MVP spec §4.2 requires: when `s40` identified, response agent receives explicit instruction not to name or describe identifiable individuals. Resolved in spec; must be enforced in implementation. |
| R4 | **Chunk parameters inadequate for legal text** — Default chunk_size=500, chunk_overlap=100 may not preserve enough context for qualified-exemption reasoning (s.43 public interest test spans multiple paragraphs). | Medium | Medium | Open | Open question OQ2. Requires empirical validation against policy corpus before implementation. |
| R5 | **LangChain sub-package incompatibilities** — Six sub-packages (`langchain-anthropic`, `langchain-chroma`, `langchain-huggingface`, `langchain-core`, `langchain-text-splitters`, `langchain-openai`) have complex interdependencies and frequent breaking changes. | Medium | High | Open | First implementation task must be `pip install -r requirements.txt` in a clean venv and confirming no conflicts. Pin exact versions immediately (`pip freeze`). |
| R6 | **Policy document staleness** — ChromaDB index built once at startup. Compliance agent may reason from outdated guidance without any visible signal. | Low (initially) | Medium | Open | Stretch S-R3 adds a staleness warning. MVP: acceptable risk for hackathon scope. |
| R7 | **HuggingFace model download blocked** — ~90 MB download required on first run. May be blocked by outbound proxy in some environments. | Low | Medium | Open | Fallback: `EMBEDDING_PROVIDER=openai` in `.env`. See `docs/architecture/tooling-agent-tom.md`. |
| R8 | **Operator rubber-stamping** — If the HITL gate becomes a click-through, AI errors are amplified at scale (Robodebt risk). | Low (hackathon) | High (production) | Accepted | By design: operator must actively choose A/R/M; no default approval. Documented in `production-spec-agent-tom.md §2.3`. Acceptable risk at hackathon scale. |

---

## Assumptions

| ID | Description | Status | If wrong |
|----|-------------|--------|----------|
| A1 | `with_structured_output()` uses **tool-calling** (not JSON mode) for Anthropic models. Pydantic field `description` strings are sent as tool parameter descriptions. | Confirmed (Context7 research, 2026-06-24) | Would change how we write field descriptions; unlikely to be wrong |
| A2 | `get_usage_metadata_callback` from `langchain_core.callbacks` is the correct built-in cost tracking mechanism; no custom `BaseCallbackHandler` subclass needed. | Confirmed (Context7 research, 2026-06-24) | Would require custom callback; unlikely to be wrong |
| A3 | `sentence-transformers/all-MiniLM-L6-v2` (~90 MB) is available for download from HuggingFace Hub and adequate for policy document similarity retrieval. | Assumed | Would need to select alternative embedding model |
| A4 | ChromaDB embedded mode (persistent on-disk, no separate server) is sufficient for hackathon scope and for the volume of policy documents provided. | Assumed | Would need a ChromaDB server setup; unlikely for hackathon scale |
| A5 | The policy documents provided in `starter/documents/policies/` (or equivalent) are representative enough for the compliance agent to make reasonable exemption assessments on the sample requests. | Assumed | Would need to augment the policy corpus before meaningful testing |
| A6 | Tenacity wraps agent functions for retry; `ChatAnthropic` native `max_retries` is **not used** to avoid potential double-retry conflicts. | **Resolved** (OQ5) | N/A — decision made to use tenacity only |
| A7 | `Chroma.from_documents()` and `Chroma.add_documents()` are the correct API methods for the current `langchain-chroma` version for creating a new collection and adding to an existing one respectively. | **Unconfirmed** — see OQ6 | Would cause runtime error in `rag.py` |
| A8 | A single human operator per run is the correct design scope. Multi-operator or concurrent processing is out of scope. | Assumed (brief-consistent) | Would require a different HITL architecture |
| A9 | Synthetic sample data (no real PII or real case data) is sufficient to demonstrate the system for the hackathon. | Assumed (brief-mandated) | — |

---

## Issues

| ID | Description | Priority | Status | Owner | Notes |
|----|-------------|----------|--------|-------|-------|
| I1 | **No consolidated spec exists yet** — `mvp-spec-agent-tom.md`, `Agent-Jack-SPEC.md`, `plan-agent-david.md` are all agent-suffixed drafts. Implementation cannot start (per `wk06/CLAUDE.md`) until at least one consolidated spec (no agent suffix) exists following the review process. | High | Open | Team | Requires review session between agents |
| I2 | **Triage confidence score design** — Schema and low-confidence routing. | High | **Resolved** | Agent-Tom | OQ1 resolved: `confidence: float` required; low-confidence triggers mandatory operator comment. Spec updated. |
| I3 | **Chunk size/overlap validation** — Parameters must be validated empirically before `rag.py` is implemented. | Medium | **Resolved → I7** | Agent-Tom | OQ2 resolved: empirical validation task created (I7) |
| I4 | **ChatAnthropic native max_retries** — Potential conflict with tenacity. | Medium | **Resolved** | Agent-Tom | OQ5 resolved: tenacity only; no native `max_retries` used. A6 updated. |
| I5 | **Chroma API pattern** — Correct methods for create vs add-to-existing. | Medium | **Resolved → I8** | Agent-Tom | OQ6 resolved: Context7 research task created (I8) before coding `rag.py` |
| I7 | **Chunk parameter validation experiment** — Before implementing `rag.py`, index policy docs with 2–3 size/overlap combinations and compare retrieval quality on sample compliance queries. | Medium | Open | Agent-Tom | Pre-implementation task. Unblocks config.py final values. |
| I8 | **ChromaDB/LangChain API research** — Use Context7 MCP to confirm `langchain-chroma` API for create vs add-to-existing collection before coding `rag.py`. | Medium | Open | Agent-Tom | Pre-implementation task. ~10 min. |
| I6 | **No `learning_materials/INDEX.md`** — `TOM_PREFERENCES.md` requires an index of learning materials. Three files exist in `learning_materials/` with no index. | Low | Open | Agent-Tom | Low priority vs implementation work |

---

## Dependencies

| ID | Description | Type | Status | Notes |
|----|-------------|------|--------|-------|
| D1 | **Anthropic API key** (`ANTHROPIC_API_KEY`) | External service | Required | Must be in `.env` before any LLM call. Never commit. |
| D2 | **HuggingFace model** (`sentence-transformers/all-MiniLM-L6-v2`, ~90 MB) | External download | Required (first run) | Cached to `~/.cache/huggingface/` after first download; subsequent runs offline |
| D3 | **Policy documents** (`.txt` files in `solution/documents/policies/`) | Internal data | Required | Can be copied from `starter/documents/` — read-only source |
| D4 | **Sample FOI requests** (`.txt` files in `solution/documents/foi_requests/`) | Internal data | Required | Can be copied from `starter/documents/` |
| D5 | **Context7 MCP** | Tool | Required pre-implementation | Must be used to confirm current API syntax for LangChain, ChromaDB before coding — per `wk06/CLAUDE.md` |
| D6 | **Agent-Jack plan doc** (`Agent-Jack-PLAN.md`) | Team dependency | Not yet created | Jack's SPEC notes it will be written separately. Needed before consolidation review can happen. |
| D7 | **Team spec consolidation review** | Process dependency | Blocked (I1) | Implementation cannot start until at least one consolidated spec exists. |
| D8 | **`OPERATOR_ID`** (env var or CLI flag) | Config | Required | Must be non-empty for every run; gate will prompt at runtime if absent. |

---

## Open Questions

These feed directly from `docs/specs/mvp-spec-agent-tom.md §10` and open assumptions above. Each needs a decision before the relevant part of the system can be implemented.

| ID | Question | Affects | Status | Decision |
|----|----------|---------|--------|----------|
| OQ1 | Should the triage agent output a confidence score? If yes, how should low-confidence results affect the pipeline? | `TriageResult` schema, HITL display | **Resolved** | Yes — include `confidence: float` (0–1). Low-confidence results (below configurable threshold) require the operator to enter a mandatory review comment before approving. Warning banner shown at HITL gate. Promoted to spec requirement — see `mvp-spec-agent-tom.md §3.1`. |
| OQ2 | What chunk size and overlap should be used? Are defaults (size=500, overlap=100) appropriate for dense legal text? | `config.py`, `rag.py` | **Resolved** | Validate empirically before coding `rag.py`. Index policy docs with 2–3 different size/overlap combinations, run sample compliance queries, pick the parameters that return the most complete exemption guidance. Added as issue I7. |
| OQ3 | Is RAG_TOP_K=5 sufficient for requests that engage multiple overlapping exemptions? | `config.py`, `rag.py` | **Resolved** | Start with k=5 (configurable in `config.py`). After chunk validation (OQ2), run a multi-exemption test case and adjust if coverage looks thin. Default of 5 is not a commitment. |
| OQ4 | How should the system handle requests that contain no clear FOI question (garbled text, non-FOI content)? | Triage fallback logic, `agents/triage.py` | **Resolved** | Triage classifies as topic `"unclear"` and sets `clarification_recommended=True` with a reason. Pipeline continues to HITL gate with a warning — consistent with FOIA s.16 duty to assist. No pre-triage validation step; no auto-rejection. |
| OQ5 | Does `ChatAnthropic` support a native `max_retries` parameter, or does tenacity always wrap it? Do they conflict? | `agents/*.py` retry logic | **Resolved** | Use tenacity only, wrapping the agent function. `@retry(wait=wait_exponential(...), stop=stop_after_attempt(5))` on each agent. No native `max_retries` used. Consistent retry behaviour across all agents. A6 assumption updated. |
| OQ6 | Is `Chroma.from_documents()` correct for creating a new collection, and `Chroma.add_documents()` for adding to an existing one? | `rag.py` | **Resolved** | Research via Context7 MCP before coding `rag.py`. This is a pre-implementation task (added as I8). Do not commit to an API pattern in plans without confirmation. |

# FOI Multi-Agent System — Implementation Plan

**Author:** AgentDoubleOSeven · **Date:** 2026-06-24 · **Companion to:** `AgentDoubleOSeven-SPEC.md`
**Provenance:** Built solely from the operator's planner JSON. No other agent's documents used.

## How to use this plan

- Work the phases in order. Each phase has **Tasks**, a **Verification** step (run it, observe the
  stated output — do not claim done without evidence), and a **Checkpoint**.
- **Every checkpoint follows the same order: Lint → Human review → Commit.**
- All commits are prefixed `[AgentDoubleOSeven]` and pushed immediately (rebase first).
- All code lives in `wk06/solution/`; `starter/` and `context/` are read-only sources to copy from.
- "Human review" = stop and show the operator the verification output before committing; proceed
  only on their OK.

**Conventions**
- Lint/type/test gate before every commit: `ruff check . && ruff format --check . && mypy . && pytest -q`.
- Tests live in `wk06/solution/tests/`. Each agent gets unit tests with a mocked `llm` seam so
  the suite runs without API calls; one opt-in live smoke test per agent behind an env flag.

---

## Phase 0 — Scaffolding, contracts & data
**Goal:** A runnable skeleton, the typed contracts frozen, and data to run against. (Unblocks parallel work.)
**ACs:** AC-0.1 project runs; AC-0.2 schemas import; AC-0.3 sample + dummy data present.

**Tasks**
1. Create `wk06/solution/` layout per SPEC §2.2; `requirements.txt` (anthropic, chromadb, typer, rich, pydantic, ruff, mypy, pytest); `.env.example` with `ANTHROPIC_API_KEY`.
2. Implement `schemas.py` (SPEC §3) in full.
3. Implement `config.py`: per-agent models (`triage=claude-haiku-4-5`, `compliance=claude-sonnet-4-6`, `response=claude-sonnet-4-6`, `redaction=claude-haiku-4-5`), fallback chains, price table, `k`, cost cap, paths.
4. Copy starter `documents/policies/*` and `documents/foi_requests/request-00{1,2,3}.txt` into `solution/documents/`. Add 3 dummy requests: a personal-data request (s40/redaction), a broad/expensive request (s12), a clean releasable request.
5. `main.py` Typer skeleton with `index` and `process` subcommands (stubs that print).

**Verification:** `python -m solution.main --help` lists both commands; `python -c "from solution import schemas"` succeeds; `ls solution/documents/foi_requests` shows 6 files.
**Checkpoint:** Lint → Human review (show the layout + schemas + data list) → Commit
`[AgentDoubleOSeven] Phase 0: scaffold, freeze data contracts, add sample+dummy FOI data`

---

## Phase 1 — RAG indexing & retrieval
**Goal:** Policy documents indexed into ChromaDB with section-aware chunks; retrieval returns relevant, citable excerpts.
**ACs:** AC-1.1 `index` reports a non-zero chunk count; AC-1.2 `search_policies("section 40 personal information")` returns the s40 chunk.

**Tasks**
1. `rag/indexer.py`: `chunk_text` splits on section headings (s12/s21/s36/s40/s41/s43 + PUBLIC INTEREST TEST / PARTIAL DISCLOSURE / RESPONSE TIMELINE; data-handling policy on its headings) so one exemption == one chunk.
2. `index_policies(dir)` → ChromaDB collection (default local embeddings); returns chunk count.
3. `search_policies(query, k)` → list of `{source, section, text, chunk_id}`.
4. Wire `main.py index`; call `index_policies` at the start of `process` (same process).
5. Unit test: chunk boundaries; retrieval relevance on 3 seed queries (s40, s43, s12).

**Verification:** `python -m solution.main index` prints a chunk count (expect ~10–20); a scratch retrieval for "personal information about third parties" returns the s40 chunk first.
**Checkpoint:** Lint → Human review (paste chunk count + top retrieval result) → Commit
`[AgentDoubleOSeven] Phase 1: section-aware ChromaDB indexing and retrieval`

---

## Phase 2 — LLM seam + Triage agent
**Goal:** The single `llm.call_structured()` seam (structured output + cost hook stub + retry), and a working triage agent.
**ACs:** AC-2.1 triage returns a valid `TriageResult` for a sample request; AC-2.2 invalid model output never crashes the caller.

**Tasks**
1. `llm.py`: `call_structured(agent, model, schema, system, user)` using native structured outputs; returns a validated Pydantic object; SDK retry on; cost-logging + model-fallback hooks present (stubbed to be filled in Phases 5–6).
2. `agents/triage.py`: prompt + taxonomy (SPEC §4.1) → `TriageResult`.
3. Unit tests with a **mocked** `llm` (no API); one opt-in live smoke test.

**Verification:** live smoke `process` on `request-001.txt` prints a plausible `TriageResult` (topic=spending, complexity≈medium); mocked tests pass.
**Checkpoint:** Lint → Human review → Commit
`[AgentDoubleOSeven] Phase 2: llm structured-output seam and triage agent`

---

## Phase 3 — Compliance agent (RAG-backed, rule-assisted)
**Goal:** Retrieve policy, identify exemptions with absolute/qualified split, run the public-interest test where required, recommend an outcome, cite chunks.
**ACs:** AC-3.1 compliance cites at least one retrieved chunk; AC-3.2 a qualified exemption (s36/s43) populates `public_interest_test`; AC-3.3 an absolute exemption (s40/s41) does not.

**Tasks**
1. `agents/compliance.py`: build prompt from retrieved chunks + request + triage; enforce the absolute/qualified taxonomy and the PIT-for-qualified rule (SPEC §4.2) → `ComplianceResult`.
2. Ensure `policy_ref` on each finding maps to a real `chunk_id`.
3. Unit tests (mocked retrieval + mocked llm) covering: a procurement request (s43 qualified → PIT present), a personal-data request (s40 absolute → no PIT), a clean request (release).

**Verification:** live smoke on the procurement request yields `recommendation` ∈ {partial_release, withhold}, an s43 finding with a populated PIT, and `policy_sources` citing the s43 chunk.
**Checkpoint:** Lint → Human review (show one full `ComplianceResult`) → Commit
`[AgentDoubleOSeven] Phase 3: RAG-backed rule-assisted compliance agent`

---

## Phase 4 — Response drafting agent
**Goal:** Draft a formal FOI reply grounded in triage + compliance, with a decision-centred evidence summary.
**ACs:** AC-4.1 the draft references the classification and the compliance recommendation; AC-4.2 a `withhold`/`partial_release` draft states the exemption + public-interest reasoning.

**Tasks**
1. `agents/response.py`: prompt consuming `TriageResult` + `ComplianceResult` → `DraftResult`; support a `modify` regeneration path that accepts operator instructions.
2. Unit tests (mocked) for release / partial / withhold drafts.

**Verification:** live smoke produces a release draft and a withhold draft; the withhold draft names the exemption and the public-interest reasoning.
**Checkpoint:** Lint → Human review → Commit
`[AgentDoubleOSeven] Phase 4: response drafting agent with regeneration path`

---

## Phase 5 — Supervisor, structured wiring & layered error handling
**Goal:** End-to-end pipeline through the supervisor with the full five-layer error/fallback defence; one bad request never kills the batch.
**ACs:** AC-5.1 `process` runs triage→compliance→response for each request; AC-5.2 a forced API error / unparseable result logs and continues with a fallback; AC-5.3 model fallback fires on a forced model error.

**Tasks**
1. `supervisor.py`: sequence agents, per-stage try/except, assemble partial results on failure.
2. Complete `llm.py` model-fallback chain + cost-cap downgrade (SPEC §8 layers 3–4).
3. Per-agent typed fallbacks (SPEC §8 layer 2).
4. Fault-injection tests: raise inside each agent and assert the batch completes with the documented fallback.

**Verification:** run `process` over the 6-file folder with a fault injected into compliance on one file; the run completes, that file shows the `withhold`+flagged fallback, others are unaffected.
**Checkpoint:** Lint → Human review (show fault-injection run output) → Commit
`[AgentDoubleOSeven] Phase 5: supervisor orchestration and layered fallbacks`

---

## Phase 6 — Cost tracking
**Goal:** Per-call cost logged, rolled up per-agent and per-request, end-of-run summary.
**ACs:** AC-6.1 every LLM call logs model + prompt/completion tokens + est cost; AC-6.2 end-of-run summary shows per-agent and per-request breakdown; AC-6.3 per-request total appears in the result JSON.

**Tasks**
1. `cost.py`: `CostTracker` with the price table; `log_call`, per-agent + per-request rollup, `print_summary` (Rich table).
2. Connect the cost hook in `llm.call_structured`.
3. Test cost maths against a known token count.

**Verification:** a full `process` prints a Rich summary with non-zero per-agent and per-request costs; a result JSON contains a `cost` block.
**Checkpoint:** Lint → Human review → Commit
`[AgentDoubleOSeven] Phase 6: per-call/per-agent/per-request cost tracking + summary`

---

## Phase 7 — HITL gate (decision centre-stage)
**Goal:** A blocking approve/reject/modify gate that presents the **decision** first, accepts a decision, and records it. Cost is not shown here.
**ACs:** AC-7.1 the gate pauses and displays recommendation + evidence (classification, chunks, reasoning, draft); AC-7.2 approve/reject/modify all work, modify edits or regenerates; AC-7.3 a `Decision` with operator id + timestamp + evidence refs is recorded; AC-7.4 cost is **not** displayed at the gate.

**Tasks**
1. `hitl.py`: `human_checkpoint(...)` Rich panel — recommendation front-and-centre, then classification, exemption reasoning + PIT, retrieved chunks, the redacted draft; mandatory-review banner when flagged.
2. Implement approve / reject (reason) / modify (inline edit **or** regenerate via the response agent).
3. Wire into the supervisor; block on input; return a `Decision`.

**Verification:** run `process` on one request; confirm it pauses, the recommendation is the headline, each action path works, and no cost is shown at the gate.
**Checkpoint:** Lint → Human review (operator drives one approve, one reject, one modify) → Commit
`[AgentDoubleOSeven] Phase 7: decision-centred HITL approve/reject/modify gate`

---

## Phase 8 — Persistence: result JSON + audit .txt
**Goal:** Each request writes a structured JSON result; the run appends to a human-readable `.txt` audit log.
**ACs:** AC-8.1 a `<stem>-result.json` per request with classification, exemptions, draft, decision, cost; AC-8.2 `audit.txt` records every agent decision, human override, and cost entry, timestamped, with operator identity.

**Tasks**
1. `audit.py`: append-only `.txt` writer (SPEC §9 line format).
2. Supervisor writes the result JSON (SPEC §9 shape) and audit lines at each stage + the human decision.
3. Test artefact contents against the schema.

**Verification:** after a run, open one result JSON (valid against schemas) and `audit.txt` (one line per stage + a HUMAN line with operator + evidence refs).
**Checkpoint:** Lint → Human review (open both artefacts) → Commit
`[AgentDoubleOSeven] Phase 8: result JSON + append-only .txt audit log`

---

## Phase 9 — Redaction agent (hybrid)
**Goal:** Mask personal data in the draft before the human gate; fail safe and flag on uncertainty.
**ACs:** AC-9.1 emails/phones/postcodes masked deterministically; AC-9.2 names/contextual PII masked by the LLM pass; AC-9.3 a failed redaction pass passes through flagged for mandatory review.

**Tasks**
1. `agents/redaction.py`: regex pass (email, phone, UK postcode) + Haiku pass for names/context → `RedactionResult`.
2. Insert before the HITL gate in the supervisor; surface `needs_mandatory_review` to the gate banner.
3. Tests: a known-PII draft is masked; a forced LLM failure yields a flagged pass-through.

**Verification:** the personal-data dummy request shows masked emails/names in the gated draft; a forced failure raises the mandatory-review banner.
**Checkpoint:** Lint → Human review → Commit
`[AgentDoubleOSeven] Phase 9: hybrid regex+LLM redaction before review`

---

## Phase 10 — Batch processing + progress display
**Goal:** Process a folder sequentially with a live progress display (status, cumulative cost, ETA).
**ACs:** AC-10.1 all sample+dummy requests process without crashing; AC-10.2 the display shows per-request status, cumulative cost, and ETA.

**Tasks**
1. Rich live progress around the sequential loop (one request at a time, interactive gate per request).
2. Per-request status transitions (triage→…→awaiting-review→done/rejected).

**Verification:** `process documents/foi_requests/` runs the whole folder end-to-end with the live display and a final cost summary; all 6 artefacts written.
**Checkpoint:** Lint → Human review (full-folder run) → Commit
`[AgentDoubleOSeven] Phase 10: sequential batch processing with live progress`

---

## Phase 11 — Polish, AI_LOG, demo dry-run
**Goal:** Tidy, document, and rehearse the demo.
**ACs:** AC-11.1 README run instructions verified from clean; AC-11.2 AI_LOG has ≥3 meaningful entries; AC-11.3 a clean end-to-end demo on a **held-out** request the build was not tuned against.

**Tasks**
1. `solution/README.md` setup + run steps; verify from a clean venv.
2. Ensure `AI_LOG.md` has ≥3 entries covering meaningful iterations.
3. Demo dry-run on a fresh request not used during development; note any rough edges.

**Verification:** a teammate follows the README from scratch and reaches a working run; the held-out request processes end-to-end.
**Checkpoint:** Lint → Human review (demo dry-run) → Commit
`[AgentDoubleOSeven] Phase 11: docs, AI_LOG, demo dry-run`

---

## Acceptance criteria summary

| Phase | ACs | Verified by |
|-------|-----|-------------|
| 0 | AC-0.1–0.3 | help output, schema import, data listing |
| 1 | AC-1.1–1.2 | index count, seed retrieval |
| 2 | AC-2.1–2.2 | triage smoke + mocked tests |
| 3 | AC-3.1–3.3 | compliance smoke (PIT present/absent, citation) |
| 4 | AC-4.1–4.2 | draft references findings |
| 5 | AC-5.1–5.3 | end-to-end + fault injection |
| 6 | AC-6.1–6.3 | cost summary + result JSON cost block |
| 7 | AC-7.1–7.4 | operator drives all three gate actions |
| 8 | AC-8.1–8.2 | result JSON + audit.txt contents |
| 9 | AC-9.1–9.3 | masking + flagged failure |
| 10 | AC-10.1–10.2 | full-folder run + live display |
| 11 | AC-11.1–11.3 | clean README run + held-out demo |

## Suggested order for a 2-day, parallel team

- **Day 1 (to MVS):** Phase 0 (whole team, then split), then in parallel — Phase 1 (RAG owner),
  Phase 2 (triage owner). Converge on Phase 3, then Phase 4 and Phase 5. Target: triage +
  RAG-backed compliance + drafting wired through the supervisor by the Day-1 checkpoint.
- **Day 2 (deepen + polish):** Phase 6 (cost) and Phase 7 (HITL) in parallel, then Phase 8
  (persistence), Phase 9 (redaction), Phase 10 (batch), Phase 11 (polish + demo). Clean module
  boundaries from Phase 0 let these proceed with minimal collision.

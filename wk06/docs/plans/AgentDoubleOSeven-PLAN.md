# FOI Multi-Agent System — Implementation Plan

**Author:** AgentDoubleOSeven · **Date:** 2026-06-24 · **Companion to:** `AgentDoubleOSeven-SPEC.md`
**Provenance:** Built solely from the operator's planner JSON. No other agent's documents used.

## How to use this plan

- This plan **realises the specification**. The spec (`AgentDoubleOSeven-SPEC.md`) owns the
  acceptance criteria (`AC-A1`…`AC-K1`, spec §6) and the test specification (`T-*`, spec §7); this
  plan owns the *implementation* (file layout, model IDs, schemas, retrieval depth, chunking, prompt
  approach, artefact formats). Each phase below names the **spec ACs it satisfies** and the **spec
  tests it implements**.
- Work the phases in order. Each phase has **Tasks**, a **Unit tests** stage, a **Verification**
  stage (run it; observe the stated output — never claim done without evidence), and a
  **Checkpoint**.
- **Every checkpoint follows the same order: Lint & type-check → Unit tests pass → Human review →
  Commit.** No commit happens until lint/type-check and that phase's unit tests are green and the
  operator has signed off on the verification evidence.
- "Human review" = stop, show the operator the verification output (and for gate/redaction phases,
  let them drive it), and proceed only on their OK.
- All commits are prefixed `[AgentDoubleOSeven]` and pushed immediately (rebase first).
- All code lives in `wk06/solution/`; `starter/` and `context/` are read-only sources to copy from.

**Standing conventions**
- Pre-commit gate (run every phase): `ruff check . && ruff format --check . && mypy . && pytest -q`.
- Tests live in `wk06/solution/tests/`. Unit tests use a **mocked LLM seam** so the suite runs
  offline with no API calls; each agent phase adds one **opt-in live smoke test** behind an env
  flag. The spec's `T-*` scenarios are realised as these unit/integration tests.
- Coverage rule (spec §7.8 definition of done): a phase is not done until every spec AC it claims
  has at least one passing test, and the reliability tests pass with faults injected at **every**
  stage.

---

## Phase 0 — Scaffolding, contracts & data
**Goal:** A runnable skeleton, the typed contracts frozen, and data to run against. (Unblocks parallel work.)
**Satisfies (spec ACs):** foundation for AC-A2 (deterministic ordering) and AC-I1 (result contract); establishes the test-data strategy for AC-K1 (spec §7.1).

**Tasks**
1. Create `wk06/solution/` layout (`main.py`, `config.py`, `schemas.py`, `llm.py`, `supervisor.py`, `agents/`, `rag/`, `cost.py`, `audit.py`, `hitl.py`, `documents/`, `output/`, `tests/`); `requirements.txt` (anthropic, chromadb, typer, rich, pydantic, ruff, mypy, pytest); `.env.example` with `ANTHROPIC_API_KEY`.
2. Implement the typed data contracts in `schemas.py`: `TriageResult` (topic, complexity, drivers, summary), `ExemptionFinding` (section, kind=absolute|qualified, applies, reasoning, policy_ref), `ComplianceResult` (exemptions, recommendation, public_interest_test|None, policy_sources, confidence), `DraftResult`, `RedactionResult` (incl. `needs_mandatory_review`), `Decision` (decision, operator, timestamp, notes, evidence_refs, final_response), `CostEntry`.
3. `config.py`: per-agent models (`triage=claude-haiku-4-5`, `compliance=claude-sonnet-4-6`, `response=claude-sonnet-4-6`, `redaction=claude-haiku-4-5`), fallback chains, price table, retrieval `k`, cost cap, paths.
4. Copy starter `documents/policies/*` and `documents/foi_requests/request-00{1,2,3}.txt`. Add 3 crafted requests (spec §7.1): a personal-data request (absolute/s40 → redaction), a broad/expensive request (s12), a clean releasable request. Reserve a separate **held-out** set, not used during development (for T-K1).
5. `main.py` Typer skeleton with `index` and `process` subcommands (stubs that print).

**Unit tests:** schema round-trip/validation tests (each contract accepts a valid object and rejects a malformed one).
**Verification:** `python -m solution.main --help` lists both commands; `python -c "from solution import schemas"` succeeds; `ls solution/documents/foi_requests` shows the sample + crafted set.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (show layout, contracts, data list) → Commit
`[AgentDoubleOSeven] Phase 0: scaffold, freeze data contracts, add sample+crafted FOI data`

---

## Phase 1 — RAG indexing & retrieval
**Goal:** Policy indexed into ChromaDB with section-aware chunks; retrieval returns relevant, citable excerpts.
**Satisfies (spec ACs):** AC-C1 (retrieval + per-exemption citation grounding).
**Implements (spec tests):** retrieval foundation for T-C1–T-C3; citation availability for T-C4.

**Tasks**
1. `rag/indexer.py`: `chunk_text` splits on section headings (s12/s21/s36/s40/s41/s43 + PUBLIC INTEREST TEST / PARTIAL DISCLOSURE / RESPONSE TIMELINE; data-handling policy on its headings) so one exemption == one citable chunk.
2. `index_policies(dir)` → ChromaDB collection (default local embeddings); returns chunk count.
3. `search_policies(query, k)` → `[{source, section, text, chunk_id}]`.
4. Wire `main.py index`; call `index_policies` at the start of `process` (same process, avoiding the in-memory-loss pitfall).

**Unit tests:** chunk-boundary test (each exemption is its own chunk); retrieval-relevance test on seed queries for s40, s43, s12 (the expected section ranks first).
**Verification:** `python -m solution.main index` prints a chunk count (~10–20); a scratch retrieval for "personal information about third parties" returns the s40 chunk first.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (paste chunk count + top retrieval result) → Commit
`[AgentDoubleOSeven] Phase 1: section-aware ChromaDB indexing and retrieval`

---

## Phase 2 — LLM seam + Triage agent
**Goal:** The single `llm.call_structured()` seam (validated structured output + retry + cost/fallback hooks) and a working triage agent.
**Satisfies (spec ACs):** AC-B1, AC-B2 (valid closed-set classification with drivers); AC-G1 (malformed output handled at the seam).
**Implements (spec tests):** T-B1 (typical request classifies), T-B2 (garbled request still yields a valid classification, errs high, no crash).

**Tasks**
1. `llm.py`: `call_structured(agent, model, schema, system, user)` using native structured outputs; returns a validated Pydantic object; SDK retry on; cost-logging + model-fallback hooks present (completed in Phases 5–6).
2. `agents/triage.py`: prompt + the closed taxonomy (topics: spending/procurement/staffing/policy/personal_data/correspondence/other; complexity low/medium/high + drivers) → `TriageResult`.

**Unit tests:** T-B1 and T-B2 with a **mocked** LLM (no API); one opt-in live smoke test.
**Verification:** live smoke `process` on `request-001.txt` prints a plausible `TriageResult`; mocked T-B1/T-B2 pass.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review → Commit
`[AgentDoubleOSeven] Phase 2: llm structured-output seam and triage agent`

---

## Phase 3 — Compliance agent (RAG-backed, rule-assisted)
**Goal:** Retrieve policy, identify exemptions with the absolute/qualified split, run the public-interest test where required, recommend an outcome, cite chunks.
**Satisfies (spec ACs):** AC-C1 (citation), AC-C2 (qualified→PIT, absolute→none), AC-C3 (valid, consistent recommendation), AC-C4 (no exemption ⇒ release).
**Implements (spec tests):** T-C1 (qualified → PIT present), T-C2 (absolute → no PIT), T-C3 (releasable → release), T-C4 (every asserted exemption cited).

**Tasks**
1. `agents/compliance.py`: build the prompt from retrieved chunks + request + triage; enforce the absolute/qualified taxonomy and the PIT-for-qualified rule → `ComplianceResult`.
2. Ensure each finding's `policy_ref` maps to a real retrieved `chunk_id`.

**Unit tests:** T-C1–T-C4 with mocked retrieval + mocked LLM — a procurement request (s43 qualified → PIT present), a personal-data request (s40 absolute → no PIT), a clean request (release), and a citation-presence assertion across all findings.
**Verification:** live smoke on the procurement request yields `recommendation ∈ {partial_release, withhold}`, an s43 finding with a populated PIT, and `policy_sources` citing the s43 chunk.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (show one full `ComplianceResult`) → Commit
`[AgentDoubleOSeven] Phase 3: RAG-backed rule-assisted compliance agent`

---

## Phase 4 — Response drafting agent
**Goal:** Draft a formal FOI reply grounded in triage + compliance, with a decision-centred evidence summary.
**Satisfies (spec ACs):** AC-D1 (reflects recommendation + references findings), AC-D2 (withhold/partial states exemption + PIT reasoning).
**Implements (spec tests):** T-D1.

**Tasks**
1. `agents/response.py`: prompt consuming `TriageResult` + `ComplianceResult` → `DraftResult`; support a `modify` regeneration path that accepts operator instructions (used by the gate in Phase 7).

**Unit tests:** T-D1 (mocked) across release / partial / withhold — assert the draft references the classification and recommendation, and that withhold/partial drafts name the exemption(s) and PIT reasoning.
**Verification:** live smoke produces a release draft and a withhold draft; the withhold draft names the exemption and the public-interest reasoning.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review → Commit
`[AgentDoubleOSeven] Phase 4: response drafting agent with regeneration path`

---

## Phase 5 — Supervisor, structured wiring & layered error handling
**Goal:** End-to-end pipeline through the supervisor with the full five-layer fail-safe defence; one bad request never kills the batch.
**Satisfies (spec ACs):** AC-A1 (batch never aborts), AC-A2 (deterministic order), AC-G1 (errors logged + handled), AC-G2 (fallbacks fail safe), AC-G3 (failure isolation).
**Implements (spec tests):** T-A1 (folder incl. a failing request completes), T-G1 (API error injected per stage), T-G2 (malformed/empty output handled), T-G3 (one persistent failure doesn't affect others), T-G4 (fallback fails safe).

**Tasks**
1. `supervisor.py`: sequence triage→compliance→response, per-stage try/except, assemble partial results on failure.
2. Complete `llm.py` model-fallback chain + cost-cap downgrade.
3. Per-agent typed fail-safe fallbacks (triage→complexity=high/route-to-human; compliance→withhold/low-confidence/flagged; response→placeholder "manual response required"; redaction handled in Phase 9).
   The five layers: SDK retry · per-agent typed fallback · model fallback · cost-threshold downgrade · per-stage try/except.

**Unit tests:** T-G1–T-G4 via fault injection (raise/return-malformed inside each agent) — assert continuation, safe fallback bias, and batch isolation; T-A1 as an integration test over a mixed folder.
**Verification:** run `process` over the folder with a fault injected into compliance on one file; the run completes, that file shows the withhold+flagged fallback, others are unaffected.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (show fault-injection run output) → Commit
`[AgentDoubleOSeven] Phase 5: supervisor orchestration and layered fail-safe fallbacks`

---

## Phase 6 — Cost tracking
**Goal:** Per-call cost logged, rolled up per-agent and per-request, with an end-of-run summary.
**Satisfies (spec ACs):** AC-H1 (per-call model + tokens + est cost), AC-H2 (per-agent + per-request rollups + summary).
**Implements (spec tests):** T-H1 (run yields rollups + summary), T-H2 (cost maths matches tokens × rates).

**Tasks**
1. `cost.py`: `CostTracker` with the price table; `log_call`, per-agent + per-request rollup, `print_summary` (Rich table).
2. Connect the cost hook in `llm.call_structured`; embed the per-request total into the result artefact.

**Unit tests:** T-H2 (cost maths against a known token count); a rollup test asserting per-agent and per-request aggregation.
**Verification:** a full `process` prints a Rich summary with non-zero per-agent and per-request costs; a result artefact contains a `cost` block.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review → Commit
`[AgentDoubleOSeven] Phase 6: per-call/per-agent/per-request cost tracking + summary`

---

## Phase 7 — HITL gate (decision centre-stage)
**Goal:** A blocking approve/reject/modify gate that presents the **decision** first, accepts a decision, and records it. Cost is not shown here.
**Satisfies (spec ACs):** AC-F1 (single pause, no auto-approve), AC-F2 (decision headline + supporting evidence), AC-F3 (approve/reject/modify take effect), AC-F4 (decision recorded with operator id, timestamp, evidence refs, notes), AC-F5 (no cost at the gate).
**Implements (spec tests):** T-F1 (pause + headline + no auto-approve), T-F2 (approve), T-F3 (reject with reason), T-F4 (modify: edit and regenerate), T-F5 (no cost at gate).

**Tasks**
1. `hitl.py`: `human_checkpoint(...)` Rich panel — recommendation front-and-centre, then classification, exemption reasoning + PIT, cited chunks, the redacted draft; mandatory-review banner when flagged.
2. Implement approve / reject (reason) / modify (inline edit **or** regenerate via the response agent).
3. Wire into the supervisor; block on input; return a `Decision`.

**Unit tests:** T-F1–T-F5 driving the gate with scripted operator inputs against a mocked I/O layer — assert pause, each action's effect on the finalised response, the decision record's fields, and the absence of cost at the gate.
**Verification:** run `process` on one request; confirm it pauses, the recommendation is the headline, each action path works, and no cost is shown at the gate.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (operator drives one approve, one reject, one modify) → Commit
`[AgentDoubleOSeven] Phase 7: decision-centred HITL approve/reject/modify gate`

---

## Phase 8 — Persistence: result artefact + human-readable audit trail
**Goal:** Each request writes a structured machine-readable result; the run appends to a human-readable `.txt` audit trail.
**Satisfies (spec ACs):** AC-I1 (structured result: classification, exemptions, draft, decision, cost), AC-I2 (append-only human-readable audit of every agent decision, override, cost entry, timestamped, with operator identity); completes AC-F5 (cost lives in the audit, not the gate).
**Implements (spec tests):** T-I1 (result artefact content), T-I2 (audit trail content), and the audit half of T-F5.

**Tasks**
1. `audit.py`: append-only `.txt` writer — one timestamped, human-readable line per event (agent decisions, human overrides, cost entries).
2. Supervisor writes the per-request result (JSON) and audit lines at each stage + the human decision.

**Unit tests:** T-I1 (result validates against the contracts and contains all required sections), T-I2 (audit trail contains a line per stage + a HUMAN line with operator + evidence refs + a cost entry).
**Verification:** after a run, open one result artefact (valid) and the audit `.txt` (per-stage lines + HUMAN line with operator + evidence refs + cost).
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (open both artefacts) → Commit
`[AgentDoubleOSeven] Phase 8: structured result artefact + human-readable .txt audit trail`

---

## Phase 9 — Redaction agent (hybrid)
**Goal:** Mask personal data in the draft before the human gate; fail safe and flag on uncertainty.
**Satisfies (spec ACs):** AC-E1 (identifiers + names masked before review), AC-E2 (uncertain redaction → flagged for mandatory review, never silently unredacted); reinforces AC-G2 (fail-safe).
**Implements (spec tests):** T-E1 (known PII masked), T-E2 (redaction failure → flagged pass-through).

**Tasks**
1. `agents/redaction.py`: deterministic pass (email, phone, UK postcode) + model pass (Haiku) for names/contextual PII → `RedactionResult`.
2. Insert before the HITL gate in the supervisor; surface `needs_mandatory_review` to the gate banner.

**Unit tests:** T-E1 (a known-PII draft is masked — deterministic identifiers + model-detected names), T-E2 (a forced model-pass failure yields a flagged, unredacted pass-through).
**Verification:** the personal-data crafted request shows masked emails/names in the gated draft; a forced failure raises the mandatory-review banner.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review → Commit
`[AgentDoubleOSeven] Phase 9: hybrid deterministic+model redaction before review`

---

## Phase 10 — Batch processing + progress display
**Goal:** Process a folder sequentially with a live progress display (status, cumulative cost, progress).
**Satisfies (spec ACs):** AC-J1 (CLI indexes + processes a folder), AC-J2 (sequential batch with per-request status, cumulative cost, progress); exercises AC-A1 at folder scale.
**Implements (spec tests):** T-J1 (CLI index + process with live display), and the full-folder form of T-A1.

**Tasks**
1. Rich live progress around the sequential loop (one request at a time, interactive gate per request).
2. Per-request status transitions (triage→…→awaiting-review→done/rejected).

**Unit tests:** T-J1 progress-state test (status transitions + cumulative cost update) with a mocked pipeline; a full-folder integration run of T-A1.
**Verification:** `process documents/foi_requests/` runs the whole folder end-to-end with the live display and a final cost summary; all artefacts written.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (full-folder run) → Commit
`[AgentDoubleOSeven] Phase 10: sequential batch processing with live progress`

---

## Phase 11 — Generalisation, polish, AI_LOG & demo
**Goal:** Prove generalisation on held-out inputs, tidy, document, and rehearse the demo. Confirm the spec §7.8 definition of done.
**Satisfies (spec ACs):** AC-K1 (correct on held-out requests); final pass over all ACs.
**Implements (spec tests):** T-K1 (held-out requests flow end-to-end and satisfy the relevant functional/governance/persistence ACs).

**Tasks**
1. `solution/README.md` setup + run steps; verify from a clean venv.
2. Ensure `AI_LOG.md` has ≥3 meaningful entries.
3. Run T-K1 on the reserved held-out set (not used during development); note any rough edges.
4. Confirm the definition of done (spec §7.8): every claimed AC has a passing test; reliability tests pass with faults injected at every stage.

**Unit tests:** T-K1 as an integration run over the held-out set; a coverage check that every spec AC maps to ≥1 passing test.
**Verification:** a teammate follows the README from scratch and reaches a working run; the held-out set processes end-to-end and passes its ACs.
**Checkpoint:** Lint & type-check → Unit tests pass → Human review (held-out demo dry-run) → Commit
`[AgentDoubleOSeven] Phase 11: held-out generalisation, docs, AI_LOG, demo`

---

## Phase → spec acceptance-criteria & test map

| Phase | Spec ACs satisfied | Spec tests implemented |
|-------|--------------------|------------------------|
| 0 | (foundation) A2, I1; data for K1 | schema validation |
| 1 | C1 | T-C4 (citation), retrieval foundation for T-C1–C3 |
| 2 | B1, B2, G1 | T-B1, T-B2 |
| 3 | C1, C2, C3, C4 | T-C1, T-C2, T-C3, T-C4 |
| 4 | D1, D2 | T-D1 |
| 5 | A1, A2, G1, G2, G3 | T-A1, T-G1, T-G2, T-G3, T-G4 |
| 6 | H1, H2 | T-H1, T-H2 |
| 7 | F1, F2, F3, F4, F5 | T-F1, T-F2, T-F3, T-F4, T-F5 |
| 8 | I1, I2, F5 | T-I1, T-I2, T-F5 |
| 9 | E1, E2, G2 | T-E1, T-E2 |
| 10 | J1, J2, A1 | T-J1, T-A1 (full folder) |
| 11 | K1 (+ all-AC final pass) | T-K1, AC→test coverage check |

Every spec AC (A1–A2, B1–B2, C1–C4, D1–D2, E1–E2, F1–F5, G1–G3, H1–H2, I1–I2, J1–J2, K1) and every
spec test (T-A1, T-B1–B2, T-C1–C4, T-D1, T-E1–E2, T-F1–F5, T-G1–G4, T-H1–H2, T-I1–I2, T-J1, T-K1) is
covered above.

## Suggested order for a 2-day, parallel team

- **Day 1 (to MVS):** Phase 0 (whole team, then split), then in parallel — Phase 1 (RAG owner),
  Phase 2 (triage owner). Converge on Phase 3, then Phase 4 and Phase 5. Target: triage +
  RAG-backed compliance + drafting wired through the supervisor, with each phase's unit tests green,
  by the Day-1 checkpoint.
- **Day 2 (deepen + polish):** Phase 6 (cost) and Phase 7 (HITL) in parallel, then Phase 8
  (persistence), Phase 9 (redaction), Phase 10 (batch), Phase 11 (generalisation + polish). Clean
  module boundaries from Phase 0 let these proceed with minimal collision.

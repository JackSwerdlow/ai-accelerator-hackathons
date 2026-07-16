# Remaining eval/test/observability work — handoff (Agent-Tom)

Written 2026-07-16 to hand off outstanding work so this session can focus on the
Day 2 presentation slide. Whoever picks this up: read
`wk09/plans/eval-test-plan-agent-tom.md` and `wk09/solution/EVAL_REPORT.md` first
for full context — this doc only lists what's *left*, not the whole history.

**Working directory:** this was authored from the worktree at
`.claude/worktrees/wk09-eval-test-plan/wk09/` — check whether that worktree still
exists or whether the work has since landed on `main` before starting; either way,
run `git status` / `git log` first, this repo is under heavy concurrent development
(multiple agents pushing directly to `main` throughout this project).

**Running the suite:** `cd wk09/solution && python3 -m pytest test_analyse.py tests/ -q`
— note the explicit file list. Bare `pytest` from `solution/` also picks up
`test_telemetry.py`/`test_telemetry_integration.py` at the repo root, which are a
different, unrelated test count (87 vs the 65 documented here) — don't conflate them
when reporting numbers.

## 1. Commit and push the S5/MON2/GOV3/GOV6 fixes (uncommitted as of writing!)

`analyse.py`, `test_analyse.py`, and `tests/unit/test_provenance.py` currently have
**uncommitted** changes on disk implementing:
- S5: unique per-PID temp filename in `_save_state`, plus a second fix in
  `_clear_state` (idempotent unlink, no exists()-then-unlink() TOCTOU gap)
- MON2: `--max-spend-gbp` / `MAX_SPEND_GBP` env var cost guardrail
- GOV3/GOV6 (merged into one fix): `model` + `raw_response` recorded per row via
  `_merge_row`; GOV3's original "pin to a dated snapshot" framing was corrected
  after a real `client.models.list()` call showed no dated snapshot exists for
  current-gen models — see the comment above `DEFAULT_MODEL` in `analyse.py`.

Before committing: re-run the full suite (`test_analyse.py tests/`, expect
**64 passed, 1 skipped, 0 failed**), run flake8, then follow the repo's git workflow
(pull --rebase, commit with `[Agent-Tom]` prefix, pull --rebase again, push) — expect
to need to rebase given how active this repo is.

## 2. Update checklist checkboxes/evidence

`wk09/solution/improvement-checklist-agent-tom.md` still has **0 of 57** items
checked `[x]`, even though many are now fixed. Mark and fill in `Evidence:` lines for:
- Already fixed by Agent-Jack's rewrite: C1, C2, C3, R1, R2, R4, S1, S9, V1, E1, E2
- Already satisfied independent of the rewrite: O1, O2, S2, S3, PII1
- Fixed by Agent-Tom (this handoff's item 1, once committed): S5, MON2, GOV3, GOV6

Also **re-tally the priority-order table** at the top of the file — a recent check
found the summary table's P0/P1/P2/P3/F counts (16/15/21/1/2) don't quite match a
fresh `grep` of the actual items (15/15/23/1/2, summing to 56 not 57 — one item may
be untagged). Worth a careful pass rather than trusting the existing table.

## 3. Add `test_analyse.py` to the CI workflow

`.github/workflows/tests.yml` currently only runs `tests/` — it's missing
Agent-Jack's 40-test `test_analyse.py` suite entirely. Add it to the pytest
invocation in the workflow.

## 4. Regenerate `EVAL_REPORT.md` and cross-check `project_cost.py`'s numbers

Both the checklist's priority counts (item 2) and `EVAL_REPORT.md`'s cost-projection
table are stale relative to a live run — `evals/scale/project_cost.py`'s *absolute*
£ figures have drifted since the report was written (pricing.py's constants moved),
though the *relative* ~34% saving from caching held up in a spot-check. Regenerate
`EVAL_REPORT.md` from a fresh full test run + a fresh `project_cost.py` run rather
than hand-editing the old numbers.

## 5. Extend `project_cost.py` with a batch-pricing curve

Currently only models baseline-vs-caching at 1,000/20,000 rows. Add the 50% batch
discount as a third curve so the projection matches all three real modes
(`sequential`/`concurrent`/`batch`) documented in `README.md`'s real 40-row
benchmark table, not just two of them.

## 6. Run the full 18-row golden-set quality eval — NEEDS USER CONFIRMATION (~£0.04 real spend)

Only 2 of 18 hand-labelled golden rows have been validated against the real API so
far (`evals/run_quality_eval.py --limit 2`: theme-Jaccard 1.0, sentiment exact-match
1.0). Running the remaining 16 rows costs real money (~£0.04 total) — confirm with
the user before spending, per this project's cost-tracking discipline.

## 7. Structural scale/latency testing at 1,000-20,000 rows (mock-based, no real API cost)

`evals/scale/generate_synthetic.py` exists but has only been used for basic
structural checks. Nothing yet drives `analyse.py --mode concurrent`/`batch`
end-to-end against synthetic data + the mock Anthropic server at 1k+ row volume to
measure actual wall-clock/memory scaling. This can be done entirely against the mock
server — no real API cost, safe to run without asking.

## 8. Real-scale rate-limit testing (checklist DEP4) — NEEDS USER CONFIRMATION (real spend/time)

Nothing models or tests Anthropic's real RPM/TPM rate limits at the 20,000-row
volume the brief describes. Testing this for real costs money and takes real wall-
clock time — confirm scope/budget with the user first.

## 9. GOV4 fairness check at a larger real sample — NEEDS USER CONFIRMATION (real spend)

Only the 2-row validation run exists; no check yet for systematic differences in
theme/sentiment classification across `respondent_type` at a meaningful sample size.
Depends on item 6 (the full golden-set run) being done first, and costs real money
beyond that.

## 10. DEP1: fallback provider/model for sustained outages

Still entirely unaddressed. `RunnableWithFallbacks`-equivalent logic (or an
`anthropic`-SDK-native fallback) for when the primary model is down for an extended
period — not implemented, not tested.

## 11. Batch mode real async failure/resume testing

`fetch_and_merge_results`/`wait_for_batch` are unit-tested against fakes only.
Nobody has actually killed the process mid-poll against a REAL in-flight Anthropic
batch and confirmed `--no-wait`/resume genuinely works end-to-end. This costs a
real (if modest) batch submission and takes real wall-clock time (batches can take
tens of minutes) — worth confirming scope before running.

## 12. Cache hit-rate degradation measurement (sequential vs. concurrent)

`README.md` asserts concurrent mode's cache hit rate is measurably worse than
sequential's ("several can race the first cache write"). This is asserted, not
measured — no test or chart currently substantiates it with real numbers.

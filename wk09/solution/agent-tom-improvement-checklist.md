# Improvement Checklist — Consultation Insights (Agent-Tom)

Tracks every issue/improvement identified against the brief's 5 pillars
(see `plans/agent-tom-eval-test-plan.md` for the full test/eval architecture
these items are checked against). Rules for using this file:

- Check an item off **only** when there is evidence it's fixed — a passing
  test, a scored eval result, or a doc — and fill in the `Evidence:` line
  with the specific file/test/section. An unchecked box with no evidence
  line means "not started or not yet proven," not "probably fine."
- IDs (`V1`, `C1`, ...) are stable references — use them in commit messages
  and `AI_LOG.md` entries (e.g. "fixes R1, R3") instead of re-describing
  the issue each time.
- New issues found during implementation get appended to the relevant
  pillar section with the next free ID — don't renumber existing IDs.

## Visibility

- [ ] **V1** — Per-run cost is visible: total tokens and £ spent analysing
      a batch is logged/reported by `analyse.py` itself (distinct from
      `ai-spend-log-Agent-Tom.csv`, which tracks the team's own dev-time
      Claude Code usage, not the pipeline's production runtime cost).
      Evidence:
- [ ] **V2** — Structured run logging: progress, retries, and failures are
      logged clearly (beyond bare `print`), so someone watching a live run
      can tell what's happening without reading code.
      Evidence:
- [ ] **V3** — Cost projection at scale: `project_cost.py` produces a
      documented £/time estimate at 20,000 rows, checked into
      `EVAL_REPORT.md`.
      Evidence:

## Correctness

- [ ] **C1** — Safe JSON parsing: a non-JSON model response does not crash
      the run (`starter/analyse.py:44`).
      Evidence: `tests/unit/test_parsing.py`
- [ ] **C2** — Idempotent re-run: re-running after a full/partial success
      does not re-call the API for rows already analysed
      (`starter/analyse.py:54-66` currently always re-analyses everything).
      Evidence: `tests/unit/test_checkpointing.py`
- [ ] **C3** — Output schema is validated: `themes` is restricted to the
      fixed 10-item list and `sentiment` to the fixed 4-value enum; a
      response that violates the schema is caught, not silently accepted.
      Evidence: `tests/unit/test_parsing.py`
- [ ] **C4** — Quality eval run and scored: theme/sentiment/summary output
      compared against the hand-labelled golden set, with a documented
      score (not just "looks reasonable").
      Evidence: `evals/run_quality_eval.py` + `EVAL_REPORT.md`

## Resilience

- [ ] **R1** — Incremental checkpointing: results are persisted as each row
      completes, not only in one write at the very end
      (`starter/analyse.py:54-66`).
      Evidence: `tests/system/test_resilience.py`
- [ ] **R2** — Resume after crash: killing the process mid-run and
      restarting it recovers already-completed rows and finishes the rest,
      without re-calling the API for completed rows.
      Evidence: `tests/system/test_resilience.py`
- [ ] **R3** — Bad-row isolation: one malformed/failing response is
      flagged and skipped, not allowed to crash the whole batch.
      Evidence: `tests/system/test_resilience.py`
- [ ] **R4** — Retry with bounded backoff on transient API errors
      (rate-limit / timeout); permanent failures are reported clearly, not
      retried forever or silently swallowed.
      Evidence: `tests/system/test_resilience.py`

## Security

- [ ] **S1** — No hardcoded API key fallback in source
      (`starter/analyse.py:11-15`, `"PASTE-YOUR-KEY-HERE"`).
      Evidence: `tests/unit/test_security.py`
- [ ] **S2** — API key never appears in logs, `results.json`, or exception
      messages/tracebacks.
      Evidence: `tests/unit/test_security.py`
- [ ] **S3** — Output escaping: consultation `response_text` (public,
      adversarial input) renders inert in `viewer.py` — no stored XSS.
      Evidence: `tests/unit/test_security.py`
- [ ] **S4** — CSV/formula-injection neutralised if results are ever
      exported to a spreadsheet tool (`=`, `@`, `+`, `-` leading
      characters).
      Evidence: `tests/unit/test_security.py`
- [ ] **S5** — Concurrent-run safety: two people running `analyse.py`
      against the same output at once does not corrupt `results.json`
      (README: "haven't checked").
      Evidence: `tests/system/test_operability.py`

## Operability

- [ ] **O1** — README reflects the actual, current run instructions
      (updated as the pipeline changes, not left describing the old
      one-shot script).
      Evidence:
- [ ] **O2** — Fresh-checkout run test: someone who isn't the author can
      run the pipeline end-to-end from the README alone.
      Evidence: `tests/system/test_operability.py`
- [ ] **O3** — Secrets/config handled cleanly (e.g. `.env` + `.gitignore`,
      no plaintext key ever committed).
      Evidence:

## Efficiency / cost (stretch — brief's "strong themes")

- [ ] **E1** — Redundant token usage reduced (e.g. prompt caching instead
      of resending the full instructions every call).
      Evidence:
- [ ] **E2** — Batch API adoption evaluated, and adopted if it holds up
      for this workload.
      Evidence:
- [ ] **E3** — Cheaper model evaluated for this task without a quality
      regression (checked against **C4**'s golden-set score).
      Evidence:

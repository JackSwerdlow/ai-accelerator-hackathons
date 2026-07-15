# Eval & Test Plan — Consultation Insights (Agent-Tom)

## Purpose

The brief (`context/hackathon-brief-2-consultation-insights.pdf`) says production-grade
is *evidence, not features*, and that we must show, by Wednesday afternoon:
visibility, correctness, resilience, security, and operability — as numbers and
demonstrations, not vibes. This plan defines the eval/test suite that produces
that evidence.

**Baseline finding (2026-07-15):** `solution/viewer.py` is byte-identical to
`starter/viewer.py`, and — until this pass — `solution/analyse.py` was
missing entirely; it has now been added as an exact copy of `starter/analyse.py`,
which is the correct starting point: `solution/` starts as a copy of `starter/`
and is refined iteratively from there, not written from scratch. This means
`solution/analyse.py` currently has every baseline sin listed below, unchanged.
The suite in this plan is written to run against **both** `starter/` (frozen,
permanent record of "the sin") and `solution/` (the same suite, run continuously
as the code is refined) from day one. Tests against `solution/` are **expected
to fail identically to `starter/` right now** — that's the correct starting
state, not a bug in the plan — and should be resolved one by one as
`solution/analyse.py` is iterated on, giving a concrete red-to-green trajectory
to show on Day 2.

**Scope:** the core pipeline only — `analyse.py` and `viewer.py`. `solution/spend/`
is out of scope for this suite (it's tooling for tracking the team's own AI spend,
not part of the production system being hardened).

## Known baseline behaviour (from reading `starter/analyse.py`)

These are the concrete, file-and-line-referenced "sins" the suite targets:

- `starter/analyse.py:11-15` — `ChatAnthropic` client and API key are constructed
  at **import time**, with a hardcoded `"PASTE-YOUR-KEY-HERE"` fallback baked into
  source if the env var is unset. This also means the module can't be imported in
  a test without a real (or monkeypatched) key already in the environment.
  `solution/analyse.py` has this same issue today (it's an unrefined copy) —
  deferring client construction out of import time is the first refinement
  step, and is what unlocks the unit-test tier below.
- `starter/analyse.py:44` — `json.loads(response.content)` with no error handling;
  comment literally says "the model always returns valid JSON (right?)". Any
  non-JSON completion crashes the whole run.
- `starter/analyse.py:54-66` — results accumulate in memory (`results.append`)
  and are written **once, at the very end**. A crash on row 39 of 40 (or row
  19,000 of 20,000, per the brief) loses every result computed so far. No
  checkpoint, no resume.
- `starter/analyse.py:11` — one blocking API call per row, full `INSTRUCTIONS`
  string (~20 lines) resent every time, no caching, priciest model implied by
  the brief's "priciest model" framing (this uses `claude-sonnet-5`; the brief's
  original prototype used something pricier still — confirm which model
  `solution/` targets before writing the cost-projection numbers).
- No handling at all for concurrent runs (README: "The policy team asked if two
  people running it at once would cause problems. Haven't checked.") — relevant
  to both resilience and operability.
- `viewer.py` renders `response_text` / `respondent_type` from `results.json`
  in a web page (not yet inspected in depth) — needs a check for whether
  user-controlled consultation text is escaped before rendering (stored XSS
  risk, since consultation responses are public/adversarial input).

## Architecture

Five components, each mapped to a brief pillar. Directory layout (new, under
`solution/`):

```
solution/
  tests/
    conftest.py              # shared fixtures: fixture CSVs, mocked LLM, tmp dirs
    system/                  # black-box, subprocess-driven
      test_resilience.py     # crash/resume, malformed JSON, rate-limit/timeout
      test_operability.py    # README-follow test, concurrent-run test
    unit/                    # pytest, mocked ChatAnthropic
      test_parsing.py        # JSON extraction/repair
      test_checkpointing.py  # checkpoint file read/write/resume logic
      test_security.py       # key handling, output escaping, injection
    baseline/
      test_starter_sins.py   # run against starter/, frozen, documents the crash
    fixtures/
      responses_tiny.csv     # 3-5 rows, deterministic, for fast unit tests
      responses_malformed.csv # rows engineered to trigger edge cases
  evals/
    golden_set.csv           # ~15-20 hand-labelled rows (theme/sentiment/summary)
    run_quality_eval.py      # scores solution's output against golden_set
    scale/
      generate_synthetic.py  # perturbs the 40 real rows up to N synthetic rows
      project_cost.py        # token-count-based £/time projection at 1k/20k rows
  EVAL_REPORT.md              # human-readable results snapshot, regenerated per run
```

### 1. Black-box system tests (Resilience + Operability)

Run `python analyse.py` / `python viewer.py` as subprocesses against fixture
CSVs, inspect `results.json`, exit codes, and stdout — not internals. This
survives whatever internal refactor `solution/analyse.py` goes through as it's
iterated on, which matters because it currently has the same internals as
`starter/analyse.py` and those will change significantly during refinement.

- **Resilience:**
  - Kill the process (`subprocess.Popen` + `terminate()`) after N of M rows
    complete; assert a resumed run recovers already-done rows without
    re-calling the (mocked) LLM for them, and completes the remainder.
  - Mock the LLM to return non-JSON on a specific row; assert the run does
    *not* crash the whole batch — it should flag/skip that row and continue,
    with the bad row visible in the output (not silently dropped).
  - Mock a rate-limit/timeout error from the API; assert retry-with-backoff
    behaviour (bounded retries, not an infinite loop) and that a
    permanent failure is reported clearly, not swallowed.
- **Operability:**
  - A test that does *only* what `README.md`'s "Running it" section says,
    from a clean checkout, and asserts it produces `results.json` +
    a reachable viewer — this is the automated form of "someone who isn't
    you could run it, from your README, tomorrow."
  - A concurrent-run test: launch two `analyse.py` processes against the
    same output path simultaneously; assert no corrupted/interleaved
    `results.json` (this directly answers the README's open question).

### 2. Unit tests (Correctness + Security)

Requires `solution/analyse.py` to expose testable functions (client
construction deferred out of import time — see Known baseline behaviour
above; this is not yet true today, since `solution/analyse.py` is currently
an unrefined copy of `starter/analyse.py`, so this test tier is blocked
until that first refinement lands). Mocked `ChatAnthropic`, no network, no cost.

- **Correctness:** JSON extraction/repair (fenced code blocks, leading/trailing
  prose, truncated output), checkpoint file format round-trips, idempotent
  resume (re-running after full success doesn't re-call the API for
  already-analysed rows — a directly stated brief requirement: *"Re-running
  re-analyses everything, including rows it has already done"* is the sin
  to fix, this test proves the fix).
- **Security:**
  - API key: never present in logs, in `results.json`, or in any exception
    message/traceback; no hardcoded fallback key in source.
  - Output escaping: a fixture row containing `<script>`/HTML in
    `response_text` must render inert in `viewer.py`'s HTML output (stored
    XSS check on public, adversarial input — the consultation responses are
    exactly this kind of untrusted input).
  - CSV/formula injection: a fixture row starting with `=`, `@`, `+`, `-`
    (spreadsheet formula injection) is neutralised if results are ever
    exported to CSV/Excel downstream.

### 3. Baseline snapshot suite (the "before" and the "before → after" trajectory)

Runs against `starter/`, frozen once written, never "fixed" — this is the
permanent record of "the sin":

- Reproduces the full-batch-loss crash: inject a malformed-JSON response
  partway through a run and assert `starter/analyse.py` crashes and
  `results.json` is never written (proves data loss), captured as evidence
  (exit code, traceback, absence of partial results) for the Day 2
  "before" slide.
- The *same* fixtures are run against `solution/analyse.py` on every commit,
  using identical scenarios. Right now — since `solution/analyse.py` is
  still an unrefined copy of `starter/analyse.py` — this run reproduces the
  exact same crash and data loss. That's the expected starting state, not a
  gap in the plan: it's proof the suite actually detects the sin, and it
  gives a concrete red baseline against `solution/` to turn green as the
  fix lands.
- `EVAL_REPORT.md` records the `starter/` run and the current `solution/`
  run side by side, updated as `solution/analyse.py` is refined — this is
  the literal "before and after" (and the trajectory between them) that the
  brief asks for in the Day 2 presentation.

### 4. Quality eval — scored, not pass/fail (Correctness, semantic)

Pass/fail tests can't judge whether a summary is *good* or a theme
classification is *right* — that needs a scored eval against ground truth.

- Hand-label ~15-20 rows of `data/responses_sample.csv` with a
  best-judgement theme set, sentiment, and a reference summary
  (`evals/golden_set.csv`).
- `run_quality_eval.py` calls the real API (small, bounded call count) with
  both the current prompt and (if `solution/` changes the prompt) the new
  prompt, and scores: theme set overlap (precision/recall against the
  fixed 10-theme list), sentiment exact-match rate, and a spot-check
  (human or LLM-as-judge, flagged as lower-confidence) on summary
  faithfulness.
- Every real-API run through this script logs a row to
  `solution/ai-spend-log-Agent-Tom.csv` with `Purpose = Testing`, per the
  root cost-tracking rule — this keeps eval cost itself visible.

### 5. Cost/scale projection (Visibility)

The 40-row sample can't demonstrate 20,000-row behaviour directly without
spending real budget on all 20,000 calls. Instead:

- `generate_synthetic.py` perturbs the 40 real rows (word-shuffling /
  concatenation / duplication with noise) to produce synthetic sets at
  1,000 and 20,000 rows, used only for structural load tests (memory,
  checkpoint-file growth, wall-clock scaling of non-API code paths) —
  **not** run through the real API at that volume.
- `project_cost.py` takes measured per-call token counts and per-call
  latency from a small real sample (e.g. the golden-set run above) and
  extrapolates: total £ cost and wall-clock time at 20,000 rows for (a)
  the current one-call-per-row approach and (b) whatever
  `solution/analyse.py` implements (batching / Batch API / caching, if
  pursued) — this is the concrete "the cost number moving" evidence the
  brief's Day 2 presentation asks for.
- Numbers go in `EVAL_REPORT.md` alongside the before/after functional
  results.

## Sequencing

1. **Now:** write `tests/baseline/`, `tests/system/`, and fixtures; run the
   suite against both `starter/` and today's `solution/analyse.py` (an
   unrefined copy). Freeze the `starter/` evidence. Expect `solution/` to
   fail identically to `starter/` at this point — record that as the
   starting red baseline, not a surprise. This alone is a deliverable: it
   demonstrates the sin with reproducible proof, usable in a Day 1
   presentation even before any fix lands.
2. **First refinement step — defer client construction out of import time
   in `solution/analyse.py`:** this alone doesn't fix any brief-stated sin,
   but it's the prerequisite that unlocks `tests/unit/` (mocked, no real
   API calls) — do this before or alongside the first behavioural fix.
3. **As `solution/analyse.py` is iteratively refined:** `tests/unit/` and
   the operability/resilience assertions in `tests/system/` are the TDD
   spec each change is written against. Track which assertions flip from
   red to green and when — that per-fix trajectory is itself evidence for
   the Day 2 presentation, not just the final green state.
4. **Once core correctness/resilience is green:** run the quality eval and
   scale/cost projection to quantify the improvement for the Day 2
   presentation, and regenerate `EVAL_REPORT.md`.

## Explicit limits of this plan (to state honestly, not hide)

- The quality eval's golden set (~15-20 rows) is a small, single-annotator
  sample — it demonstrates a scoring *method*, not statistically robust
  proof of quality at 20,000-response scale. Flagging this in the
  presentation is itself a production-grade behaviour per the brief.
- Structural load tests at 1k/20k synthetic rows exercise code paths, not
  real API behaviour at volume (real rate limits, real latency variance,
  real cost) — cost/latency numbers at that scale are a projection from a
  small real sample, not a measurement.
- Concurrent-run and crash-recovery tests cover the failure modes the
  brief explicitly names; they are not an exhaustive chaos-engineering
  suite. Any additional failure modes found ad hoc during implementation
  should be added as new fixtures, not treated as fully covered by this plan.
- This plan does not cover `solution/spend/` (out of scope per agreed
  scope) or infrastructure/deployment concerns (no Docker/CI in scope per
  the brief's ground rules).

## Open items to confirm once `solution/analyse.py`'s refined design is chosen

- Which model `solution/analyse.py` targets (affects the cost-projection
  numbers in `project_cost.py`).
- Whether `solution/` pursues the Batch API / prompt caching (a brief
  stretch direction) — if so, `project_cost.py` needs a third cost curve,
  not just old-vs-new-synchronous.

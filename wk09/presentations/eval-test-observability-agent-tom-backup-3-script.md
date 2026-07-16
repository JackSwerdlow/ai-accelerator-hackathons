# Backup 3 — Q&A notes: "The honest ledger — what Day 3 would hold."

Slide: `eval-test-observability-agent-tom-backup-3.html`

---

Use this if asked "so is it actually production ready?" or "what would you
do next?" — this slide *is* the answer, don't paraphrase it away.

- **Lead with this framing if pressed on "production ready":** nothing here
  is a vague "needs more testing" — every row names the exact gap, what it
  would take to close it, and whether it needs a go/no-go decision (cost or
  time) or is just unstarted work.
- **If asked "what's the single most important thing left?"** — reasonable
  answer: the CI gap (Jack's 40 tests aren't gated yet) and DEP1 (no fallback
  provider), because both are structural rather than "we ran out of time to
  measure something." The rate-limit and quality-eval items are more about
  spending real money/time to *confirm* things already believed true.
- **If asked why the checklist itself shows 0 checked off despite ~20 items
  being fixed** — that's an honest answer, not a defensive one: the
  checkbox-and-evidence bookkeeping pass is itself one of the named gaps.
  Don't claim more progress than the file shows; say the file is behind and
  that's tracked too.
- **S4 is the one deliberately-skipped item, not a mistake** — there's no
  CSV-export feature anywhere in the codebase yet, so there's nothing for the
  test to exercise. It's a documented `pytest.mark.skip`, findable by name,
  not a silent absence.

---

**Not timed** — reference material for follow-up questions only.

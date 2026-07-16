# Backup 2 — Q&A notes: "The checklist — and what's watching it."

Slide: `eval-test-observability-agent-tom-backup-2.html`

---

Use this if asked "how did you decide what to prioritise?", "how do you know
the model version is trustworthy?", or "what does 'observable' actually
mean here?"

- **The tally is re-counted, not quoted from memory.** 16 P0 / 15 P1 / 23 P2 /
  1 P3 / 2 F, summing to 57 — an earlier internal handoff note had a slightly
  different (stale) count; this one was re-derived directly from the
  checklist file on 2026-07-16, not copied forward.
- **The GOV3 story is the best answer to "how do we know you're not just
  guessing?"** The first instinct was wrong (assumed pinned dated-snapshot
  model IDs exist for every model) and it was checked, not asserted — a real,
  free API call (`client.models.list()`) settled it. That's the standard this
  team tried to hold itself to elsewhere too.
- **"Observable" is concrete, not a buzzword** — 5 named OTel metrics,
  `hide_inputs=True`/`hide_outputs=True` so consultation text and model output
  never leave the machine via telemetry, structured logs, all shipped to
  SigNoz today, not planned.
- **The CI gap is deliberately shown here, not hidden.** The pipeline runs one
  of two test suites automatically; the other (`test_analyse.py`, Jack's 40
  tests) passes locally but isn't yet gated — worth naming if asked "is this
  fully automated?"

---

**Not timed** — reference material for follow-up questions only.

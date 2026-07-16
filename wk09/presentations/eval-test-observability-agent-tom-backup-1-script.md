# Backup 1 — Q&A notes: "The bugs, in depth."

Slide: `eval-test-observability-agent-tom-backup-1.html`

---

Use this if asked "how exactly did the race condition work?" or "how sure are
you the fix actually works?" — not scripted for time, just talking points.

- **Why two stages, not one.** Fixing the temp-filename collision in
  `_save_state` changed the timing just enough to expose a second, previously
  masked race in `_clear_state` (an exists-then-unlink gap). This is a common
  shape with concurrency bugs — fixing the first race can change what the
  second one needs to hide behind. Worth saying explicitly if asked why the
  fix took two passes instead of one.
- **Why 100+ trials, not 1.** The bug was probabilistic (~1-in-5-6 real
  attempts before the fix), so a single successful run after the fix proves
  nothing either way. The test runs 6 trials × 12 concurrent-process attempts
  specifically because the failure is timing-dependent.
- **Was this an isolated incident?** No — the spend-tracker bug is the same
  root-cause *shape* (an unlocked, shared state file racing across concurrent
  writers), independently discovered in a completely different subsystem.
  That's a pattern worth deliberately checking for elsewhere in the codebase
  too — not yet done (see Backup 3).
- **If asked for the exact numbers again:** S5 repro rate ~1-in-5-6 before,
  0-in-100+ after. Spend-tracker: two wrong charges, £16.37 and £23.41, for
  two ordinary Claude Code turns.

---

**Not timed** — reference material for follow-up questions only.

# Speaker script — "Two lines collided. One bug didn't survive it." (~2.5-3 min)

Slide: `eval-test-observability-agent-tom.html` (now a full scrolling interactive
page, not a fixed slide — scroll to the "Walk the collision" panel before you
start talking)

---

Three of us worked on getting this analysis tool production-ready. My piece
was: does anyone actually believe it's fixed? So before Jack's rewrite of
analyse.py even existed, I wrote a 57-item hardening checklist and a test
suite against the original prototype's real sins — pinned as failing tests
against the actual original commit, before any fix code existed.

*[click dot 1 in the walkthrough panel, or it's already there on load]* That's
this step.

*[click dot 2]* And this is Jack, rewriting the same file from scratch, at the
same time, without either of us planning it. That could have been a disaster.

*[click dot 3 — the collision node opens]* Instead, reconciling the two is
exactly how we found a real bug: two people running the analyser at the same
time raced on an identical temp filename and crashed with a bare
FileNotFoundError — about one time in five or six, reproducibly. That's the
actual error, right there if anyone wants to read it.

*[click dot 4 — the satellite node]* And reconciling didn't just fix one
thing — it changed what we went and checked elsewhere. Our own AI
spend-tracking tool had logged sixteen and twenty-three pound charges for two
completely ordinary Claude Code turns. Same root cause, different file: an
unlocked, shared state file racing across concurrent sessions. The tool
watching our own safety net had its own bug.

*[click through dots 5, 6, 7 — or just hit Next three times]* We fixed both
races — the second one only visible once the first stopped hiding it. A
hundred-plus concurrent trials later: zero crashes. And it's not just
pass/fail any more: every run emits real OpenTelemetry traces, metrics, and
PII-safe logs to SigNoz.

*[scroll up slightly, point at the Verdict banner]* So — will this hold up in
production? Here's exactly how sure to be: what's verified by repeated
trials, what's actually measured rather than claimed, and three things we're
naming, not hiding, because a stakeholder deserves the honest ledger, not a
green checkmark and a shrug.

That's the pitch: we didn't just build tests. The tests found the bugs — and
we can tell you precisely how confident to be in what's left.

---

**Timing:** ~300 words, ~2.5-3 minutes at a natural conversational pace,
excluding stage directions. Clicking through the walkthrough live adds a few
seconds versus reading straight through — if running short, skip ahead with
Next rather than reading every narration line aloud (the panel's own text
covers it, you don't have to repeat it verbatim).

**Numbers on this page are live re-runs, not fixed claims** — before using
this script/page again, re-run `cd wk09/solution && python3 -m pytest
test_analyse.py tests/ -q` and update the "64 / 65" / "0 crashes" figures if
the count has moved. Live re-run on 2026-07-16: 64 passed, 1 skipped, 0
failed — matches the numbers on the page.

**Cost/caching is deliberately not on this page** — Jack's presentation covers
cost-at-scale and prompt caching; putting it here would double up. It still
lives in `wk09/solution/EVAL_REPORT.md` and is one of Backup 3's "honest
ledger" items if asked.

**Format note:** this page is a full scrolling interactive page (matching
Agent-Jack's `batch-vs-concurrent-decision-tool-agent-jack.html` style), not
the fixed 1280×720 slide the 3 backups still use — an intentional, temporary
split while the deck's overall format settles. If presenting live, have the
page pre-scrolled to the "Walk the collision" panel so the walkthrough is
already in view when you start talking.

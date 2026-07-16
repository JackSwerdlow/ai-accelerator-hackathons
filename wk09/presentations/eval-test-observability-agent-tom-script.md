# Speaker script — "Two lines collided. One bug didn't survive it." (~2.5-3 min)

Slide: `eval-test-observability-agent-tom.html`

---

Three of us worked on getting this analysis tool production-ready. My piece
was: does anyone actually believe it's fixed? So before Jack's rewrite of
analyse.py even existed, I wrote a 57-item hardening checklist and a test
suite against the original prototype's real sins — pinned as failing tests
against the actual original commit, before any fix code existed.

*[click the "Agent-Tom" step]* That's this line, running here.

*[click the "Agent-Jack" step]* And this is Jack, rewriting the same file
from scratch, at the same time, without either of us planning it. That
could have been a disaster.

*[click "Reconciliation finds a real race"]* Instead, reconciling the two
is exactly how we found a real bug: two people running the analyser at the
same time raced on an identical temp filename and crashed with a bare
FileNotFoundError — about one time in five or six, reproducibly. That's
the actual error, if anyone wants to see it.

*[click "Same shape, different file"]* And reconciling didn't just fix one
thing — it changed what we went and checked elsewhere. Our own AI
spend-tracking tool had logged sixteen and twenty-three pound charges for
two completely ordinary Claude Code turns. Same root cause, different
file: an unlocked, shared state file racing across concurrent sessions.
The tool watching our own safety net had its own bug.

*[click through "Both races fixed" → "100+ trials, 0 crashes" → "Now
observable" — or hit Play and let it walk itself]* We fixed both races —
the second one only visible once the first stopped hiding it. A
hundred-plus concurrent trials later: zero crashes. And it's not just
pass/fail any more: every run emits real OpenTelemetry traces, metrics,
and PII-safe logs to SigNoz.

*[point at the confidence ledger]* So — will this hold up in production?
Here's exactly how sure to be: what's verified by repeated trials, what's
actually measured rather than claimed, and three things we're naming, not
hiding, because a stakeholder deserves the honest ledger, not a green
checkmark and a shrug.

That's the pitch: we didn't just build tests. The tests found the bugs —
and we can tell you precisely how confident to be in what's left.

---

**Timing:** ~300 words, ~2.5-3 minutes at a natural conversational pace
(measured against this script's actual word count, not estimated). Clicking
through the timeline live adds a few seconds versus reading straight through —
budget for it; cut to "hit Play" if running short.

**Numbers on this slide are live re-runs, not fixed claims** — before using
this script/slide again, re-run `cd wk09/solution && python3 -m pytest
test_analyse.py tests/ -q` and update the "64 of 65" / "0 crashes" figures if
the count has moved. Live re-run on 2026-07-16: 64 passed, 1 skipped, 0
failed — matches the numbers baked into this slide.

**Cost/caching is deliberately not on this slide** — Jack's presentation
covers cost-at-scale and prompt caching; putting it here would double up. It
still lives in `wk09/solution/EVAL_REPORT.md` and is one of Backup 3's
"honest ledger" items if asked.

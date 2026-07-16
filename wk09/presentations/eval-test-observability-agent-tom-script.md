# Speaker script — "We didn't just fix it. We proved it — and caught two bugs." (~2.5-3 min)

Slide: `eval-test-observability-agent-tom.html`

---

Three of us worked on getting this analysis tool production-ready. My piece
was: does anyone actually believe it's fixed? So before Jack's rewrite of
analyse.py even existed, I wrote a 57-item hardening checklist and a test
suite against the original prototype's real sins — the crash-and-lose-
everything bug, the "re-run it and pay twice" bug — both frozen forever in
a baseline test against the actual original commit.

Then Jack rewrote analyse.py from scratch, underneath my suite, while I was
still writing it. That could have been a disaster. Instead, reconciling
the two is exactly how we found a real bug: two people running the
analyser at the same time raced on an identical temp filename and crashed
with a bare FileNotFoundError — about one time in five or six, reproducibly.
We fixed it, and then found a second, masked race in the cleanup path,
only visible once the first one stopped hiding it. A hundred-plus
concurrent trials later: zero crashes.

*[point at "Show me the crash" on the slide]* That's the actual error, if
anyone wants to see it.

Then something stranger came up, completely separate from analyse.py: our
own AI spend-tracking tool had logged sixteen and twenty-three pound
charges for two completely ordinary Claude Code turns — obviously wrong.
Same root cause, different file: an unlocked, shared state file racing
across concurrent sessions. Fixed with a file lock and a persisted dedup
set. The tool watching our own safety net had its own bug.

Where we are today: sixty-four of sixty-five tests green, one honestly
skipped because there's no code path yet to test it. Two real bugs, both
testing-found, both fixed and proven — not assumed fixed. And it's not
just pass/fail: every run now emits real OpenTelemetry traces, metrics,
and PII-safe logs to SigNoz, and using real measured tokens, we can tell
you this scales to twenty thousand rows roughly a third cheaper with
prompt caching than without it.

That's the pitch: we didn't just build tests. The tests found the bugs.
Backups have the rest — including exactly what we didn't get to.

---

**Timing:** ~365 words, ~2.5-3 minutes at a natural conversational pace (measured
against this script's actual word count, not estimated).

**Numbers on this slide are live re-runs, not fixed claims** — before using this
script/slide again, re-run `cd wk09/solution && python3 -m pytest test_analyse.py
tests/ -q` and `python3 evals/scale/project_cost.py`, and update the slide's chart
values/labels if either has moved. The 2026-07-15 "before" figures (56/3-4/1) are
a frozen historical fact from `EVAL_REPORT.md` and should NOT be regenerated.

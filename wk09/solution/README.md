# Consultation Insights

Analyses public consultation responses with AI: one-line summary, themes,
and sentiment per response, plus a results viewer.

Built in a rush before the 'Digital Identity in Public Services' consultation
closed. The policy team loved the demo. There is now talk of running every
DSIT consultation through it — the last one got 1,100 responses and the big
identity one is expected to get 20,000+.

**Status:** production-hardened for scale on the analysis side (see
"What changed from the prototype" below). `responses_sample.csv` is a 40-row
sample of the full export (the full file lives on the shared drive).

## Running it

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here     # Windows: set ANTHROPIC_API_KEY=your-key-here
python analyse.py                    # default: sequential, one request at a time
python analyse.py --mode concurrent  # fast: fires requests at once via a thread pool
python analyse.py --mode batch       # cheap: a single Message Batches API submission
python viewer.py                     # then open http://<host>:5001
```

### Which mode, when

There isn't one "right" mode — `--mode` is the tradeoff dial:

| Mode (flag) | Wall time, 40 rows | Cost, 40 rows | When to use it |
|---|---|---|---|
| `sequential` (default) | 103s | £0.083 (standard rate) | small/interactive runs, debugging a single response |
| `concurrent` | **11s** | £0.082 (standard rate) | you need the answer soon and are fine paying standard price |
| `batch` | ~26 min | **£0.0425** (50% batch discount) | large, non-urgent runs — the 20,000-row consultation this tool actually has to handle |

Those are real numbers from running the full 40-row sample through all three
modes, not estimates — see `AI_LOG.md` for the raw run output. The two big
takeaways:

- **`concurrent` is not `batch`.** Concurrent mode is what "send everything
  at once and get it back fast" actually means: many synchronous
  `client.messages.create()` calls fired in parallel via a thread pool,
  same per-token price as one-at-a-time. It was only added because a check
  of this account's rate limits (10,000 requests/min) confirmed 40
  concurrent requests is nowhere near the ceiling — worth checking for your
  own account/tier before assuming it'll scale.
- **`batch` optimises cost, not speed.** The Message Batches API is
  asynchronous — Anthropic's own SLA is up to 24h, with no guaranteed
  minimum speed, in exchange for 50% off token pricing. It is the right
  choice for the 20,000-row production run this brief describes (not
  time-sensitive, run once, feeds a report), and the wrong choice for
  anything where someone is waiting on the answer.

Useful flags on `analyse.py`:

| Flag | Applies to | Purpose |
|---|---|---|
| `--mode {sequential,concurrent,batch}` | all | pick the mode (default `sequential`) |
| `--concurrency N` | concurrent | max concurrent requests (default 10) |
| `--limit N` | all | only analyse the first N rows — cheap smoke test before a full run |
| `--no-wait` | batch | submit/check once and exit immediately (exit code 75 = "still processing") instead of blocking |
| `--status` | batch | just report on any in-flight batch, don't submit anything |
| `--force-resubmit` | batch | ignore an existing checkpoint and submit a brand new batch |
| `--model`, `--max-tokens`, `--input`, `--output`, `--state-file`, `--poll-interval` | all | override the defaults |

Run the tests with `python -m unittest test_analyse.py -v` (no API key needed —
they cover parsing, checkpointing, concurrency, and result-merging logic with
fakes, not live calls).

## Provenance

This file is the result of merging three parallel efforts, in this order:

1. **nhsbsa-sakiu's fix** to `starter/analyse.py` (results.json-based resume,
   a `json.JSONDecodeError` fallback) — the idea was moved into `solution/`
   (where it belongs) and `starter/` was restored to its original,
   untouched state, per this repo's read-only-starter convention.
2. **Susana's prompt-caching branch** — merged in for its `anthropic`-SDK
   foundation and its `UsageRecord`/`UsageTotals` cache instrumentation
   (hit/write/miss counts, cache hit rate), both still in place below.
3. **This batching work** — layered on top: the 3 `--mode`s, checkpoint/
   resume, tolerant parsing, and cost tracking, built on Susana's foundation
   rather than replacing it.

Agent-Tom's plain (unfixed) seed copy of `solution/analyse.py` predates all
three and is fully superseded; nothing further was needed from it.

## What changed from the prototype

The prototype (still in `../starter/`, untouched) had three problems the brief
called out explicitly, and used `langchain_anthropic` for its one-call-per-row
loop. `analyse.py` here fixes all three, in all three modes, using the plain
`anthropic` SDK directly instead. `langchain_anthropic`'s wrapper has no
equivalent to the Message Batches API (its own `.batch()` method is just local
thread-pool concurrency over single calls, i.e. this file's `concurrent` mode,
not real server-side batching), so there was no single client library that
covered all three modes — and Susana's branch reached the same "use `anthropic`
directly" conclusion independently, for the same underlying reason (needing
`cache_control` on the system prompt), which is good corroborating evidence
this wasn't just a personal preference.

1. **One API call per response, full instructions re-sent every time.**
   The shared instructions go into a `system` block marked `cache_control:
   {"type": "ephemeral"}` in every mode (`build_system_blocks()`), with the
   per-response text deliberately kept out of that cached prefix
   (`build_user_messages()`) so it never invalidates the cache — repeated
   calls within the cache TTL only pay full price for the instructions once,
   *when the block is large enough to be cacheable at all* (see the honest
   ledger below — right now, at this prompt's size, it isn't). This isn't
   just assumed to work either way: every run ends with a real "Prompt-cache
   usage summary" (`UsageTotals.summary_lines()`) reporting actual API calls,
   cache writes/hits/misses, and the cache hit rate, built from each
   response's real `cache_creation_input_tokens`/`cache_read_input_tokens`
   (`extract_usage()`) — not a projection, which is exactly how the
   below-threshold problem was caught rather than assumed away. In `batch`
   mode this also means the whole file goes into a *single*
   [Message Batch](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
   submission — one HTTP round trip regardless of row count.

2. **A crash loses everything — no resume, no checkpoints, no retries.**
   Every mode checkpoints its progress to `.batch_state.json`
   (write-then-rename, so a crash mid-write can't corrupt it) after every
   row (`sequential`/`concurrent`) or immediately after submission
   (`batch`). Re-running `analyse.py` against the same input/model/mode
   always checks this file first and picks up where it left off instead of
   starting over — you can Ctrl-C at any point and lose nothing but time.
   A batch you've already paid for is never resubmitted (and re-billed).
   Batches can legitimately sit `in_progress` for minutes to hours (that's
   normal, not a bug) — `--no-wait` lets you check in without blocking a
   terminal, so `batch` mode is safe to drive from a cron job or CI step,
   not just an interactive session.

3. **`json.loads` on raw model output.** `parse_model_output()` strips
   markdown code fences, recovers a JSON object embedded in extra text, and
   falls back to a safe placeholder (rather than crashing) when the model
   emits a theme outside the fixed allow-list or an invalid sentiment. A
   genuinely unparseable response, or an outright API error on that one
   request, becomes a `PARSE_ERROR`/`API_ERROR`/`BATCH_ERRORED` sentinel row
   (raw text/error preserved for debugging) instead of aborting the other
   39,999 rows in a 20,000-row run. This isn't hypothetical — the live
   40-row test run reproduced the exact malformed-output failure the
   prototype crashed on (row 17, a model emitting invalid pseudo-JS for an
   out-of-allowlist theme) and handled it as a sentinel row without
   affecting the other 39.

At 20,000+ rows, a single batch is still well within the Batch API's request
limit, so no chunking is needed for the sizes this brief describes; that
would be the next thing to add if the volume grew an order of magnitude
further.

## Cost tracking

There are two separate logs, deliberately not mixed together:

- **`ai-spend-log-{AGENT_NAME}.csv`** — Claude Code assistance cost
  (`CallType=ClaudeCode`), one row per assistant turn, written automatically
  by the Stop hook.
- **`ai-spend-log-{AGENT_NAME}-analysis-runs.csv`** — the cost of actually
  *running* `analyse.py` (`CallType=Claude API`, `Purpose=Data analysis`),
  one row per completed run, written by `analyse.py` itself via
  `spend/spend_logger.py:log_analysis_run()`. Its extra `RunMode` column
  records which of `sequential`/`concurrent`/`batch` produced that cost, so
  "what did the tool actually cost to run" doesn't get buried inside "what
  did the AI assistance cost." Both filenames still match the
  `ai-spend-log-*.csv` glob `spend/show_spend.py`/`plot_spend.py` use, so
  team-wide totals still include both.

Both use the token counts the API actually reports and the shared
`spend/pricing.py` rates, which now price cache writes/reads correctly
(`CACHE_WRITE_MULTIPLIER = 1.25`, `CACHE_READ_MULTIPLIER = 0.1`, applied to
the standard input rate) rather than treating all input tokens as
uncached — necessary once cache usage was being tracked explicitly, since
a flat per-token rate would misstate the very savings this feature exists
to prove. `batch` mode also passes `batch=True` to `cost_gbp()`, applying
Anthropic's 50% batch discount on top — `sequential`/`concurrent` are costed
at standard (cache-adjusted) rate. Together these logs are meant to answer
"what did this project actually cost, and on what" per the department's
FinOps ask.

**`claude-sonnet-5` is on an introductory rate right now.** Its rate in
`pricing.py` is `$2.00`/`$10.00` per million tokens, not the standard
`$3.00`/`$15.00` — Anthropic is running an introductory discount on this
model through **2026-08-31**, and every run in this project uses it as the
default model. Every logged cost in both CSVs was originally computed at
the standard rate and was therefore 50% too high; `AI_LOG.md` has the
correction, recomputed from raw token counts rather than a blanket
multiply. **Revert `pricing.py` to `{"input": 3.00, "output": 15.00}` once
the introductory window ends**, or costs will silently understate from
that date onward.

## Known limitations / honest ledger

- **Prompt caching currently provides zero measurable benefit at this
  prompt's size — confirmed live, not assumed.** `client.messages.count_tokens`
  puts the cacheable system-prompt block at ~307 tokens; Anthropic requires
  roughly 1024 tokens minimum before a block is eligible for caching on
  Sonnet-class models at all. A live 3-row smoke test in every mode showed
  `cache=miss` on 100% of calls, `Cache writes: 0, Cache hits: 0` — exactly
  what the ~307 vs ~1024 gap predicts, not a bug in `build_system_blocks()`
  or `extract_usage()`. The `cache_control` marker is correct and
  forward-looking (it would start working automatically if the instructions
  grew past the threshold — e.g. with few-shot examples), but as written
  today it's a no-op. Don't claim a caching cost saving in a presentation
  without re-running this check against whatever the live instructions
  happen to be at the time.
- `concurrent` mode's cache benefit is weaker than `sequential`'s in
  practice: requests fire close enough together that several can race the
  first cache write, so more of them pay the uncached input-token price
  than in `sequential` mode, where each call has time to see the previous
  cache write. The end-of-run cache summary makes this visible (compare
  `cache_hit_rate` between modes on the same input) rather than hiding it.
  Still cheaper in wall-clock time, just not a clean 2-for-1 on cost.
- No automated quality eval (e.g. a small labelled set to catch a prompt
  regression) exists yet — a natural next step, not attempted here.
- Two people running this against the same input/mode at the same time will
  both submit their own work (the checkpoint is local to the machine/repo
  checkout, not shared) — fine for now at this team size, would need a
  shared/locking checkpoint store to fully close out.

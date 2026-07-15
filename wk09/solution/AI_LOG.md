# AI Assistance Log

Format per `wk09/CLAUDE.md`: Date / Task / What AI Generated / What You Changed + Why.
Only meaningful (non one-shot) tasks are logged here — see repo-root `CLAUDE.md`
for why this is separate from commit messages.

## [Agent-Tom] 2026-07-15 — Spend tracking design and implementation

**Task:** Design and implement a token spend tracking solution for a 4-person team with separate machines and individual API keys, covering both `analyse.py` API calls and Claude Code assistant usage.

**What AI Generated:**
- Option A (per-agent CSV files + aggregation script) selected after presenting three approaches
- `spend/` directory with `pricing.py`, `spend_logger.py`, `show_spend.py`, `log_claude_code_session.py`, `install_hook.sh`, `remove_hook.sh`, `plot_spend.py`, `dashboard.py`
- Stop hook auto-detecting purpose category from `last_assistant_message` keywords
- Streamlit interactive dashboard with cumulative timeline, groupby toggle, daily burn rate, and token efficiency plots

**What You Changed + Why:**
1. **Purpose taxonomy added to CLAUDE.md** — initial design used free-text purpose descriptions ("Claude Code — wk09 (session 2)"). You directed that purposes should be fixed categories to enable retrospective analysis of where effort went. Added 11-category table and updated the hook's auto-detection to match.
2. **CSV location moved to `spend/`** — scripts originally wrote CSVs to `solution/`. You pointed out all spend files should live together in `spend/`. Moved CSV and updated all path references from `parent.parent` to `parent`.

---

## [Agent-Tom] 2026-07-15 — Three bugs introduced by AI and corrected by human

**Task:** Ongoing — bugs introduced during the spend tracking implementation that required human correction.

**What AI Generated (incorrectly):**

1. **NameError: `cwd` not defined** in `log_claude_code_session.py`
   - When rewriting `main()` to use `last_assistant_message` for purpose inference, the `cwd = data.get("cwd", "")` line was dropped. The CWD guard added later still referenced `cwd`, causing a `NameError` at hook runtime.
   - You: reported the error. Fix: added the missing `cwd` assignment.

2. **Wrong settings filename: `settings.json` instead of `settings.local.json`**
   - `install_hook.sh` wrote to `wk09/.claude/settings.json`. Claude Code's convention is that `settings.local.json` is the per-machine project override (untracked), while `settings.json` is the shared project config (committable).
   - You: opened `settings.local.json` in the IDE and flagged the mismatch. Fix: updated both `install_hook.sh` and `remove_hook.sh` to target `settings.local.json`.

3. **Dashboard `ROOT` path pointed at `solution/` not `spend/`**
   - All scripts used `Path(__file__).parent.parent` (= `solution/`), but after CSVs were moved into `spend/` the glob found nothing. Also lacked `.resolve()`, making the path sensitive to the directory from which the script was launched.
   - You: reported "No spend logs found" from the running dashboard. Fix: changed all five scripts to `Path(__file__).resolve().parent`.

---

## [Agent-Jack] 2026-07-15 — Rewrite analyse.py on the Message Batches API

**Task:** Replace the prototype's one-call-per-row `langchain_anthropic` loop
with the Anthropic Message Batches API, to address the brief's named sins
(priciest-model-per-call architecture, no resume/checkpoint, `json.loads` on
raw output crashing the whole run).

**What AI generated:** An initial design assumed (based on one Context7 doc
snippet showing `if batch.processing_status == "succeeded":`) that a
completed batch's `processing_status` field would read `"succeeded"`.

**What was changed + why:** Before writing the polling loop against that
assumption, ran a live one-request probe batch (`msgbatch_015HtgKtbh3EB9MEoigCfU9e`)
against the real API and printed `processing_status`/`request_counts` at
every poll. The real lifecycle is `"in_progress"` → `"ended"` — `"succeeded"`
only appears as a per-*individual-result* status inside `request_counts` and
each streamed result's `result.type`, never as the batch-level
`processing_status`. The doc snippet's example was a simplification, not the
literal field value. Rewrote `wait_for_batch()`/the `--no-wait` check to key
off `processing_status not in ("in_progress", "canceling")` instead of
matching a specific "done" string, so it doesn't silently hang forever if a
new intermediate status is ever added. This was caught by testing against
the real API rather than trusting the fetched docs verbatim — worth noting
for future library integration work in this repo.

Also discovered mid-task that a single-request batch stayed `in_progress`
for several minutes even for a trivial "say pong" prompt — this is normal
Batch API behaviour (not a bug), and is *why* `analyse.py` was designed
around a checkpoint-and-resume model (`--no-wait`, `.batch_state.json`)
rather than a script that blocks a terminal open until done: it needed to
be safe to run from something like a cron job or a CI step, and safe to
re-invoke after any crash without double-submitting (and double-billing)
the same batch.

**Files:** `solution/analyse.py`, `solution/test_analyse.py`,
`solution/README.md`, `solution/requirements.txt` (added `anthropic`).

**Live run result:** the real 40-row batch (`msgbatch_01SbgSad6orvB4pvMJnsJU1Y`)
took roughly 26 minutes to move from `in_progress` to `ended` — all 40
requests succeeded, 0 needed a `PARSE_ERROR`/`BATCH_ERRORED` fallback.
15,436 input / 4,083 output tokens, £0.085 total, logged automatically as
`Claude API` / `Data analysis`. `viewer.py` renders the output with zero
changes, confirming the `results.json` contract was preserved. A parallel
3-row diagnostic batch, submitted purely to check whether the 40-row
batch's slow start was size-related, was *still* `in_progress` after the
40-row batch had already finished — good evidence the delay was general
queue/capacity timing on the day, not something tied to request count.

## [Agent-Jack] 2026-07-15 — Add sequential/concurrent modes; fix batch discount and a stray spend-log file

**Task:** Follow-up after the batch run above, prompted by the user's
questions: (1) a spend-log file had appeared named after the machine's
hostname instead of an agent name, (2) why `anthropic` instead of
`langchain_anthropic`, and could/should it be just one library, (3) whether
the logged batch cost reflected the batch API's 50% discount, and (4) a
request to add a "what I originally thought batching meant" mode — firing
all 40 requests concurrently instead of one at a time — but only if the
account could actually support that much concurrency.

**What AI generated / what was wrong:**

1. **Stray spend file.** While probing the batch API earlier, I logged a
   tiny research call's spend via a one-off inline script and forgot to set
   `AGENT_NAME=Agent-Jack` on it. `spend_logger.py` falls back to
   `socket.gethostname()` when `AGENT_NAME` is unset, so it silently wrote
   `ai-spend-log-lab14102.labs.decoded.com.csv` instead of appending to
   `ai-spend-log-Agent-Jack.csv`. Fixed by merging that one row (correcting
   `AgentName`, same timestamp/tokens/cost) into the real log and deleting
   the stray file. This was a discipline gap on my part (forgetting the env
   var on an ad-hoc script), not a design flaw to fix in code — the lesson
   was "always set `AGENT_NAME` explicitly," not "change the fallback."

2. **Batch discount not applied.** `pricing.py`'s `cost_gbp()` had no
   concept of batch vs. standard pricing, so the previous entry's logged
   £0.085 for the 40-row batch was computed at the *standard* per-token
   rate applied to batch-processed tokens — actually overstating the cost
   by 2x. Anthropic's Message Batches API bills at 50% off standard
   pricing. Added a `batch: bool = False` parameter to `cost_gbp()`
   (default preserves old behaviour for the `ClaudeCode` Stop-hook caller,
   which never batches) and corrected the already-logged row from £0.085 to
   the true £0.0425.

**What was changed + why (design decisions, not corrections):**

- Confirmed nothing in `solution/` actually imports `langchain_anthropic`
  (`grep` came back empty outside `starter/`, which is untouched) — it was
  listed in `solution/requirements.txt` unused, likely carried over from
  `starter/requirements.txt` when the file was first created. Removed it;
  `analyse.py` now uses the plain `anthropic` SDK for all three modes
  (sequential/concurrent/batch) rather than mixing two client libraries for
  overlapping work.
- Checked this Anthropic account's actual rate limits before building the
  concurrent mode, per the user's explicit condition ("only add this if it
  can run all 40 at once, not just 2-3"): a raw `messages.create` call's
  response headers showed `anthropic-ratelimit-requests-limit: 10000`/min
  and multi-million token limits — 40 concurrent requests is nowhere near
  the ceiling, so the mode was worth building.
- Restructured `analyse.py` around `--mode {sequential,concurrent,batch}`
  (default `sequential`, matching the original prototype's behaviour)
  rather than separate boolean flags, so the three approaches are
  mutually exclusive by construction. All three now share one checkpoint
  schema (`mode` + `signature` folded together so switching modes can't
  accidentally resume another mode's stale progress) and one resilience
  story: `sequential`/`concurrent` checkpoint every row's result to disk
  immediately (not just batch's single `batch_id`), so a crash mid-run
  loses at most the one in-flight row, not the whole run — closing the
  same "no resume/retries" gap for these two modes that batch mode already
  had fixed.

**Files:** `solution/analyse.py` (major refactor), `solution/test_analyse.py`
(+7 tests for the new shared helpers/modes), `solution/README.md`,
`solution/requirements.txt` (removed `langchain-anthropic`),
`solution/spend/pricing.py` (`batch` discount param),
`solution/ai-spend-log-Agent-Jack.csv` (merged stray row, corrected cost).

**Live run result (real 40-row sample, all three modes):**

| Mode | Wall time | Cost | Sentinel rows |
|---|---|---|---|
| `sequential` | 103.4s | £0.0830 (standard) | 1 (row 17, malformed JS output) |
| `concurrent` (10 workers) | **11.3s** | £0.0822 (standard) | 1 (same row 17 failure mode) |
| `batch` | ~26 min | £0.0425 (batch discount) | 0 |

Row 17's failure — the model emitting invalid pseudo-JS
(`"inclusion".includes ? "accessibility":"accessibility"`) when it wants a
theme outside the fixed allow-list — is the exact real failure mode found
during initial exploration of the prototype, now reproduced live and
handled as a `PARSE_ERROR` sentinel in both direct-call modes without
affecting the other 39 rows.

## [Agent-Jack] 2026-07-15 — Split the analysis-run cost log; fix Purpose miscategorization

**Task:** Two more follow-up questions from the user: (1) the cost of
actually *running* `analyse.py` was mixed into the same CSV as Claude Code
session-assistance cost, and they wanted it in its own log that also records
which run mode (`sequential`/`concurrent`/`batch`) produced each cost; (2)
several `ClaudeCode` rows were tagged `Purpose=Debugging` for turns that
were mostly implementation work, not debugging.

**What was changed + why:**

1. **Separate cost log.** Added `spend_logger.log_analysis_run(mode, ...)`,
   writing to a new `ai-spend-log-{AGENT_NAME}-analysis-runs.csv` with an
   extra `RunMode` column, instead of `analyse.py` calling the general
   `log_row()`. Kept the filename matching the `ai-spend-log-*.csv` glob
   `show_spend.py`/`plot_spend.py` already use (checked both: they read via
   `csv.DictReader`/`pd.read_csv` on the header, so an extra column and an
   extra file are both harmless) — so per-agent and per-model team totals
   still include analysis-run cost, it's just no longer interleaved with
   Claude Code session rows in the same file. Migrated the 3 historical
   `Claude API`/`Data analysis` rows (batch/concurrent/sequential, logged
   earlier today) out of `ai-spend-log-Agent-Jack.csv` into the new file,
   backfilling `RunMode` from which run actually produced each cost value.
   (Also repeated the exact same `AGENT_NAME`-forgotten mistake from
   earlier in this session on the first smoke-test of the new function —
   caught and cleaned up immediately this time, no merge needed since it
   was just a throwaway 1-token test row, not real data.)

2. **`Debugging` miscategorization.** The Stop hook's `_infer_purpose()`
   picks the first category whose keywords appear in the last assistant
   message, and `Debugging`'s keyword list (`error`, `crash`, `fail`, `bug`,
   ...) is checked first. Several of this session's turns *talked about*
   error-handling/crash-resilience as the feature being built (`PARSE_ERROR`
   sentinels, "a crash loses everything") without the turn actually being
   about debugging broken code — that vocabulary alone was enough to
   trip the classifier. Went through the 6 `ClaudeCode` rows logged this
   session and reclassified by what was actually being done in that time
   window (using output-token volume as a rough signal of how much was
   generated, cross-referenced against the conversation):
   `Implementation` (the two large builds: the initial batch rewrite, and
   the later 3-mode refactor), `Research` (diagnosing/explaining the
   batch API's slow-start behaviour and the batch-vs-concurrent
   distinction), `Data analysis` (verifying the completed batch's
   `results.json`/`viewer.py`). None of the 6 were actually fixing broken
   code, so none stayed `Debugging`. This is a manual correction per
   `wk09/CLAUDE.md`'s own guidance ("You can override it by editing the CSV
   row directly if the auto-detection is wrong") — the classifier's
   keyword-order heuristic itself wasn't changed, since misclassification
   is already an acknowledged, expected limitation of that automation, not
   a bug to patch.

**Files:** `solution/spend/spend_logger.py` (new `log_analysis_run()`),
`solution/analyse.py` (calls the new logger), `solution/README.md`,
`solution/ai-spend-log-Agent-Jack.csv` (3 rows removed, 6 rows'
`Purpose` corrected), `solution/ai-spend-log-Agent-Jack-analysis-runs.csv`
(new).

## [Agent-Jack] 2026-07-15 — Reconcile the wk09 merge mess: Sakiu, Susana, Tom, then this work

**Task:** By the time this batching work was ready to commit, three other
agents had pushed to `main`: Agent-Tom seeded a plain (unfixed) copy of
`solution/analyse.py`; nhsbsa-sakiu fixed the JSON-crash/no-resume bugs
directly on `starter/analyse.py` (and, in the same commit, re-added
`starter/data/` and committed a `starter/results.json` - both against this
repo's read-only-starter convention); and Susana pushed an unmerged branch
(`origin/susana`) with a full alternate `solution/analyse.py` built around
proving prompt-cache effectiveness. The user's instruction: move Sakiu's fix
into `solution/` first and restore `starter/` to pristine, merge Susana's
branch resolving conflicts by taking whichever side is best practice, check
whether anything from Tom's seed still needed keeping, then apply this
session's batching work on top **without silently overwriting anything
better** from the other three.

**What was found, checked before acting on it:**

- `git diff --stat origin/main...origin/<branch> -- wk09/` for every other
  branch in the repo (`agent-dale/build`, both `agent-jack/*` branches,
  `david-dfe-agent`, `docs/hackathon-deck`, `research/stretch-second-pathway`,
  `sk/add_local_storage`) came back empty - confirmed these are other
  weeks'/teams' work with zero overlap with `wk09/`, so they were correctly
  left untouched rather than assumed irrelevant.
- Diffed Tom's seed against Sakiu's fixed `starter/analyse.py` directly and
  confirmed the seed predates the fix byte-for-byte (no try/except, no
  resume logic) - nothing from Tom's seed needed preserving beyond what
  Sakiu's version already had.
- Read Susana's actual `solution/analyse.py` rather than assuming what
  "prompt caching implementation" meant - it's raw `anthropic` SDK (not
  langchain), sequential-only (no batching/resume/JSON-robustness), built
  around `UsageRecord`/`UsageTotals`/`extract_usage()` to prove cache
  hit/write/miss with real numbers rather than just adding `cache_control`
  and hoping. This directly settled the standing "langchain vs anthropic"
  question from two commits ago - two independent implementations reaching
  the same conclusion for the same reason (needing `cache_control`) is real
  corroborating evidence, not a coin flip.

**What was done, in order:**

1. Moved Sakiu's fix from `starter/analyse.py` into `solution/analyse.py`
   (own commit), then reverted `starter/analyse.py` to its pre-fix content
   and removed `starter/data/`/`starter/results.json` (separate commit) -
   restoring the read-only-starter convention Sakiu's commit had broken,
   while keeping the value of what she found.
2. Merged `origin/susana` (`git merge --no-ff`). Two conflicts:
   `solution/analyse.py` (add/add - resolved by taking Susana's content
   wholesale, since it's a genuinely better foundation than the
   Sakiu-derived version from step 1, not just a different style) and
   `solution/requirements.txt` (resolved to `anthropic` per Susana's side,
   but with `pandas`/`matplotlib`/`streamlit`/`plotly` restored - her branch
   forked before Tom's spend-dashboard commits added those, so her copy
   never had them; that's a branch-timing gap, not an intentional removal).
   `solution/test_analyse.py` added cleanly, no conflict (new path on main).
3. Rewrote `analyse.py` to combine the 3-mode batching architecture from
   two commits ago with Susana's cache instrumentation, rather than
   picking one and discarding the other: `analyse_response()` keeps her
   exact signature (so her existing tests needed zero changes) but now
   calls the tolerant `parse_model_output()` instead of raw `json.loads`;
   `call_single_sync`/`run_sequential`/`run_concurrent`/
   `fetch_and_merge_results` all now build and accumulate her
   `UsageRecord`/`UsageTotals` instead of raw token-count integers, so
   every mode - not just hers - reports a real cache hit/write/miss summary
   at the end of a run.
4. Fixed a real gap this surfaced: `pricing.py`'s `cost_gbp()` had no
   concept of cache-write/cache-read pricing at all, so once cache usage
   was being tracked explicitly, leaving it un-costed would have made the
   log understate the very savings the new instrumentation exists to
   prove. Added `CACHE_WRITE_MULTIPLIER = 1.25` and
   `CACHE_READ_MULTIPLIER = 0.1` (Anthropic's standard ephemeral-cache
   pricing multipliers on the input rate), applied before the existing
   batch discount.
5. Combined `test_analyse.py`: kept Susana's cache/prompt-structure test
   classes verbatim (still passing unmodified against the merged file),
   adjusted this session's own tests for the new `UsageRecord`/`UsageTotals`
   return shapes (e.g. `fetch_and_merge_results` now returns `(results,
   totals, errors)`, not `(results, total_in, total_out, errors)`) - 40
   tests total, all passing.
6. Re-applied the unrelated `log_claude_code_session.py` cwd-guard fix and
   the analysis-run cost-log split from the previous two commits - neither
   touched by the merge, so these were clean re-applies, not re-resolutions.

**Files:** `starter/analyse.py` (reverted), `starter/data/`,
`starter/results.json` (removed), `solution/analyse.py` (rewritten, merges
Susana's instrumentation with this session's batching work),
`solution/test_analyse.py` (combined), `solution/requirements.txt`
(resolved via merge), `solution/spend/pricing.py` (cache-aware pricing
added), `solution/spend/spend_logger.py`, `solution/spend/
log_claude_code_session.py`, `solution/README.md` (provenance section
added, cache-cost limitation resolved), `solution/results.json`,
`solution/ai-spend-log-Agent-Jack*.csv`.

**Post-merge live smoke test surfaced a real finding, not a bug:** ran
`--mode sequential --limit 3` after wiring in Susana's cache instrumentation,
expecting to see it prove a cache hit on calls 2-3. Instead every call
showed `cache=miss`, `Cache writes: 0`, `Cache hits: 0`. Rather than assume
the instrumentation was broken, checked the actual cacheable block size via
`client.messages.count_tokens(model=..., system=build_system_blocks(), ...)`:
~307 tokens. Anthropic's minimum for a block to be cache-eligible at all on
Sonnet-class models is roughly 1024 tokens - this prompt is well under that,
so `cache_control` is currently a structural no-op, not a broken
implementation. `build_system_blocks()`/`extract_usage()` are both correct;
the instructions text itself is simply too short to benefit yet. Documented
prominently in `README.md`'s honest ledger rather than left to be discovered
the hard way in a live presentation - this is exactly the kind of thing
"visibility" (the brief's first success criterion) is supposed to catch.

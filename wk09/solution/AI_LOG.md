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

## [Agent-Jack] 2026-07-15 — Fix a real 50%-too-high cost figure: claude-sonnet-5's introductory price

**Task:** User asked to review the spend log because the numbers didn't
seem to match what they were actually being charged for these prompts.

**What was wrong:** `pricing.py`'s `MODELS["claude-sonnet-5"]` was
`{"input": 3.00, "output": 15.00}` - the model's *standard* rate. But
`claude-sonnet-5` currently has an **introductory rate of $2.00/$10.00 per
million tokens, in effect through 2026-08-31** - and today is 2026-07-15,
inside that window. Every cost figure logged this session used
`claude-sonnet-5` and was therefore overstated by exactly 50% (the intro
rate is 2/3 of standard, so charging at standard states the true cost as
1.5x). Verified against the current Claude API pricing reference (not
assumed) before touching anything. The pre-existing code comment on this
same line claiming `"claude-sonnet-5" is not a valid model ID` was also
simply wrong - both errors reinforced each other (a teammate skeptical the
model ID was even real would have had no reason to check whether its price
was current).

**What was changed:**

1. `spend/pricing.py`: corrected the rate to `{"input": 2.00, "output":
   10.00}`, with a comment giving the standard rate and the 2026-08-31
   expiry date so a future session knows to revert it.
2. Recomputed every affected row in both spend logs from their raw token
   counts through the corrected `cost_gbp()` (not a blanket ×0.667 multiply,
   to avoid compounding rounding error on rows that also had the batch
   discount or cache terms applied) - 6 `ClaudeCode` rows and all 4
   `Claude API`/analysis-run rows in the two CSVs.
3. While correcting those rows, also reclassified 3 more `ClaudeCode` rows
   that had appeared since the last Purpose-correction pass (all still
   auto-tagged `Debugging` by the same keyword-order heuristic) to
   `Implementation`/`Testing` based on what that turn actually did (the
   Sakiu/Susana/Tom merge reconciliation, and the verification pass before
   committing it) - same reasoning as the earlier correction, not a new
   pattern.

**Files:** `solution/spend/pricing.py`, `solution/ai-spend-log-Agent-Jack.csv`,
`solution/ai-spend-log-Agent-Jack-analysis-runs.csv`.

**Note for future sessions:** re-check this rate after 2026-08-31 - it needs
to revert to the standard $3.00/$15.00 once the introductory window ends.

## [Agent-Jack] 2026-07-15 — Fix the real bug: the Stop hook never counted cache tokens at all

**Task:** After the pricing fix above, the user checked our logged totals
against actual account usage and found a large mismatch - our CSV showed a
few pounds total; they were seeing roughly $45 of real usage for the
session. Asked to find and fix the actual discrepancy, not just assume the
"tracking started late" explanation from earlier in the session covered it.

**What was wrong:** `log_claude_code_session.py`'s `_parse_usage()` only
ever summed `usage.input_tokens` and `usage.output_tokens` from the
transcript. It never read `cache_creation_input_tokens` or
`cache_read_input_tokens` at all. In a long Claude Code session, almost all
"input" is served from the prompt cache - each turn resends the entire,
ever-growing conversation history, and the vast majority of that arrives as
a cache read rather than fresh input. Checked this directly on the real
transcript rather than assuming: across the ~300 assistant messages logged
this session, raw `input_tokens` totalled ~1,900 tokens, while
`cache_read_input_tokens` totalled **~120 million**. The hook's cost
calculation was built entirely on the ~1,900 number - the field that
actually drove real cost was never read at all. This wasn't the
"we started tracking late" gap from earlier - that was a real, separate,
smaller effect; this was a straightforward missing-field bug in the same
script, present since it was first written (before this session touched it).

**How it was found and verified, not assumed:**
1. Located this session's own transcript JSONL and directly summed
   `cache_creation_input_tokens`/`cache_read_input_tokens` across all
   assistant messages (deduplicated by message ID, same as the hook does) -
   confirmed the ~120M figure was real, not a parsing artefact.
2. Computed what the corrected total *should* be using the already-fixed,
   cache-aware `cost_gbp()` from two commits ago: ~£25 (~$32) at the
   introductory `claude-sonnet-5` rate, ~£38 (~$48) at the standard rate -
   both land close to the user's observed ~$45, versus the ~£3 (~$4) the
   buggy hook had actually logged. This is what confirmed the missing-cache-
   fields bug was the dominant cause, not a rounding or rate issue.
3. Reconstructed each of the 12 already-logged `ClaudeCode` rows from the
   real transcript rather than just fixing the code going forward: paired
   each row's timestamp to the transcript entries between it and the
   previous row's timestamp (both bounded by the point tracking was seeded
   from - see the earlier "cost tracking" entries), summed the correct
   fields per segment, and replaced each row's `UploadTokens`/`CostGBP` with
   the corrected values. Spot-checked that the reconstructed `input`/`output`
   figures matched the old logged values almost exactly per row (confirming
   the segment boundaries were reconstructed correctly) before trusting the
   newly-recovered cache figures layered on top.

**What was changed:**
1. `spend/log_claude_code_session.py`: `_parse_usage()` now also sums
   `cache_creation_input_tokens`/`cache_read_input_tokens`; `_write_row()`
   passes them into `cost_gbp()` for correct differential pricing, and now
   logs `UploadTokens` as the true total input-side volume (fresh + cache
   write + cache read) rather than just the fresh-input sliver - matching
   the convention `spend_logger.log_analysis_run()` already used. The
   `ImportError` fallback `cost_gbp` was updated to accept and price the
   same cache parameters, for parity.
2. `solution/ai-spend-log-Agent-Jack.csv`: all 12 `ClaudeCode` rows
   recomputed from the real transcript as above. Corrected total for this
   agent: **£21.48** (was £2.09) - roughly a 10x correction, consistent with
   the scale of the missing cache-read volume.

**What's still not fully reconciled, and why that's expected, not a new bug:**
- **`ai-spend-log-Agent-Tom.csv` almost certainly has the identical bug**
  (same shared hook script) but wasn't corrected here - this agent doesn't
  have access to Agent-Tom's session transcript to reconstruct it from, and
  guessing at his numbers would be worse than leaving them flagged as
  suspect. Worth Agent-Tom re-running the same reconstruction on his own
  transcript.
- **Still a real gap to the user's ~$45 figure** even after this fix
  (corrected team total here: ~£22.6, roughly $28.6 at the intro rate).
  Plausible remaining causes, none of which are fixable in this file: (a)
  whatever "usage" view the user is checking may show cost at the
  *standard* rate rather than the introductory rate this project's
  `pricing.py` deliberately uses (the standard-rate estimate above, ~$48,
  is actually closer to $45 than the intro-rate one) - if so our tool is
  self-consistently accurate to *this* project's chosen convention, just
  not to whatever the console displays; (b) there is a second session from
  earlier today on the same account (`734e69b9...`) not covered by this
  reconstruction at all; (c) a further ~18 assistant messages generated
  after the last logged row (during this very investigation) hadn't been
  captured by the hook yet at the time of this fix - they'll log
  automatically on the next Stop event.

**Files:** `solution/spend/log_claude_code_session.py`,
`solution/ai-spend-log-Agent-Jack.csv`.

---

## [Agent-Tom] 2026-07-15 — Implemented the eval/test plan; several assumptions in the plan itself turned out to be wrong

**Task:** Implement `plans/eval-test-plan-agent-tom.md` in full: `tests/` (baseline, system, unit), `evals/` (PII scan, golden-set quality eval, cost/scale projection), and a CI workflow. This entry's corrections were caught by actually running the code, not by a separate human review pass - logged here because the AI's first assumption differed from reality in ways worth recording, per the same rationale as the entries above.

**What AI Generated (and initially assumed, incorrectly):**

1. The plan asserted `solution/analyse.py`'s import-time `ChatAnthropic` client construction would block in-process unit testing, and named "defer client construction" as a required first refinement step before `tests/unit/` could exist.
   - **Corrected by testing, not assumption:** wrote a throwaway script that imported `analyse` with a dummy key and monkeypatched `analyse.llm` afterward - it worked immediately. SDK client construction doesn't make a network call, so nothing needed to change in `analyse.py` to unlock unit testing. Removed the refactor step from the plan (Purpose, Architecture §2, and Sequencing sections) and proceeded straight to writing `tests/unit/` against today's code.

2. The plan's "frozen baseline" design assumed `starter/` was still a read-only, unmodified reference of the original prototype's bugs.
   - **Corrected by running the baseline test and getting a confusing pass:** a collaborator (`nhsbsa-sakiu`, commit `44291c8`) had patched `starter/analyse.py` directly with checkpointing and safe JSON parsing, in violation of `wk09/CLAUDE.md`'s read-only rule for `starter/`. Running the "prove the crash" test against the *live* `starter/` directory would no longer reproduce the crash. Fix: extracted the original `starter/analyse.py` from git history (commit `f7a35f5`, before the patch) into `tests/fixtures/starter_analyse_original_snapshot.py`, verified its checksum against the git object, and pointed the baseline suite at that frozen snapshot instead of the live directory.

3. `evals/pii_scan.py`'s first NI-number regex was written as a strict validator excluding the letter combinations real NI numbers can't start with (per HMRC rules) - which meant it did **not** flag `tests/fixtures/responses_pii.csv`'s deliberate example, `QQ123456C`.
   - **Corrected by running the test fixture through it:** `QQ123456C` is HMRC's own documentation example, deliberately using an invalid prefix so it can never collide with a real person's number - exactly why a strict validator missed it. Since this is a screening scan (false positives are cheap, false negatives are the real risk), loosened the pattern to match the general two-letters/six-digits/one-letter shape rather than validating real NI-number rules.

4. Assumed (without checking) that the model string `"claude-sonnet-5"` used throughout `analyse.py` might need updating, after finding a comment in `spend/pricing.py` (unrelated tooling, written in an earlier session) claiming it "is not a valid model ID."
   - **Corrected with a real, minimal API call:** called the real Anthropic API with `model="claude-sonnet-5"` directly rather than trusting either claim - it returned a normal response. The `spend/pricing.py` comment is incorrect (likely written before this model existed) and is flagged in `EVAL_REPORT.md` so nobody "fixes" `analyse.py` to a worse model based on it. The verification call's tiny real cost (18 input / 4 output tokens) is logged to `spend/ai-spend-log-Agent-Tom.csv`.

**What was otherwise test-harness bugs, not product findings (fixed without ceremony):** `MockAnthropicServer.queue_json()` initially didn't accept token-count kwargs (`TypeError` on first run of `tests/system/test_visibility.py`); the README/viewer reachability test initially only caught `URLError`/`ConnectionError`, not the bare `TimeoutError` a slow-starting Flask server actually raised. Both were caught by watching tests fail for the wrong reason (per TDD's "verify RED" step) and fixed in the test harness, not the assertions.

---

## [Agent-Tom] 2026-07-15 — Diagnosed and fixed a real spend-log double-counting bug

**Task:** Investigate why two `ai-spend-log-Agent-Tom.csv` rows from this
session showed 73,574,226 and 118,180,028 "upload tokens" (£16.37 and
£23.41) for two ordinary Claude Code turns - a human (you) flagged this as
implausible after noticing the Purpose column was also miscategorised
("Debugging" for what was really "Testing" work).

**What AI investigated and found:** Recomputing the true, deduplicated
token total across the entire session transcript (`918b131a-....jsonl`,
2,146 lines) gave 126.5M input-equivalent tokens for 370 unique messages -
plausible for a very long session. Recomputing the *cumulative* running
total specifically at the line offsets recorded in
`~/.claude/spend_tracking_state.json` (459 / 1726 / 2106) gave 8.8M / 83.9M
/ 122.3M - closely tracking the two bogus CSV rows. That match is the
signature of "summed everything since the start of the file," not "summed
everything since the last checkpoint." Ruled out one candidate explanation
first: checked whether message IDs were re-emitted far apart in the
transcript (they weren't - all duplicates cluster within 20 lines of first
occurrence), so it isn't simple duplicate-write pollution.

**Root cause:** `log_claude_code_session.py`'s `_load_state`/`_save_state`
did a non-atomic, unlocked read-modify-write on a *single state file
shared across every concurrent Claude Code session/worktree in this
environment*. A write race between concurrent hook invocations can lose an
update to a session's line cursor; the next invocation then re-reads a
stale (lower) cursor, reprocesses a huge already-billed swath of the
transcript, and - because deduplication was by `msg_id` within a single
invocation's batch only, never persisted - re-bills tokens that were
already counted in an earlier row.

**Fix:**
- `_StateLock`: an `fcntl.flock`-based exclusive lock held across the
  entire load → process → write-CSV → save cycle in `main()`, so concurrent
  invocations (same session or different) can no longer race on the shared
  state file at all.
- `_save_state` now writes via write-temp-then-rename (matching the pattern
  already used for `analyse.py`'s own checkpoint file), so a crash mid-write
  can't corrupt the state file even without the lock.
- State now persists a bounded (last 2,000) set of already-billed
  `msg_id`s per session, not just a line-number cursor - a second,
  independent line of defence: even if the cursor is ever wrong again for
  some other reason, already-billed messages can't be re-billed.
- `tests/unit/test_spend_logging.py` (4 tests, all against tmp_path -
  never the real `~/.claude` state or a real CSV): reproduces the exact
  failure mode (a reverted line cursor after billing) and proves the fix
  yields the true total, not a doubled one; proves old-format
  (line-cursor-only) state entries migrate without crashing; proves the
  lock actually serialises two threads racing the critical section.

**What you changed + why:** Nothing - this was investigate-then-fix at
your explicit request, with no correction needed to the diagnosis or the
implementation.

---

## [Agent-Jack] 2026-07-16 — Split logged input tokens into fresh/cache-write/cache-read columns

**Task:** User asked, after checking `/model` and their live session cost, to
(a) confirm `pricing.py` stayed on the introductory `claude-sonnet-5` rate
(it had - no code was ever changed away from it, only compared against
standard rate for discussion) and (b) refactor the existing spend logs so
input tokens are tracked as separate fresh/cache-write/cache-read columns
instead of one combined total, since those three are priced very
differently (1x / 1.25x / 0.1x of the base input rate).

**What was wrong:** Both CSVs stored input-side volume as a single
`UploadTokens` total (fresh + cache write + cache read summed together).
`cost_gbp()` was always called with the correct three-way split under the
hood, so the *cost* figure was right, but the split itself was discarded
before it hit the CSV - meaning the cost could never be re-audited or
re-priced later without going back to raw transcripts, and cache
efficiency couldn't be analysed per row.

**What was changed:**

1. `spend/spend_logger.py` and `spend/log_claude_code_session.py`: header
   and write logic for both `_HEADERS`/`_ANALYSIS_HEADERS` now carry
   `FreshInputTokens`, `CacheCreationTokens`, `CacheReadTokens`,
   `OutputTokens` instead of `UploadTokens`/`DownloadTokens`. `log_row()`
   and `log_analysis_run()` signatures updated to accept the three input
   components separately rather than one pre-summed value.
2. `analyse.py`: the `log_analysis_run()` call site already had the three
   components on hand via `UsageTotals` (`uncached_input_tokens`,
   `cache_creation_tokens`, `cache_read_tokens`) - it was combining them
   into `total_input_tokens` purely to match the old single-column
   contract. That combination step is now gone; the components are passed
   straight through, so `analyse.py`'s cache-efficiency tracking (already
   correct in memory - see the earlier `UsageTotals` design from Susana's
   branch) is no longer lossy on the way to disk.
3. `wk09/CLAUDE.md` (Cost tracking section) and `solution/README.md`
   updated to describe the new four-column split instead of
   Upload/Download tokens, since the CLAUDE.md field list is the team-wide
   contract other agents' logging should also follow.

**Historical CSV rows - reconstructed where verifiable, left blank where not:**
The Stop hook only ever wrote the combined total to disk, so the exact
fresh/write/read split for already-logged rows wasn't sitting anywhere
retrievable - except the session's own raw transcript
(`~/.claude/projects/.../6a9a99d1-....jsonl`), which still had every
per-message `usage` object. Reconstructed by:

1. Deduping assistant messages by `message.id` (same rule `_parse_usage`
   uses) and segmenting them by the timestamp boundaries between
   consecutive already-logged rows - an approximation of the *real*
   segmentation, which is by raw line-index at each Stop-hook invocation
   (a detail not preserved anywhere history-side; only the current
   cumulative line offset is saved in `~/.claude/spend_tracking_state.json`).
2. Verifying each reconstructed segment against the row's own
   already-recorded `UploadTokens`/`DownloadTokens` (both fields had to
   match exactly, not just the total) before trusting it.
3. Of 16 pre-existing `ClaudeCode` rows, **11 matched exactly** and got the
   real split. **5 didn't** - the very first row (its true start-of-tracking
   boundary predates this transcript file in a way that can't be
   recovered; treating "start of file" as the boundary overcounts it by
   ~2x) and the four rows nearest the end of the reconstructible window
   (small-to-moderate mismatches, likely from async tool-result timestamps
   landing on the wrong side of a timestamp-based cutoff that the real
   line-index-based one wouldn't have been sensitive to). For those 5, the
   split columns were left **blank rather than fabricated** - `OutputTokens`
   and `CostGBP` are untouched (both were already exact and unambiguous).
   One further row (the tiny manual `Claude API`/`Research` test entry,
   14/4 tokens) isn't hook-derived at all; assumed all-fresh-input as a
   documented guess, not a reconstruction.
4. The 4 `ai-spend-log-Agent-Jack-analysis-runs.csv` rows have no
   equivalent raw-transcript source (they're real `anthropic` API calls
   from `analyse.py`, not local Claude Code messages) - left blank on the
   split for the same reason, `OutputTokens`/`CostGBP` unchanged.
5. One row (`Planning`, 15:03:45) was **already** in the new split format
   by the time this migration ran, because the code change (step 1 above)
   had taken effect mid-session and the Stop hook wrote a new-format row
   under the still-old header - the file was briefly malformed (mixed
   8-column/10-column rows) until this migration rewrote the header.
   That row's already-correct split values were kept as-is, not
   re-derived.

Total `CostGBP` across both files is unchanged by this migration (verified
by summing before/after) - only how the input side is broken down changed,
never the cost itself.

**What's still open:** `pricing.py` stayed on the introductory
`claude-sonnet-5` rate per explicit instruction, despite a live cross-check
this session that cuts the other way - the full live transcript, recomputed
end-to-end, comes to $40.36 at the introductory rate vs $60.54 at the
standard rate, and the user's own observed total ($60) matches the standard
figure far more closely. `/model` reports the introductory rate applies.
Neither this file nor `pricing.py`'s comment resolves that contradiction -
flagging it here so a future session checking the Console usage page
directly (rather than `/model` or `/usage`, both shown elsewhere in this
project to be local, possibly-stale estimates) can settle it for good.

**Files:** `solution/spend/spend_logger.py`,
`solution/spend/log_claude_code_session.py`, `solution/analyse.py`,
`wk09/CLAUDE.md`, `solution/README.md`,
`solution/ai-spend-log-Agent-Jack.csv`,
`solution/ai-spend-log-Agent-Jack-analysis-runs.csv`.

---

## [Agent-Jack] 2026-07-16 — Merged with Agent-Tom's concurrency fix; re-audited the unreconciled rows against his bug signature

**Task:** `git pull --rebase` (delayed until after the split-token work above,
which is itself a process slip against this repo's "pull before any file
changes" rule) surfaced a large incoming push from Agent-Tom - telemetry,
an eval framework, new tests, and his own independent rewrite of
`spend/log_claude_code_session.py` / `spend/spend_logger.py`: a real fix
for a race condition on the shared `~/.claude/spend_tracking_state.json`
(used by every concurrent Claude Code session/worktree on this machine,
not just one agent's), where a lost state update could regress a session's
line cursor and re-bill an already-billed swath of transcript - in his own
log this inflated two rows to 73M/118M tokens. He also added a
`Description` column. Discussed the merge approach with the user rather
than resolving unilaterally, given the size of the incoming change and
that it directly bears on whether this file's own historical numbers can
still be trusted.

**What was done:**

1. Resolved the 3-way conflicts in `spend/log_claude_code_session.py`,
   `spend/spend_logger.py`, and this file by combining both changes rather
   than picking one side: kept Tom's `_StateLock`/`billed_ids` fix and
   `Description` field, kept this session's fresh/cache-write/cache-read
   token split, in both `_HEADERS` and the row-writing code.
2. Backfilled a blank `Description` column onto the pre-existing rows in
   both Agent-Jack CSVs (the field didn't exist when they were written;
   left blank rather than guess at what each historical turn was about).
3. **Re-audited the 5 rows this session's earlier reconstruction couldn't
   verify exactly**, specifically testing whether they matched Tom's bug
   signature (a recorded total close to "everything since the true start
   of the transcript" rather than "everything since the previous
   checkpoint" - the tell-tale sign of a from_line reset to zero).
   **They didn't:** recomputing a from-transcript-start cumulative total
   for each of the 5 rows gave figures 2x-100x higher than what's actually
   recorded, nowhere near a match. Tom's exact failure mode (full reset) is
   ruled out for these specific rows. The likely explanation is still the
   original one from this session's earlier entry - the *real* segmentation
   is by raw line-index at each historical Stop-hook invocation, which
   isn't preserved anywhere (only the current cumulative offset survives in
   `spend_tracking_state.json`); this session's transcript-timestamp-based
   reconstruction is only an approximation of that, and approximations can
   be imprecise without the underlying data being wrong. Left these 5 rows'
   token-split columns blank, as before - not fabricating a number just
   because one plausible cause got ruled out.
4. Ran the full test suite post-merge. `tests/unit/test_spend_logging.py`
   (Tom's 4 concurrency tests) all pass against the merged code, confirming
   the header/row-write merge didn't break his fix. Separately, 11 of 40
   `test_analyse.py` tests fail with `AttributeError: 'NoneType' object has
   no attribute 'add'` from `telemetry.py`'s uninitialised metric
   instruments - confirmed via a throwaway `git worktree` against
   `origin/main` alone (no changes from this session at all) that this
   failure is **pre-existing on Tom's own commit**, unrelated to spend
   logging or this merge. Flagging it rather than fixing it - it's a
   different feature (his telemetry integration) with its own design
   intent this session doesn't have context on.

**What you changed + why:** Directed the merge strategy (merge both sides
and re-audit) rather than leaving it to a unilateral pick, given the
financial-integrity stakes of choosing wrong between two independently
correct-looking fixes.

**Files:** `solution/spend/log_claude_code_session.py`,
`solution/spend/spend_logger.py`, `solution/AI_LOG.md`,
`solution/ai-spend-log-Agent-Jack.csv`,
`solution/ai-spend-log-Agent-Jack-analysis-runs.csv`.

---

## [Agent-Jack] 2026-07-16 — Interactive "batch vs concurrent" decision tool (HTML)

**Task:** Turn the one-slide "Batch APIs: cheaper, not faster" lightning talk
into a larger, interactive HTML page for a company audience — one that lets a
viewer *select* when batch beats concurrent (and vice-versa) by dialling real
variables (request count, cost per request, concurrent/batch turnaround, cost
of waiting, and a manual-labour baseline), with live charts showing which mode
is cheapest for their case. Style modelled on `wk06/docs/tutorial/foi_demo_v2.html`.

**What AI generated:** A single self-contained page
(`wk09/presentations/batch-vs-concurrent-decision-tool-agent-jack.html`) — a
total-cost-of-ownership model (API cost + cost-of-waiting + manual labour), a
live recommendation banner, and three hand-built SVG charts: a stacked TCO bar,
a crossover line chart (x-axis toggles between request count and cost-of-waiting),
and a volume×urgency decision-map heatmap with a "you are here" marker. Defaults
seeded from the real measured 40-row run and `evals/scale/project_cost.py`.

**What you changed + why:**
- *Palette not eyeballed.* Ran the dataviz `validate_palette.js` before writing
  any colour: the first candidate (blue/green/amber) FAILED the dark-surface
  lightness band and sat in the 6–8 CVD floor. Switched to the reference
  palette's pre-validated steps (manual=orange, concurrent=blue, batch=green),
  which pass all checks on **both** light and dark surfaces.
- *SVG colour bug caught and fixed.* The first draft set fills/strokes as
  `setAttribute('fill','var(--…)')`. `var()` is not reliably resolved as an SVG
  *presentation attribute* (unlike a real CSS property), so colours could
  silently fail — and the theme toggle wouldn't recolour the charts. Added a
  `resolveVar()` step inside the `el()` helper that resolves custom properties
  to concrete hex (cached per render, re-resolved on theme change) — fixing all
  call sites at once and keeping the 2,000-cell map fast.
- *Adaptive region labels, not fixed ones.* Map labels are placed at each
  winning region's computed centroid and only drawn when the region is large
  enough — so a label can never sit in the wrong-coloured region as the
  boundaries move with the sliders (an earlier fixed-position `labelAt()` helper
  would have mislabelled shifted regions; it was removed).
- *Honest economics.* Kept the model faithful even where it undersells a mode:
  at 20k rows with someone waiting, concurrent wins because batch's multi-hour
  wait costs more than its 50% token saving; batch only wins once cost-of-waiting
  drops. Manual almost never wins for this cheap a task — surfaced as a finding,
  not hidden. Verified all state paths (presets, toggles, hover, both themes)
  produce no NaN/undefined geometry via a Node DOM-stub harness (no browser
  available in this environment).

**Files:** `wk09/presentations/batch-vs-concurrent-decision-tool-agent-jack.html`,
`wk09/solution/AI_LOG.md`.

---

## [Agent-Tom] 2026-07-16 — Built and substantially revised the Day 2 presentation slide

**Task:** Build a single self-contained interactive HTML "slide"
(`wk09/presentations/eval-test-observability-agent-tom.html` + paired
`-script.md`) presenting the eval/test/observability work for a ~10-minute,
4-person team demo. Needed to "wow," be quantitative, run 2-3 minutes, and
connect to the "production ready" goal.

**What AI generated (v1):** Matched the one existing precedent in the repo
(Agent-Jack's `lightning-talk-batch-apis-agent-jack.html`) closely: light
GDS-style palette, a 3-tile row (checklist / bugs / observability) plus two
bar charts (red→green test outcomes, cost-at-scale with caching) side by
side, one `<details>` crash-text reveal. Built via the dataviz skill (palette
validated, mark specs followed), committed as `50281ae`.

**What you changed + why (three rounds of revision, not a one-shot):**

1. First round: "wow the audience more - more interactivity, less focus on
   caching (that's Jack's), nicer graphics, don't be constrained by Jack's
   slide (it was an interim talk from yesterday) - refer to
   `wk06/solution/hackathon-report.html` for impact." This wasn't a small
   tweak - it explicitly rejected the precedent I'd been matching. Read
   wk06's report directly (dark theme, gradient hero text,
   `.stat-card`/`.agent-card`/`.timeline` patterns - confirmed via grep it
   has almost no actual JS, its richness is CSS gradients/`color-mix()`/
   hover-transitions, not animation) and re-planned the visual system from
   scratch around it instead of Jack's light convention.
2. Second round, before any code changed: "an interactive project timeline
   infographic... showing how steps were ordered, worked on in parallel,
   combined and influenced subsequent steps. Focus on one strong message."
   This reframed the whole layout: dropped the 3-tile grid and both bar
   charts entirely in favour of a single two-lane timeline (Agent-Tom's
   track / Agent-Jack's track) that visually collides at one node -
   literally showing "worked in parallel, combined" rather than describing
   it in prose.
3. Third round, after presenting the timeline plan: asked for concrete
   specifics on what's clickable, a "play button" flow-sequence, and - the
   substantive redirect - "put a stronger focus on giving stakeholders the
   assurance that improvements will hold up... what can we project and have
   confidence in and why." This added a 4th element that wasn't in either
   prior design: a 3-tier "confidence ledger" (Verified / Measured /
   Named-not-hidden) reframing the close of the pitch from "we found bugs"
   to "here's exactly how sure to be, and what isn't proven yet" - a
   genuinely different rhetorical move than the bug-story alone, driven
   entirely by the user's steer rather than something derivable from the
   brief alone.

**Verification before shipping:** re-ran `pytest test_analyse.py tests/ -q`
live (64 passed, 1 skipped, 0 failed - matches the numbers baked into the
slide); re-validated the new categorical palette (`199e70,9085e9,e66767,
008300`) with `scripts/validate_palette.js --mode dark --surface
"#0d0f14"` - all checks pass; checked HTML tag-matching and CSS
brace-balance with a small Python script, since no working headless browser
exists in this sandbox (chromium/playwright absent; firefox present but
snap-confined and fails under this environment's mount-namespace
restrictions). **A real-browser check of the finished slide is still
outstanding and flagged to the user** - structural validation is not a
substitute for seeing it render.

**Files:** `wk09/presentations/eval-test-observability-agent-tom.html`,
`wk09/presentations/eval-test-observability-agent-tom-script.md`,
`wk09/solution/AI_LOG.md`.

## [Agent-Jack] 2026-07-16 — Fix cost model: staff wages are Manual-only

**Task:** User review of the decision tool caught a modelling error — the
Concurrent/Batch bars carried a fixed "oversight" segment priced at the
employee hourly rate, i.e. the model was effectively paying staff wages
during the time spent waiting on the API.

**What AI generated (first version):** `costOf()` charged
`OVERSIGHT_HOURS × empRate` of labour to both API modes, shown as an orange
"Manual labour" slice on the Concurrent/Batch bars.

**What you changed + why:** Removed employee cost from the API modes entirely.
Staff wages now appear on **Manual only** (`N × minutes × rate`); Concurrent and
Batch are costed as API tokens + cost-of-waiting, where cost-of-waiting is an
explicit *business* opportunity cost (blocked work / SLA) on its own slider,
never wages — and it no longer applies to Manual (you pay people to do the
work, not to wait on a machine). Honest consequence, surfaced rather than
papered over: with the fake oversight floor gone, the API is so cheap per
request that Manual essentially never wins on cost, so the decision map is now
effectively Batch-vs-Concurrent. Updated the legend, the money-model copy, the
slider caption, the map note, and the "what's hardcoded" list to match.

**Files:** `wk09/presentations/batch-vs-concurrent-decision-tool-agent-jack.html`,
`wk09/solution/AI_LOG.md`.

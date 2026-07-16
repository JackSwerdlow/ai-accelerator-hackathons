# Consultation Insights - batch analyser
#
# Rewrite of starter/analyse.py with three interchangeable ways to drive the
# Anthropic API, so the cost/latency tradeoff is a flag, not a rewrite:
#
#   --mode sequential  (default) - one request at a time, same shape as the
#                        original prototype, but with the resilience/parsing
#                        fixes below. Slowest, standard price.
#   --mode concurrent  - fires many requests at once via a thread pool
#                        against the regular (synchronous) Messages API.
#                        Fast (bounded by --concurrency and account rate
#                        limits), but still standard price - no batch discount.
#   --mode batch       - a single Message Batches API submission. Cheapest
#                        (50% off token pricing) but async: can take minutes
#                        to hours, no latency guarantee. Right tool for a
#                        large, non-time-sensitive run (e.g. the 20,000-row
#                        consultation), wrong tool if you need the answer now.
#
# All three fix the three problems called out in the brief:
#   - one API call per response, full instructions re-sent every time
#       -> the shared instructions go into a `system` block marked
#          `cache_control: {"type": "ephemeral"}` in every mode, so repeated
#          calls within the cache TTL only pay full price for the first one.
#          Per-response text is deliberately kept OUT of that cached prefix
#          (see build_system_blocks/build_user_messages) so it never
#          invalidates the cache, and UsageTotals below proves - with real
#          hit/write/miss counts, not assumption - that caching is working.
#   - a crash loses everything, no resume/checkpoint/retry
#       -> every mode checkpoints its progress to disk after each row (or
#          after batch submission); re-running this script after a crash
#          resumes from where it left off instead of starting over (and,
#          for --mode batch, without resubmitting/re-billing the batch)
#   - json.loads on raw model output
#       -> tolerant parsing (strips markdown fences, recovers from
#          out-of-allowlist values) with a PARSE_ERROR/API_ERROR sentinel
#          per row instead of aborting the whole run
#
# Usage:
#   python analyse.py                        # sequential, 40 rows, one at a time
#   python analyse.py --mode concurrent       # same 40 rows, fired concurrently
#   python analyse.py --mode batch            # submit (or resume) a Message Batch
#   python analyse.py --limit 5               # cheap smoke test on any mode
#
# Safe to Ctrl-C and re-run at any point in any mode: the on-disk checkpoint
# means completed rows are never re-analysed (or, for batches, re-billed).

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from anthropic import Anthropic

_SOLUTION_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SOLUTION_DIR))
from spend.pricing import cost_gbp  # noqa: E402
from spend.spend_logger import log_analysis_run  # noqa: E402
import telemetry  # noqa: E402

DEFAULT_INPUT = _SOLUTION_DIR.parent / "data" / "responses_sample.csv"
DEFAULT_OUTPUT = _SOLUTION_DIR / "results.json"
DEFAULT_STATE_FILE = _SOLUTION_DIR / ".batch_state.json"
DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_MAX_TOKENS = 500
DEFAULT_POLL_INTERVAL = 20  # seconds
DEFAULT_CONCURRENCY = 10

ALLOWED_THEMES = [
    "privacy", "digital exclusion", "security", "business efficiency",
    "accessibility", "governance", "fraud reduction", "cost", "trust",
    "implementation",
]
ALLOWED_SENTIMENTS = ["supportive", "opposed", "mixed", "neutral"]

# Stable prefix — identical for every consultation response. This is what
# gets cached. Anything that varies per response (the response text, the
# row id, timestamps) MUST NOT appear here.
INSTRUCTIONS = """You are analysing responses to the UK government consultation
'Digital Identity in Public Services: Call for Views' run by the Department for
Science, Innovation and Technology.

The consultation asked the public and organisations for views on introducing
a certified, reusable digital identity for accessing public services, including
questions on privacy, inclusion, security, business impact, and governance.

For the consultation response below, produce a JSON object with exactly these
fields:
- "summary": a one-sentence neutral summary of the response
- "themes": a list of 1-3 themes from this fixed list ONLY:
  ["privacy", "digital exclusion", "security", "business efficiency",
   "accessibility", "governance", "fraud reduction", "cost", "trust",
   "implementation"]
- "sentiment": one of "supportive", "opposed", "mixed", "neutral"

Respond with ONLY the JSON object, no other text."""


def build_system_blocks(instructions: str = INSTRUCTIONS) -> list:
    """Return the `system` argument for messages.create with the stable
    prefix marked cacheable. Isolated as a function so tests can assert
    the shape without calling the API."""
    return [
        {
            "type": "text",
            "text": instructions,
            "cache_control": {"type": "ephemeral"},
        }
    ]


def build_user_messages(response_text: str) -> list:
    """Return the per-request `messages` argument. The response text is
    the ONLY dynamic content and it lives outside the cached prefix."""
    return [{"role": "user", "content": response_text}]


@dataclass
class UsageRecord:
    row_id: str
    model: str
    input_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    output_tokens: int

    @property
    def cache_status(self) -> str:
        if self.cache_read_input_tokens > 0:
            return "hit"
        if self.cache_creation_input_tokens > 0:
            return "write"
        return "miss"


def extract_usage(response: Any, row_id: str, model: str = DEFAULT_MODEL) -> UsageRecord:
    """Pull usage fields off a messages.create response defensively.
    Cache fields may be missing (older API) or None; treat both as 0."""
    usage = getattr(response, "usage", None)

    def _safe_int(obj: Any, name: str) -> int:
        val = getattr(obj, name, 0)
        return int(val) if val else 0

    return UsageRecord(
        row_id=row_id,
        model=getattr(response, "model", model) or model,
        input_tokens=_safe_int(usage, "input_tokens"),
        cache_creation_input_tokens=_safe_int(usage, "cache_creation_input_tokens"),
        cache_read_input_tokens=_safe_int(usage, "cache_read_input_tokens"),
        output_tokens=_safe_int(usage, "output_tokens"),
    )


@dataclass
class UsageTotals:
    api_calls: int = 0
    cache_writes: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    uncached_input_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    output_tokens: int = 0
    records: list = field(default_factory=list)

    def add(self, rec: UsageRecord) -> None:
        self.api_calls += 1
        self.uncached_input_tokens += rec.input_tokens
        self.cache_creation_tokens += rec.cache_creation_input_tokens
        self.cache_read_tokens += rec.cache_read_input_tokens
        self.output_tokens += rec.output_tokens
        if rec.cache_status == "hit":
            self.cache_hits += 1
        elif rec.cache_status == "write":
            self.cache_writes += 1
        else:
            self.cache_misses += 1
        self.records.append(rec)

    @property
    def cache_hit_rate(self) -> float:
        # First call cannot hit (nothing to hit yet). Rate is over
        # subsequent calls so it isn't diluted by the unavoidable write.
        eligible = max(self.api_calls - 1, 0)
        return (self.cache_hits / eligible) if eligible else 0.0

    def summary_lines(self) -> list:
        return [
            f"API calls:               {self.api_calls}",
            f"Cache writes:            {self.cache_writes}",
            f"Cache hits:              {self.cache_hits}",
            f"Cache misses:            {self.cache_misses}",
            f"Cache hit rate:          {self.cache_hit_rate:.1%}",
            f"Uncached input tokens:   {self.uncached_input_tokens}",
            f"Cache-creation tokens:   {self.cache_creation_tokens}",
            f"Cache-read tokens:       {self.cache_read_tokens}",
            f"Output tokens:           {self.output_tokens}",
        ]


class ParseError(Exception):
    pass


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compute_signature(rows, model, max_tokens, mode):
    """Fingerprint of (input rows, model params, mode) so a saved checkpoint
    can be checked against the current invocation before resuming it blindly."""
    h = hashlib.sha256()
    h.update(mode.encode())
    h.update(model.encode())
    h.update(str(max_tokens).encode())
    for row in rows:
        h.update(row["id"].encode())
        h.update(row["response_text"].encode())
    return h.hexdigest()


def _load_state(state_file):
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text())
    except json.JSONDecodeError:
        return None


def _save_state(state_file, state):
    # Write-then-rename so a crash mid-write can't corrupt the checkpoint.
    tmp = state_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(state_file)


def _clear_state(state_file):
    if state_file.exists():
        state_file.unlink()


def strip_code_fence(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[: -3]
    return text.strip()


def parse_model_output(text):
    """Recover a valid {summary, themes, sentiment} dict from raw model text.

    Handles the two failure modes observed against this exact prompt:
      1. output wrapped in a ```json ... ``` fence
      2. a syntactically-invalid JSON value (e.g. "x".slice(0,0) || "y")
         when the model wants to express a theme outside the allowlist
    Anything else is a genuine parse failure and raises ParseError, which
    the caller turns into a sentinel row rather than crashing the whole run.
    """
    cleaned = strip_code_fence(text)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ParseError(f"no JSON object found in output: {text!r}")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            raise ParseError(f"malformed JSON: {e}; raw output: {text!r}")

    if not isinstance(data, dict):
        raise ParseError(f"expected a JSON object, got {type(data).__name__}: {text!r}")

    summary = data.get("summary")
    if not isinstance(summary, str) or not summary:
        raise ParseError(f"missing/invalid 'summary' field: {text!r}")

    raw_themes = data.get("themes")
    if not isinstance(raw_themes, list):
        raise ParseError(f"missing/invalid 'themes' field: {text!r}")
    themes = [t for t in raw_themes if t in ALLOWED_THEMES]
    if not themes:
        # Model picked an out-of-allowlist theme (or produced malformed
        # entries) - fall back to a neutral placeholder rather than
        # discarding the whole row.
        themes = ["implementation"]

    sentiment = data.get("sentiment")
    if sentiment not in ALLOWED_SENTIMENTS:
        sentiment = "neutral"

    return {"summary": summary, "themes": themes, "sentiment": sentiment}


def _merge_row(row, analysis):
    return {
        "id": row["id"],
        "respondent_type": row["respondent_type"],
        "response_text": row["response_text"],
        **analysis,
    }


# ---------------------------------------------------------------------------
# Sequential / concurrent modes - direct (non-batch) Messages API calls
# ---------------------------------------------------------------------------

def analyse_response(client, response_text, row_id, model=DEFAULT_MODEL, max_tokens=DEFAULT_MAX_TOKENS):
    """Send one consultation response for analysis. Returns the parsed
    JSON result and a usage record proving whether the cached prefix
    was created / read / missed. Raises on API error or unparseable
    output - call_single_sync is what turns those into sentinel rows."""
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=build_system_blocks(),
        messages=build_user_messages(response_text),
    )
    text = "".join(
        block.text for block in resp.content if getattr(block, "type", None) == "text"
    )
    usage = extract_usage(resp, row_id, model=model)
    # Recorded here, before parse_model_output can raise: the API call was
    # made and billed regardless of whether the output goes on to parse.
    telemetry.record_response_size(len(text.encode("utf-8")))
    telemetry.record_spend(model, usage.input_tokens, usage.output_tokens,
                            cache_creation_tokens=usage.cache_creation_input_tokens,
                            cache_read_tokens=usage.cache_read_input_tokens, batch=False)
    telemetry.record_cache_status(usage.cache_status)
    analysis = parse_model_output(text)
    return analysis, usage


def call_single_sync(client, row, model, max_tokens):
    """One direct Messages API call for one row. Never raises - any API or
    parse failure becomes a sentinel row instead of crashing the run, the
    same principle the batch path applies per-result."""
    try:
        analysis, usage = analyse_response(client, row["response_text"], row["id"],
                                            model=model, max_tokens=max_tokens)
        telemetry.record_row_outcome("success")
    except ParseError as e:
        analysis = {"summary": "PARSE_ERROR", "themes": [], "sentiment": "neutral",
                    "parse_error": str(e)}
        usage = UsageRecord(row_id=row["id"], model=model, input_tokens=0,
                             cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=0)
        telemetry.record_row_outcome("parse_error")
        telemetry.log_parse_error(row["id"], str(e), e)
    except Exception as e:
        analysis = {"summary": "API_ERROR", "themes": [], "sentiment": "neutral",
                    "parse_error": str(e)}
        usage = UsageRecord(row_id=row["id"], model=model, input_tokens=0,
                             cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=0)
        telemetry.record_row_outcome("api_error")
        telemetry.log_api_error(row["id"], e)
    return _merge_row(row, analysis), usage


def run_sequential(client, rows, model, max_tokens, state, state_file):
    totals = UsageTotals()
    already_done = len(state["progress"])
    if already_done:
        print(f"Resuming: {already_done}/{len(rows)} rows already done.")
    for i, row in enumerate(rows, start=1):
        if row["id"] in state["progress"]:
            continue
        merged, usage = call_single_sync(client, row, model, max_tokens)
        totals.add(usage)
        state["progress"][row["id"]] = merged
        _save_state(state_file, state)
        print(f"  [{i}/{len(rows)}] done ({merged['sentiment']}, cache={usage.cache_status})")
    return totals


def run_concurrent(client, rows, model, max_tokens, state, state_file, max_workers):
    totals = UsageTotals()
    todo = [row for row in rows if row["id"] not in state["progress"]]
    done_count = len(rows) - len(todo)
    if done_count:
        print(f"Resuming: {done_count}/{len(rows)} rows already done.")
    print(f"Firing {len(todo)} requests with up to {max_workers} concurrent workers...")

    lock = Lock()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(call_single_sync, client, row, model, max_tokens): row
            for row in todo
        }
        for future in as_completed(futures):
            row = futures[future]
            merged, usage = future.result()
            with lock:
                totals.add(usage)
                state["progress"][row["id"]] = merged
                _save_state(state_file, state)
                done_count += 1
                print(f"  [{done_count}/{len(rows)}] done (row {row['id']}, "
                      f"{merged['sentiment']}, cache={usage.cache_status})")
    return totals


# ---------------------------------------------------------------------------
# Batch mode - Message Batches API
# ---------------------------------------------------------------------------

def build_requests(rows, model, max_tokens):
    return [
        {
            "custom_id": f"row-{row['id']}",
            "params": {
                "model": model,
                "max_tokens": max_tokens,
                "system": build_system_blocks(),
                "messages": build_user_messages(row["response_text"]),
            },
        }
        for row in rows
    ]


def submit_batch(client, rows, model, max_tokens):
    requests = build_requests(rows, model, max_tokens)
    return client.messages.batches.create(requests=requests)


def poll_once(client, batch_id):
    return client.messages.batches.retrieve(message_batch_id=batch_id)


def wait_for_batch(client, batch_id, poll_interval, on_poll=None):
    while True:
        batch = poll_once(client, batch_id)
        if on_poll:
            on_poll(batch)
        if batch.processing_status not in ("in_progress", "canceling"):
            return batch
        time.sleep(poll_interval)


def fetch_and_merge_results(client, batch_id, rows_by_id, model=DEFAULT_MODEL):
    """Returns (ordered_results, totals, error_count)."""
    by_custom_id = {}
    totals = UsageTotals()
    errors = 0

    for item in client.messages.batches.results(batch_id):
        row_id = item.custom_id.removeprefix("row-")
        row = rows_by_id.get(row_id, {"id": row_id, "respondent_type": "unknown", "response_text": ""})

        if item.result.type == "succeeded":
            message = item.result.message
            usage = extract_usage(message, row_id, model=model)
            totals.add(usage)
            raw_text = "".join(
                block.text for block in message.content if block.type == "text"
            )
            # Recorded regardless of parse outcome: the batch item succeeded
            # and was billed (at the batch discount) either way.
            telemetry.record_response_size(len(raw_text.encode("utf-8")))
            telemetry.record_spend(model, usage.input_tokens, usage.output_tokens,
                                    cache_creation_tokens=usage.cache_creation_input_tokens,
                                    cache_read_tokens=usage.cache_read_input_tokens, batch=True)
            telemetry.record_cache_status(usage.cache_status)
            try:
                analysis = parse_model_output(raw_text)
                telemetry.record_row_outcome("success")
            except ParseError as e:
                errors += 1
                analysis = {"summary": "PARSE_ERROR", "themes": [], "sentiment": "neutral",
                            "parse_error": str(e)}
                telemetry.record_row_outcome("parse_error")
                telemetry.log_parse_error(row_id, str(e), e)
        else:
            errors += 1
            detail = getattr(item.result, "error", None)
            analysis = {
                "summary": f"BATCH_{item.result.type.upper()}",
                "themes": [],
                "sentiment": "neutral",
                "parse_error": str(detail) if detail else item.result.type,
            }
            telemetry.record_row_outcome("api_error")
            telemetry.log_api_error(row_id, detail if detail else item.result.type)

        by_custom_id[row_id] = _merge_row(row, analysis)

    # Preserve original CSV order regardless of the order batch results stream in.
    ordered = [by_custom_id[row_id] for row_id in rows_by_id if row_id in by_custom_id]
    return ordered, totals, errors


def run_batch(client, rows, rows_by_id, args, signature, state, state_file):
    if state and state.get("mode") == "batch" and state.get("signature") == signature and not args.force_resubmit:
        print(f"Resuming existing batch {state['batch_id']} "
              f"(submitted {state['submitted_at']}) - not resubmitting.")
        batch_id = state["batch_id"]
    else:
        if state and not args.force_resubmit:
            print("Existing checkpoint doesn't match this input/model/mode - submitting a new batch.")
        print(f"Submitting batch of {len(rows)} requests (model={args.model})...")
        batch = submit_batch(client, rows, args.model, args.max_tokens)
        batch_id = batch.id
        state = {
            "mode": "batch",
            "signature": signature,
            "batch_id": batch_id,
            "model": args.model,
            "max_tokens": args.max_tokens,
            "row_count": len(rows),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        _save_state(state_file, state)
        print(f"Batch {batch_id} submitted and checkpointed to {state_file}.")
        print("Safe to Ctrl-C now - re-run this script any time to resume.")

    def report(batch):
        print(f"  status={batch.processing_status} counts={batch.request_counts}")

    if args.no_wait:
        batch = poll_once(client, batch_id)
        report(batch)
        if batch.processing_status in ("in_progress", "canceling"):
            print("Still processing - re-run later to check again.")
            sys.exit(75)  # EX_TEMPFAIL: not an error, just "not ready yet"
    else:
        print("Polling until the batch finishes (safe to Ctrl-C and re-run later)...")
        batch = wait_for_batch(client, batch_id, args.poll_interval, on_poll=report)
        if batch.processing_status in ("in_progress", "canceling"):
            return None  # interrupted mid-wait; state file still has the batch_id

    print("Batch finished - fetching results...")
    return fetch_and_merge_results(client, batch_id, rows_by_id, model=args.model)


def classify_outcomes(results):
    """Tally final results.json rows into success/parse_error/api_error
    counts for the batch.finished summary log. Every sentinel analyse.py
    can produce is one of: "PARSE_ERROR" (call_single_sync,
    fetch_and_merge_results), "API_ERROR" (call_single_sync), or a
    "BATCH_<TYPE>" batch-item failure (fetch_and_merge_results) - anything
    else is a real analysis and counts as success."""
    outcomes = {"success": 0, "parse_error": 0, "api_error": 0}
    for r in results:
        summary = r["summary"]
        if summary == "PARSE_ERROR":
            outcomes["parse_error"] += 1
        elif summary == "API_ERROR" or summary.startswith("BATCH_"):
            outcomes["api_error"] += 1
        else:
            outcomes["success"] += 1
    return outcomes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["sequential", "concurrent", "batch"], default="sequential")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--limit", type=int, default=None,
                         help="only analyse the first N rows (cheap smoke test)")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                         help="max concurrent requests for --mode concurrent")
    parser.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_INTERVAL,
                         help="[batch mode only] seconds between status checks")
    parser.add_argument("--no-wait", action="store_true",
                         help="[batch mode only] submit/check once and exit immediately")
    parser.add_argument("--force-resubmit", action="store_true",
                         help="[batch mode only] ignore any existing checkpoint and submit a new batch")
    parser.add_argument("--status", action="store_true",
                         help="[batch mode only] report on any in-flight batch and exit")
    args = parser.parse_args()

    if args.mode != "batch" and (args.no_wait or args.status or args.force_resubmit):
        parser.error("--no-wait/--status/--force-resubmit only apply to --mode batch")

    rows = load_rows(args.input)
    if args.limit:
        rows = rows[: args.limit]
    rows_by_id = {row["id"]: row for row in rows}
    signature = compute_signature(rows, args.model, args.max_tokens, args.mode)

    telemetry.init_telemetry()
    client = Anthropic()
    state = _load_state(args.state_file)

    if args.status:
        if not state or state.get("mode") != "batch":
            print("No in-flight batch checkpoint found.")
            return
        batch = poll_once(client, state["batch_id"])
        print(f"batch {batch.id}: {batch.processing_status} {batch.request_counts}")
        return

    started = telemetry.log_batch_started(args.model, len(rows))

    if args.mode == "batch":
        outcome = run_batch(client, rows, rows_by_id, args, signature, state, args.state_file)
        if outcome is None:
            return  # still processing, guidance already printed
        results, totals, error_count = outcome
        is_batch_pricing = True
    else:
        if not (state and state.get("mode") == args.mode and state.get("signature") == signature):
            state = {"mode": args.mode, "signature": signature, "progress": {}}
        print(f"Running {len(rows)} rows in {args.mode} mode (model={args.model})...")
        if args.mode == "sequential":
            totals = run_sequential(client, rows, args.model, args.max_tokens, state, args.state_file)
        else:
            totals = run_concurrent(client, rows, args.model, args.max_tokens, state,
                                     args.state_file, args.concurrency)
        results = [state["progress"][row["id"]] for row in rows]
        error_count = sum(1 for r in results if r["summary"] in ("PARSE_ERROR", "API_ERROR"))
        is_batch_pricing = False

    elapsed = time.monotonic() - started

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    cost = cost_gbp(args.model, totals.uncached_input_tokens, totals.output_tokens,
                     cache_creation_tokens=totals.cache_creation_tokens,
                     cache_read_tokens=totals.cache_read_tokens,
                     batch=is_batch_pricing)
    log_analysis_run(
        mode=args.mode,
        purpose="Data analysis",
        model=args.model,
        fresh_input_tokens=totals.uncached_input_tokens,
        cache_creation_tokens=totals.cache_creation_tokens,
        cache_read_tokens=totals.cache_read_tokens,
        output_tokens=totals.output_tokens,
        cost_gbp=cost,
    )

    telemetry.log_batch_finished(started, classify_outcomes(results), cost)

    _clear_state(args.state_file)

    print("\n--- Prompt-cache usage summary ---")
    for line in totals.summary_lines():
        print(line)

    print(f"\nSaved {len(results)} results to {args.output} "
          f"({error_count} needed a fallback/error sentinel) in {elapsed:.1f}s.")
    print(f"Cost: £{cost:.4f}"
          f"{' (batch discount applied)' if is_batch_pricing else ''} "
          f"(logged to ai-spend-log-*-analysis-runs.csv)")


if __name__ == "__main__":
    main()

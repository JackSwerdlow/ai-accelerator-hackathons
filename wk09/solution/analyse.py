"""Consultation Insights batch analyser with Anthropic prompt caching.

The stable analysis instructions go into a `system` block marked with
`cache_control: {"type": "ephemeral"}`. Each consultation response is
sent as a fresh user message and is deliberately kept OUT of the cached
prefix so it does not invalidate it.
"""

import csv
import json
import os
from dataclasses import dataclass, field
from typing import Any

from anthropic import Anthropic

MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 500

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


def build_system_blocks(instructions: str = INSTRUCTIONS) -> list[dict]:
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


def build_user_messages(response_text: str) -> list[dict]:
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


def extract_usage(response: Any, row_id: str) -> UsageRecord:
    """Pull usage fields off a messages.create response defensively.
    Cache fields may be missing (older API) or None; treat both as 0."""
    usage = getattr(response, "usage", None)

    def _safe_int(obj: Any, name: str) -> int:
        val = getattr(obj, name, 0)
        return int(val) if val else 0

    return UsageRecord(
        row_id=row_id,
        model=getattr(response, "model", MODEL) or MODEL,
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
    records: list[UsageRecord] = field(default_factory=list)

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

    def summary_lines(self) -> list[str]:
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


def analyse_response(
    client: Anthropic,
    response_text: str,
    row_id: str,
) -> tuple[dict, UsageRecord]:
    """Send one consultation response for analysis. Returns the parsed
    JSON result and a usage record proving whether the cached prefix
    was created / read / missed."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=build_system_blocks(),
        messages=build_user_messages(response_text),
    )
    text = "".join(
        block.text for block in resp.content if getattr(block, "type", None) == "text"
    )
    analysis = json.loads(text)
    return analysis, extract_usage(resp, row_id)


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    client = Anthropic(api_key=api_key)

    with open("data/responses_sample.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Analysing {len(rows)} responses with model {MODEL}...")
    totals = UsageTotals()
    results = []

    for i, row in enumerate(rows, start=1):
        analysis, usage = analyse_response(client, row["response_text"], row["id"])
        totals.add(usage)
        results.append(
            {
                "id": row["id"],
                "respondent_type": row["respondent_type"],
                "response_text": row["response_text"],
                **analysis,
            }
        )
        # Per-request cache evidence (no response content logged).
        print(
            f"  [{i}/{len(rows)}] id={usage.row_id} "
            f"cache={usage.cache_status} "
            f"in={usage.input_tokens} "
            f"cw={usage.cache_creation_input_tokens} "
            f"cr={usage.cache_read_input_tokens} "
            f"out={usage.output_tokens}"
        )

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved results.json")

    print("\n--- Prompt-cache usage summary ---")
    for line in totals.summary_lines():
        print(line)


if __name__ == "__main__":
    main()

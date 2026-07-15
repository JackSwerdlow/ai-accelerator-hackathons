"""Focused tests for prompt-cache wiring in analyse.py.

All API calls are mocked. No real credits are spent.
Run with: python -m unittest wk09/solution/test_analyse.py
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from analyse import (
    INSTRUCTIONS,
    UsageRecord,
    UsageTotals,
    analyse_response,
    build_system_blocks,
    build_user_messages,
    extract_usage,
)


def _fake_response(text: str, usage_kwargs: dict, model: str = "claude-sonnet-4-5"):
    """Build a SimpleNamespace shaped like an anthropic Message."""
    content = [SimpleNamespace(type="text", text=text)]
    usage = SimpleNamespace(**usage_kwargs)
    return SimpleNamespace(content=content, usage=usage, model=model)


ANALYSIS_JSON = json.dumps(
    {"summary": "s", "themes": ["privacy"], "sentiment": "neutral"}
)


class PromptStructureTests(unittest.TestCase):
    """Prove the cacheable prefix contains ONLY stable content and the
    per-request response text is outside it."""

    def test_stable_instructions_are_in_cacheable_prefix(self):
        blocks = build_system_blocks()
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block["type"], "text")
        self.assertEqual(block["cache_control"], {"type": "ephemeral"})
        # The instructions text itself is in the cached block.
        self.assertIn("Digital Identity in Public Services", block["text"])
        self.assertIn('"summary"', block["text"])
        self.assertIn('"themes"', block["text"])
        self.assertIn('"sentiment"', block["text"])

    def test_response_text_is_outside_cacheable_prefix(self):
        response_text = "I strongly oppose the proposed digital identity scheme."
        system = build_system_blocks()
        messages = build_user_messages(response_text)

        # response text must not appear in any system block
        for block in system:
            self.assertNotIn(response_text, block["text"])

        # response text must appear in the user message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], response_text)

    def test_two_different_responses_share_the_same_cached_prefix(self):
        a = build_system_blocks()
        b = build_system_blocks()
        # identical prefix content, byte-for-byte
        self.assertEqual(a, b)
        # dynamic parts differ
        self.assertNotEqual(
            build_user_messages("response A"),
            build_user_messages("response B"),
        )

    def test_changing_the_response_does_not_change_the_prefix(self):
        prefix_before = build_system_blocks()
        _ = build_user_messages("something completely different")
        prefix_after = build_system_blocks()
        self.assertEqual(prefix_before, prefix_after)
        # And the cached text must still be exactly the original instructions.
        self.assertEqual(prefix_after[0]["text"], INSTRUCTIONS)


class UsageExtractionTests(unittest.TestCase):
    def test_hit_write_miss_classification(self):
        write = extract_usage(
            _fake_response(
                ANALYSIS_JSON,
                {
                    "input_tokens": 5,
                    "cache_creation_input_tokens": 1200,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 40,
                },
            ),
            row_id="1",
        )
        hit = extract_usage(
            _fake_response(
                ANALYSIS_JSON,
                {
                    "input_tokens": 5,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 1200,
                    "output_tokens": 42,
                },
            ),
            row_id="2",
        )
        miss = extract_usage(
            _fake_response(
                ANALYSIS_JSON,
                {
                    "input_tokens": 300,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 45,
                },
            ),
            row_id="3",
        )
        self.assertEqual(write.cache_status, "write")
        self.assertEqual(hit.cache_status, "hit")
        self.assertEqual(miss.cache_status, "miss")

    def test_missing_cache_fields_do_not_crash(self):
        # Older responses may not include cache fields at all.
        resp = SimpleNamespace(
            content=[SimpleNamespace(type="text", text=ANALYSIS_JSON)],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
            model="claude-sonnet-4-5",
        )
        rec = extract_usage(resp, row_id="x")
        self.assertEqual(rec.cache_creation_input_tokens, 0)
        self.assertEqual(rec.cache_read_input_tokens, 0)
        self.assertEqual(rec.cache_status, "miss")

    def test_zero_or_none_cache_fields_do_not_crash(self):
        resp = _fake_response(
            ANALYSIS_JSON,
            {
                "input_tokens": 0,
                "cache_creation_input_tokens": None,
                "cache_read_input_tokens": None,
                "output_tokens": 0,
            },
        )
        rec = extract_usage(resp, row_id="y")
        self.assertEqual(rec.input_tokens, 0)
        self.assertEqual(rec.cache_creation_input_tokens, 0)
        self.assertEqual(rec.cache_read_input_tokens, 0)
        self.assertEqual(rec.output_tokens, 0)
        self.assertEqual(rec.cache_status, "miss")

    def test_missing_usage_object_entirely(self):
        resp = SimpleNamespace(
            content=[SimpleNamespace(type="text", text=ANALYSIS_JSON)],
            usage=None,
            model="claude-sonnet-4-5",
        )
        rec = extract_usage(resp, row_id="z")
        self.assertEqual(rec.input_tokens, 0)
        self.assertEqual(rec.output_tokens, 0)


class UsageTotalsTests(unittest.TestCase):
    def test_totals_and_hit_rate(self):
        totals = UsageTotals()
        # request 1: cache write
        totals.add(
            UsageRecord(
                row_id="1",
                model="claude-sonnet-4-5",
                input_tokens=5,
                cache_creation_input_tokens=1200,
                cache_read_input_tokens=0,
                output_tokens=40,
            )
        )
        # requests 2 & 3: cache read
        for rid in ("2", "3"):
            totals.add(
                UsageRecord(
                    row_id=rid,
                    model="claude-sonnet-4-5",
                    input_tokens=5,
                    cache_creation_input_tokens=0,
                    cache_read_input_tokens=1200,
                    output_tokens=42,
                )
            )
        self.assertEqual(totals.api_calls, 3)
        self.assertEqual(totals.cache_writes, 1)
        self.assertEqual(totals.cache_hits, 2)
        self.assertEqual(totals.cache_misses, 0)
        self.assertEqual(totals.uncached_input_tokens, 15)
        self.assertEqual(totals.cache_creation_tokens, 1200)
        self.assertEqual(totals.cache_read_tokens, 2400)
        self.assertEqual(totals.output_tokens, 124)
        # 2 hits out of (3-1) eligible follow-up calls = 100%
        self.assertAlmostEqual(totals.cache_hit_rate, 1.0)

    def test_hit_rate_with_zero_calls_is_zero(self):
        totals = UsageTotals()
        self.assertEqual(totals.cache_hit_rate, 0.0)

    def test_hit_rate_with_only_one_call_is_zero(self):
        totals = UsageTotals()
        totals.add(
            UsageRecord(
                row_id="1",
                model="claude-sonnet-4-5",
                input_tokens=300,
                cache_creation_input_tokens=0,
                cache_read_input_tokens=0,
                output_tokens=10,
            )
        )
        # No follow-up call yet — dividing by (1-1) must not throw.
        self.assertEqual(totals.cache_hit_rate, 0.0)


class AnalyseResponseBehaviourTests(unittest.TestCase):
    """The existing behaviour — parses JSON out of the model reply and
    returns a dict — must still work after adding caching."""

    def test_returns_parsed_json_and_usage(self):
        client = MagicMock()
        client.messages.create.return_value = _fake_response(
            ANALYSIS_JSON,
            {
                "input_tokens": 5,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 1200,
                "output_tokens": 40,
            },
        )
        analysis, usage = analyse_response(client, "resp text", row_id="42")
        self.assertEqual(analysis["summary"], "s")
        self.assertEqual(analysis["themes"], ["privacy"])
        self.assertEqual(analysis["sentiment"], "neutral")
        self.assertEqual(usage.row_id, "42")
        self.assertEqual(usage.cache_status, "hit")

    def test_call_sends_cache_control_and_isolates_response(self):
        client = MagicMock()
        client.messages.create.return_value = _fake_response(
            ANALYSIS_JSON,
            {
                "input_tokens": 5,
                "cache_creation_input_tokens": 1200,
                "cache_read_input_tokens": 0,
                "output_tokens": 40,
            },
        )
        analyse_response(client, "unique response body", row_id="1")

        _, kwargs = client.messages.create.call_args
        # system carries the cache_control marker...
        self.assertEqual(
            kwargs["system"][0]["cache_control"], {"type": "ephemeral"}
        )
        # ...and does NOT contain the per-request text.
        self.assertNotIn("unique response body", kwargs["system"][0]["text"])
        # user message carries the per-request text.
        self.assertEqual(kwargs["messages"][0]["content"], "unique response body")


if __name__ == "__main__":
    unittest.main()

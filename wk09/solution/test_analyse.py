# Unit tests for analyse.py - no network calls, no API key required.
# Run with: python -m unittest test_analyse.py -v
#
# Two sets of tests, kept together deliberately: the prompt-cache/usage
# tests (PromptStructureTests, UsageExtractionTests, UsageTotalsTests,
# AnalyseResponseBehaviourTests) came from Susana's prompt-caching branch;
# everything else covers the batching/resilience work built on top of it.

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock

import analyse


def _row(id_, text, respondent_type="individual"):
    return {"id": id_, "respondent_type": respondent_type, "response_text": text}


def _merge_row_stub(id_, summary):
    return {"id": id_, "respondent_type": "individual", "response_text": "a",
            "summary": summary, "themes": [], "sentiment": "neutral"}


ANALYSIS_JSON = json.dumps(
    {"summary": "s", "themes": ["privacy"], "sentiment": "neutral"}
)


def _fake_response(text, usage_kwargs, model="claude-sonnet-5"):
    """Build a SimpleNamespace shaped like an anthropic Message."""
    content = [SimpleNamespace(type="text", text=text)]
    usage = SimpleNamespace(**usage_kwargs)
    return SimpleNamespace(content=content, usage=usage, model=model)


# ---------------------------------------------------------------------------
# Prompt-cache wiring (from Susana's branch)
# ---------------------------------------------------------------------------

class PromptStructureTests(unittest.TestCase):
    """Prove the cacheable prefix contains ONLY stable content and the
    per-request response text is outside it."""

    def test_stable_instructions_are_in_cacheable_prefix(self):
        blocks = analyse.build_system_blocks()
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(block["type"], "text")
        self.assertEqual(block["cache_control"], {"type": "ephemeral"})
        self.assertIn("Digital Identity in Public Services", block["text"])
        self.assertIn('"summary"', block["text"])
        self.assertIn('"themes"', block["text"])
        self.assertIn('"sentiment"', block["text"])

    def test_response_text_is_outside_cacheable_prefix(self):
        response_text = "I strongly oppose the proposed digital identity scheme."
        system = analyse.build_system_blocks()
        messages = analyse.build_user_messages(response_text)

        for block in system:
            self.assertNotIn(response_text, block["text"])

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], response_text)

    def test_two_different_responses_share_the_same_cached_prefix(self):
        a = analyse.build_system_blocks()
        b = analyse.build_system_blocks()
        self.assertEqual(a, b)
        self.assertNotEqual(
            analyse.build_user_messages("response A"),
            analyse.build_user_messages("response B"),
        )

    def test_changing_the_response_does_not_change_the_prefix(self):
        prefix_before = analyse.build_system_blocks()
        _ = analyse.build_user_messages("something completely different")
        prefix_after = analyse.build_system_blocks()
        self.assertEqual(prefix_before, prefix_after)
        self.assertEqual(prefix_after[0]["text"], analyse.INSTRUCTIONS)


class UsageExtractionTests(unittest.TestCase):
    def test_hit_write_miss_classification(self):
        write = analyse.extract_usage(
            _fake_response(ANALYSIS_JSON, {
                "input_tokens": 5, "cache_creation_input_tokens": 1200,
                "cache_read_input_tokens": 0, "output_tokens": 40,
            }), row_id="1",
        )
        hit = analyse.extract_usage(
            _fake_response(ANALYSIS_JSON, {
                "input_tokens": 5, "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 1200, "output_tokens": 42,
            }), row_id="2",
        )
        miss = analyse.extract_usage(
            _fake_response(ANALYSIS_JSON, {
                "input_tokens": 300, "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0, "output_tokens": 45,
            }), row_id="3",
        )
        self.assertEqual(write.cache_status, "write")
        self.assertEqual(hit.cache_status, "hit")
        self.assertEqual(miss.cache_status, "miss")

    def test_missing_cache_fields_do_not_crash(self):
        resp = SimpleNamespace(
            content=[SimpleNamespace(type="text", text=ANALYSIS_JSON)],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
            model="claude-sonnet-5",
        )
        rec = analyse.extract_usage(resp, row_id="x")
        self.assertEqual(rec.cache_creation_input_tokens, 0)
        self.assertEqual(rec.cache_read_input_tokens, 0)
        self.assertEqual(rec.cache_status, "miss")

    def test_zero_or_none_cache_fields_do_not_crash(self):
        resp = _fake_response(ANALYSIS_JSON, {
            "input_tokens": 0, "cache_creation_input_tokens": None,
            "cache_read_input_tokens": None, "output_tokens": 0,
        })
        rec = analyse.extract_usage(resp, row_id="y")
        self.assertEqual(rec.input_tokens, 0)
        self.assertEqual(rec.cache_creation_input_tokens, 0)
        self.assertEqual(rec.cache_read_input_tokens, 0)
        self.assertEqual(rec.output_tokens, 0)
        self.assertEqual(rec.cache_status, "miss")

    def test_missing_usage_object_entirely(self):
        resp = SimpleNamespace(
            content=[SimpleNamespace(type="text", text=ANALYSIS_JSON)],
            usage=None,
            model="claude-sonnet-5",
        )
        rec = analyse.extract_usage(resp, row_id="z")
        self.assertEqual(rec.input_tokens, 0)
        self.assertEqual(rec.output_tokens, 0)


class UsageTotalsTests(unittest.TestCase):
    def test_totals_and_hit_rate(self):
        totals = analyse.UsageTotals()
        totals.add(analyse.UsageRecord(
            row_id="1", model="claude-sonnet-5", input_tokens=5,
            cache_creation_input_tokens=1200, cache_read_input_tokens=0, output_tokens=40,
        ))
        for rid in ("2", "3"):
            totals.add(analyse.UsageRecord(
                row_id=rid, model="claude-sonnet-5", input_tokens=5,
                cache_creation_input_tokens=0, cache_read_input_tokens=1200, output_tokens=42,
            ))
        self.assertEqual(totals.api_calls, 3)
        self.assertEqual(totals.cache_writes, 1)
        self.assertEqual(totals.cache_hits, 2)
        self.assertEqual(totals.cache_misses, 0)
        self.assertEqual(totals.uncached_input_tokens, 15)
        self.assertEqual(totals.cache_creation_tokens, 1200)
        self.assertEqual(totals.cache_read_tokens, 2400)
        self.assertEqual(totals.output_tokens, 124)
        self.assertAlmostEqual(totals.cache_hit_rate, 1.0)

    def test_hit_rate_with_zero_calls_is_zero(self):
        self.assertEqual(analyse.UsageTotals().cache_hit_rate, 0.0)

    def test_hit_rate_with_only_one_call_is_zero(self):
        totals = analyse.UsageTotals()
        totals.add(analyse.UsageRecord(
            row_id="1", model="claude-sonnet-5", input_tokens=300,
            cache_creation_input_tokens=0, cache_read_input_tokens=0, output_tokens=10,
        ))
        self.assertEqual(totals.cache_hit_rate, 0.0)


class AnalyseResponseBehaviourTests(unittest.TestCase):
    """The core behaviour - parses JSON out of the model reply and returns
    a (dict, UsageRecord) pair - must still work after adding batching."""

    def test_returns_parsed_json_and_usage(self):
        client = MagicMock()
        client.messages.create.return_value = _fake_response(ANALYSIS_JSON, {
            "input_tokens": 5, "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 1200, "output_tokens": 40,
        })
        analysis, usage = analyse.analyse_response(client, "resp text", row_id="42")
        self.assertEqual(analysis["summary"], "s")
        self.assertEqual(analysis["themes"], ["privacy"])
        self.assertEqual(analysis["sentiment"], "neutral")
        self.assertEqual(usage.row_id, "42")
        self.assertEqual(usage.cache_status, "hit")

    def test_call_sends_cache_control_and_isolates_response(self):
        client = MagicMock()
        client.messages.create.return_value = _fake_response(ANALYSIS_JSON, {
            "input_tokens": 5, "cache_creation_input_tokens": 1200,
            "cache_read_input_tokens": 0, "output_tokens": 40,
        })
        analyse.analyse_response(client, "unique response body", row_id="1")

        _, kwargs = client.messages.create.call_args
        self.assertEqual(kwargs["system"][0]["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("unique response body", kwargs["system"][0]["text"])
        self.assertEqual(kwargs["messages"][0]["content"], "unique response body")


# ---------------------------------------------------------------------------
# Parsing robustness
# ---------------------------------------------------------------------------

class ParseModelOutputTests(unittest.TestCase):
    def test_plain_json(self):
        text = '{"summary": "s", "themes": ["privacy"], "sentiment": "mixed"}'
        self.assertEqual(
            analyse.parse_model_output(text),
            {"summary": "s", "themes": ["privacy"], "sentiment": "mixed"},
        )

    def test_markdown_fenced_json(self):
        text = '```json\n{"summary": "s", "themes": ["cost"], "sentiment": "opposed"}\n```'
        self.assertEqual(
            analyse.parse_model_output(text),
            {"summary": "s", "themes": ["cost"], "sentiment": "opposed"},
        )

    def test_plain_fence_no_language_tag(self):
        text = '```\n{"summary": "s", "themes": ["trust"], "sentiment": "neutral"}\n```'
        result = analyse.parse_model_output(text)
        self.assertEqual(result["summary"], "s")

    def test_out_of_allowlist_theme_falls_back_instead_of_crashing(self):
        # Mirrors the real row-17 failure: model emits a theme outside the
        # fixed list, sometimes as malformed pseudo-JS.
        text = '{"summary": "s", "themes": ["inclusion"], "sentiment": "neutral"}'
        result = analyse.parse_model_output(text)
        self.assertEqual(result["themes"], ["implementation"])

    def test_invalid_sentiment_falls_back_to_neutral(self):
        text = '{"summary": "s", "themes": ["privacy"], "sentiment": "furious"}'
        result = analyse.parse_model_output(text)
        self.assertEqual(result["sentiment"], "neutral")

    def test_missing_summary_raises_parse_error(self):
        text = '{"themes": ["privacy"], "sentiment": "neutral"}'
        with self.assertRaises(analyse.ParseError):
            analyse.parse_model_output(text)

    def test_garbage_raises_parse_error(self):
        with self.assertRaises(analyse.ParseError):
            analyse.parse_model_output('not json at all, sorry')

    def test_non_dict_json_raises_parse_error(self):
        with self.assertRaises(analyse.ParseError):
            analyse.parse_model_output('["summary", "themes"]')


class SignatureTests(unittest.TestCase):
    def test_same_input_same_signature(self):
        rows = [_row("1", "hello"), _row("2", "world")]
        self.assertEqual(
            analyse.compute_signature(rows, "claude-sonnet-5", 500, "sequential"),
            analyse.compute_signature(rows, "claude-sonnet-5", 500, "sequential"),
        )

    def test_different_text_changes_signature(self):
        rows_a = [_row("1", "hello")]
        rows_b = [_row("1", "goodbye")]
        self.assertNotEqual(
            analyse.compute_signature(rows_a, "claude-sonnet-5", 500, "sequential"),
            analyse.compute_signature(rows_b, "claude-sonnet-5", 500, "sequential"),
        )

    def test_different_model_changes_signature(self):
        rows = [_row("1", "hello")]
        self.assertNotEqual(
            analyse.compute_signature(rows, "claude-sonnet-5", 500, "sequential"),
            analyse.compute_signature(rows, "claude-haiku-4-5", 500, "sequential"),
        )

    def test_different_mode_changes_signature(self):
        # Switching modes must not silently resume another mode's checkpoint.
        rows = [_row("1", "hello")]
        self.assertNotEqual(
            analyse.compute_signature(rows, "claude-sonnet-5", 500, "sequential"),
            analyse.compute_signature(rows, "claude-sonnet-5", 500, "concurrent"),
        )


class CheckpointRoundTripTests(unittest.TestCase):
    def test_save_then_load(self):
        with TemporaryDirectory() as d:
            state_file = Path(d) / "state.json"
            analyse._save_state(state_file, {"batch_id": "abc", "signature": "xyz"})
            loaded = analyse._load_state(state_file)
            self.assertEqual(loaded, {"batch_id": "abc", "signature": "xyz"})

    def test_load_missing_file_returns_none(self):
        with TemporaryDirectory() as d:
            self.assertIsNone(analyse._load_state(Path(d) / "missing.json"))

    def test_load_corrupt_file_returns_none_not_crash(self):
        with TemporaryDirectory() as d:
            state_file = Path(d) / "state.json"
            state_file.write_text("{not valid json")
            self.assertIsNone(analyse._load_state(state_file))

    def test_clear_removes_file(self):
        with TemporaryDirectory() as d:
            state_file = Path(d) / "state.json"
            analyse._save_state(state_file, {"a": 1})
            analyse._clear_state(state_file)
            self.assertFalse(state_file.exists())

    def test_clear_missing_file_is_a_noop(self):
        with TemporaryDirectory() as d:
            analyse._clear_state(Path(d) / "missing.json")  # should not raise


class BuildRequestsTests(unittest.TestCase):
    def test_custom_id_and_cache_control(self):
        rows = [_row("7", "some response")]
        requests = analyse.build_requests(rows, "claude-sonnet-5", 500)
        self.assertEqual(len(requests), 1)
        req = requests[0]
        self.assertEqual(req["custom_id"], "row-7")
        self.assertEqual(req["params"]["model"], "claude-sonnet-5")
        self.assertEqual(req["params"]["messages"][0]["content"], "some response")
        self.assertEqual(req["params"]["system"][0]["cache_control"], {"type": "ephemeral"})


def _fake_content_block(text):
    return SimpleNamespace(type="text", text=text)


def _fake_succeeded_item(custom_id, text, input_tokens=10, output_tokens=5):
    message = SimpleNamespace(
        content=[_fake_content_block(text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )
    result = SimpleNamespace(type="succeeded", message=message)
    return SimpleNamespace(custom_id=custom_id, result=result)


def _fake_errored_item(custom_id, error="rate_limit_error"):
    result = SimpleNamespace(type="errored", error=error)
    return SimpleNamespace(custom_id=custom_id, result=result)


class FakeBatchesClient:
    def __init__(self, items):
        self._items = items

    def results(self, batch_id):
        return iter(self._items)


class FakeClient:
    def __init__(self, items):
        self.messages = SimpleNamespace(batches=FakeBatchesClient(items))


class FetchAndMergeResultsTests(unittest.TestCase):
    def test_preserves_csv_order_regardless_of_stream_order(self):
        rows = [_row("1", "a"), _row("2", "b"), _row("3", "c")]
        rows_by_id = {r["id"]: r for r in rows}
        # Results streamed out of order on purpose.
        items = [
            _fake_succeeded_item("row-3", '{"summary": "s3", "themes": ["cost"], "sentiment": "neutral"}'),
            _fake_succeeded_item("row-1", '{"summary": "s1", "themes": ["cost"], "sentiment": "neutral"}'),
            _fake_succeeded_item("row-2", '{"summary": "s2", "themes": ["cost"], "sentiment": "neutral"}'),
        ]
        client = FakeClient(items)
        results, totals, errors = analyse.fetch_and_merge_results(client, "batch-1", rows_by_id)
        self.assertEqual([r["id"] for r in results], ["1", "2", "3"])
        self.assertEqual(totals.uncached_input_tokens, 30)
        self.assertEqual(totals.output_tokens, 15)
        self.assertEqual(errors, 0)

    def test_errored_result_becomes_sentinel_not_crash(self):
        rows = [_row("1", "a")]
        rows_by_id = {r["id"]: r for r in rows}
        items = [_fake_errored_item("row-1")]
        client = FakeClient(items)
        results, totals, errors = analyse.fetch_and_merge_results(client, "batch-1", rows_by_id)
        self.assertEqual(errors, 1)
        self.assertEqual(results[0]["summary"], "BATCH_ERRORED")
        self.assertEqual(results[0]["sentiment"], "neutral")

    def test_unparseable_succeeded_result_becomes_sentinel_not_crash(self):
        rows = [_row("1", "a")]
        rows_by_id = {r["id"]: r for r in rows}
        items = [_fake_succeeded_item("row-1", "not json at all")]
        client = FakeClient(items)
        results, totals, errors = analyse.fetch_and_merge_results(client, "batch-1", rows_by_id)
        self.assertEqual(errors, 1)
        self.assertEqual(results[0]["summary"], "PARSE_ERROR")
        self.assertIn("parse_error", results[0])


def _fake_message(text, input_tokens=10, output_tokens=5):
    return SimpleNamespace(
        content=[_fake_content_block(text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class FakeSyncClient:
    """Fake for the direct (non-batch) client.messages.create() path."""

    def __init__(self, responder):
        self.messages = SimpleNamespace(create=responder)


class CallSingleSyncTests(unittest.TestCase):
    def test_success(self):
        def responder(**kwargs):
            return _fake_message('{"summary": "s", "themes": ["cost"], "sentiment": "mixed"}',
                                  input_tokens=7, output_tokens=3)
        client = FakeSyncClient(responder)
        merged, usage = analyse.call_single_sync(client, _row("1", "a"), "model", 500)
        self.assertEqual(merged["summary"], "s")
        self.assertEqual((usage.input_tokens, usage.output_tokens), (7, 3))

    def test_api_error_becomes_sentinel_not_crash(self):
        def responder(**kwargs):
            raise RuntimeError("connection reset")
        client = FakeSyncClient(responder)
        merged, usage = analyse.call_single_sync(client, _row("1", "a"), "model", 500)
        self.assertEqual(merged["summary"], "API_ERROR")
        self.assertEqual((usage.input_tokens, usage.output_tokens), (0, 0))
        self.assertIn("connection reset", merged["parse_error"])

    def test_parse_error_becomes_sentinel_not_crash(self):
        def responder(**kwargs):
            return _fake_message("not json at all")
        client = FakeSyncClient(responder)
        merged, usage = analyse.call_single_sync(client, _row("1", "a"), "model", 500)
        self.assertEqual(merged["summary"], "PARSE_ERROR")


class RunSequentialTests(unittest.TestCase):
    def test_processes_rows_and_checkpoints_incrementally(self):
        rows = [_row("1", "a"), _row("2", "b")]

        def responder(**kwargs):
            content = kwargs["messages"][0]["content"]
            return _fake_message(f'{{"summary": "s-{content}", "themes": ["cost"], "sentiment": "neutral"}}')

        client = FakeSyncClient(responder)
        with TemporaryDirectory() as d:
            state_file = Path(d) / "state.json"
            state = {"mode": "sequential", "signature": "sig", "progress": {}}
            totals = analyse.run_sequential(client, rows, "model", 500, state, state_file)
            self.assertEqual(state["progress"]["1"]["summary"], "s-a")
            self.assertEqual(state["progress"]["2"]["summary"], "s-b")
            self.assertEqual(totals.uncached_input_tokens, 20)  # 10 per row
            # Checkpoint was actually written to disk, not just held in memory.
            on_disk = analyse._load_state(state_file)
            self.assertEqual(on_disk["progress"]["1"]["summary"], "s-a")

    def test_resume_skips_already_completed_rows(self):
        rows = [_row("1", "a"), _row("2", "b")]
        calls = []

        def responder(**kwargs):
            content = kwargs["messages"][0]["content"]
            calls.append(content)
            return _fake_message(f'{{"summary": "s-{content}", "themes": ["cost"], "sentiment": "neutral"}}')

        client = FakeSyncClient(responder)
        with TemporaryDirectory() as d:
            state_file = Path(d) / "state.json"
            state = {
                "mode": "sequential", "signature": "sig",
                "progress": {"1": _merge_row_stub("1", "already-done")},
            }
            analyse.run_sequential(client, rows, "model", 500, state, state_file)
            self.assertNotIn("a", calls)  # row 1 was never re-sent
            self.assertIn("b", calls)
            self.assertEqual(state["progress"]["1"]["summary"], "already-done")


class RunConcurrentTests(unittest.TestCase):
    def test_processes_all_rows_concurrently(self):
        rows = [_row(str(i), f"text-{i}") for i in range(1, 6)]

        def responder(**kwargs):
            content = kwargs["messages"][0]["content"]
            return _fake_message(f'{{"summary": "s-{content}", "themes": ["cost"], "sentiment": "neutral"}}')

        client = FakeSyncClient(responder)
        with TemporaryDirectory() as d:
            state_file = Path(d) / "state.json"
            state = {"mode": "concurrent", "signature": "sig", "progress": {}}
            totals = analyse.run_concurrent(client, rows, "model", 500, state, state_file, 3)
            for i in range(1, 6):
                self.assertEqual(state["progress"][str(i)]["summary"], f"s-text-{i}")
            self.assertEqual(totals.uncached_input_tokens, 50)  # 10 tokens * 5 rows


if __name__ == "__main__":
    unittest.main()

# Proves telemetry.py's hooks actually fire, with the right data, at the
# points they were wired into analyse.py - not just that analyse.py's own
# behavior didn't regress (test_analyse.py already covers that). Reuses
# analyse.py's own test doubles rather than redefining them.

import logging

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

import analyse
import telemetry
from test_analyse import (
    FakeBatchesClient,
    FakeClient,
    FakeSyncClient,
    _fake_errored_item,
    _fake_message,
    _fake_succeeded_item,
    _row,
)


def _configured_reader():
    reader = InMemoryMetricReader()
    telemetry.configure_metrics(MeterProvider(metric_readers=[reader]))
    return reader


def _data_points(reader, metric_name):
    data = reader.get_metrics_data()
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == metric_name:
                    return list(metric.data.data_points)
    return []


def test_call_single_sync_success_records_outcome_spend_and_cache_status():
    reader = _configured_reader()

    def responder(**kwargs):
        return _fake_message('{"summary": "s", "themes": ["cost"], "sentiment": "mixed"}',
                              input_tokens=100, output_tokens=50)

    client = FakeSyncClient(responder)
    analyse.call_single_sync(client, _row("1", "some response text"), "claude-sonnet-4-6", 500)

    outcome_points = _data_points(reader, "consultation.rows.total")
    assert {p.attributes["outcome"]: p.value for p in outcome_points} == {"success": 1}

    spend_points = _data_points(reader, "consultation.spend.gbp")
    assert len(spend_points) == 1
    assert spend_points[0].attributes["batch"] is False
    assert spend_points[0].value > 0

    cache_points = _data_points(reader, "consultation.cache.status")
    # No cache_creation/cache_read tokens in this fake response -> "miss".
    assert {p.attributes["status"]: p.value for p in cache_points} == {"miss": 1}

    size_points = _data_points(reader, "consultation.response.bytes")
    assert len(size_points) == 1
    assert size_points[0].count == 1


def test_call_single_sync_parse_error_records_outcome_and_redacted_log(caplog):
    _configured_reader()
    long_bad_output = "not json " * 50

    def responder(**kwargs):
        return _fake_message(long_bad_output)

    client = FakeSyncClient(responder)
    with caplog.at_level(logging.ERROR, logger="consultation_insights"):
        analyse.call_single_sync(client, _row("2", "some response text"), "model", 500)

    error_record = next(r for r in caplog.records if r.message == "row.parse_error")
    assert long_bad_output not in error_record.error
    assert long_bad_output not in error_record.response_snippet


def test_call_single_sync_api_error_records_outcome_and_log(caplog):
    reader = _configured_reader()

    def responder(**kwargs):
        raise RuntimeError("connection reset")

    client = FakeSyncClient(responder)
    with caplog.at_level(logging.ERROR, logger="consultation_insights"):
        analyse.call_single_sync(client, _row("3", "text"), "model", 500)

    outcome_points = _data_points(reader, "consultation.rows.total")
    assert {p.attributes["outcome"]: p.value for p in outcome_points} == {"api_error": 1}

    error_record = next(r for r in caplog.records if r.message == "row.api_error")
    assert error_record.row_id == "3"
    assert "connection reset" in error_record.error

    # No API response was received, so nothing was billed or sized.
    assert _data_points(reader, "consultation.spend.gbp") == []
    assert _data_points(reader, "consultation.response.bytes") == []


def test_fetch_and_merge_results_batch_success_labels_spend_as_batch():
    reader = _configured_reader()
    rows = [_row("1", "a")]
    rows_by_id = {r["id"]: r for r in rows}
    items = [_fake_succeeded_item(
        "row-1", '{"summary": "s", "themes": ["cost"], "sentiment": "neutral"}',
        input_tokens=200, output_tokens=80,
    )]
    client = FakeClient(items)

    analyse.fetch_and_merge_results(client, "batch-1", rows_by_id)

    spend_points = _data_points(reader, "consultation.spend.gbp")
    assert len(spend_points) == 1
    assert spend_points[0].attributes["batch"] is True

    outcome_points = _data_points(reader, "consultation.rows.total")
    assert {p.attributes["outcome"]: p.value for p in outcome_points} == {"success": 1}


def test_fetch_and_merge_results_batch_item_error_records_api_error(caplog):
    reader = _configured_reader()
    rows = [_row("1", "a")]
    rows_by_id = {r["id"]: r for r in rows}
    items = [_fake_errored_item("row-1", error="rate_limit_error")]
    client = FakeClient(items)

    with caplog.at_level(logging.ERROR, logger="consultation_insights"):
        analyse.fetch_and_merge_results(client, "batch-1", rows_by_id)

    outcome_points = _data_points(reader, "consultation.rows.total")
    assert {p.attributes["outcome"]: p.value for p in outcome_points} == {"api_error": 1}

    error_record = next(r for r in caplog.records if r.message == "row.api_error")
    assert error_record.row_id == "1"

    # A batch item that never succeeded was never billed.
    assert _data_points(reader, "consultation.spend.gbp") == []

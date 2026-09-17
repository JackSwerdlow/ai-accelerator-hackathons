import logging

import telemetry
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


def test_redact_snippet_leaves_short_text_untouched():
    assert telemetry._redact_snippet("short text") == "short text"


def test_redact_snippet_truncates_long_text():
    long_text = "x" * 500
    result = telemetry._redact_snippet(long_text, max_len=80)
    assert len(result) < 500
    assert result.startswith("x" * 80)
    assert "500 chars total" in result


def test_redact_snippet_never_returns_full_text_over_limit():
    long_text = "SECRET " * 50
    result = telemetry._redact_snippet(long_text, max_len=20)
    assert long_text not in result


def _configured_reader():
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    telemetry.configure_metrics(provider)
    return reader


def _data_points(reader, metric_name):
    data = reader.get_metrics_data()
    for rm in data.resource_metrics:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name == metric_name:
                    return list(metric.data.data_points)
    return []


def test_record_row_outcome_increments_counter_with_outcome_label():
    reader = _configured_reader()
    telemetry.record_row_outcome("success")
    telemetry.record_row_outcome("success")
    telemetry.record_row_outcome("parse_error")

    points = _data_points(reader, "consultation.rows.total")
    by_outcome = {p.attributes["outcome"]: p.value for p in points}
    assert by_outcome == {"success": 2, "parse_error": 1}


def test_record_spend_returns_and_records_gbp_amount():
    reader = _configured_reader()

    gbp = telemetry.record_spend("claude-sonnet-4-6", input_tokens=1000, output_tokens=1000)

    assert gbp > 0
    points = _data_points(reader, "consultation.spend.gbp")
    assert len(points) == 1
    assert points[0].attributes["model"] == "claude-sonnet-4-6"
    assert points[0].value == gbp


def test_record_spend_prices_cache_and_batch_tokens_and_labels_batch():
    reader = _configured_reader()

    gbp = telemetry.record_spend(
        "claude-sonnet-4-6", input_tokens=1000, output_tokens=1000,
        cache_creation_tokens=500, cache_read_tokens=2000, batch=True,
    )

    # Independently derive the expected cost via the same pricing table
    # analyse.py uses, so this doesn't just re-assert telemetry's own math.
    from spend.pricing import cost_gbp
    expected = cost_gbp("claude-sonnet-4-6", 1000, 1000,
                         cache_creation_tokens=500, cache_read_tokens=2000, batch=True)
    assert gbp == expected

    points = _data_points(reader, "consultation.spend.gbp")
    assert len(points) == 1
    assert points[0].attributes["model"] == "claude-sonnet-4-6"
    assert points[0].attributes["batch"] is True
    assert points[0].value == gbp


def test_record_cache_status_increments_counter_with_status_label():
    reader = _configured_reader()
    telemetry.record_cache_status("hit")
    telemetry.record_cache_status("hit")
    telemetry.record_cache_status("write")
    telemetry.record_cache_status("miss")

    points = _data_points(reader, "consultation.cache.status")
    by_status = {p.attributes["status"]: p.value for p in points}
    assert by_status == {"hit": 2, "write": 1, "miss": 1}


def test_record_response_size_records_histogram_value():
    reader = _configured_reader()
    telemetry.record_response_size(256)

    points = _data_points(reader, "consultation.response.bytes")
    assert len(points) == 1
    assert points[0].sum == 256
    assert points[0].count == 1


def test_record_batch_rows_total_sets_gauge():
    reader = _configured_reader()
    telemetry.record_batch_rows_total(40)

    points = _data_points(reader, "consultation.batch.rows_total")
    assert len(points) == 1
    assert points[0].value == 40


def test_log_batch_started_logs_and_sets_gauge(caplog):
    reader = _configured_reader()
    with caplog.at_level(logging.INFO, logger="consultation_insights"):
        telemetry.log_batch_started("claude-sonnet-4-6", row_count=40)

    assert any(r.message == "batch.started" for r in caplog.records)
    started = next(r for r in caplog.records if r.message == "batch.started")
    assert started.model == "claude-sonnet-4-6"
    assert started.row_count == 40

    points = _data_points(reader, "consultation.batch.rows_total")
    assert points[0].value == 40


def test_log_batch_finished_reports_duration_and_spend(caplog):
    _configured_reader()  # log_batch_started() -> record_batch_rows_total() needs metrics configured
    with caplog.at_level(logging.INFO, logger="consultation_insights"):
        start_time = telemetry.log_batch_started("claude-sonnet-4-6", row_count=3)
        telemetry.log_batch_finished(
            start_time,
            outcomes={"success": 2, "parse_error": 1, "api_error": 0},
            total_spend_gbp=0.0123,
        )

    finished = next(r for r in caplog.records if r.message == "batch.finished")
    assert finished.rows_success == 2
    assert finished.rows_parse_error == 1
    assert finished.rows_api_error == 0
    assert finished.total_spend_gbp == 0.0123
    assert finished.duration_s >= 0


def test_log_parse_error_redacts_full_response_text(caplog):
    long_response = "not json " * 50  # 450 chars, well past REDACT_SNIPPET_LEN
    with caplog.at_level(logging.ERROR, logger="consultation_insights"):
        telemetry.log_parse_error("row-7", long_response, ValueError("bad json"))

    error_record = next(r for r in caplog.records if r.message == "row.parse_error")
    assert error_record.row_id == "row-7"
    assert error_record.response_length == len(long_response)
    assert long_response not in error_record.response_snippet
    assert "bad json" in error_record.error


def test_log_parse_error_redacts_full_text_embedded_in_error_message(caplog):
    """analyse.py's ParseError messages embed the raw model output directly
    in the exception text (e.g. "malformed JSON: ...; raw output: <full
    text>") — str(error) alone can carry the same full consultation-response
    text this function exists to keep out of the telemetry backend. The
    `error` field must be redacted too, not just `raw_response`."""
    raw_output = "not json " * 50  # 450 chars
    error_with_embedded_text = ValueError(f"malformed JSON: bad token; raw output: {raw_output!r}")

    with caplog.at_level(logging.ERROR, logger="consultation_insights"):
        telemetry.log_parse_error("row-8", raw_output, error_with_embedded_text)

    error_record = next(r for r in caplog.records if r.message == "row.parse_error")
    assert raw_output not in error_record.error


def test_log_api_error_records_row_id_and_error(caplog):
    with caplog.at_level(logging.ERROR, logger="consultation_insights"):
        telemetry.log_api_error("row-9", RuntimeError("rate limited"))

    error_record = next(r for r in caplog.records if r.message == "row.api_error")
    assert error_record.row_id == "row-9"
    assert "rate limited" in error_record.error


def test_init_telemetry_never_raises_even_if_instrumentor_fails(monkeypatch):
    from openinference.instrumentation.anthropic import AnthropicInstrumentor

    def _boom(self, **kwargs):
        raise RuntimeError("simulated instrumentor failure")

    monkeypatch.setattr(AnthropicInstrumentor, "instrument", _boom)

    telemetry.init_telemetry()  # must not raise


def test_init_telemetry_configures_metrics_so_recording_works_after():
    telemetry.init_telemetry()
    telemetry.record_row_outcome("success")  # must not raise (instruments exist)


def test_init_telemetry_enables_info_level_logging_without_caplog_help(monkeypatch):
    """Regression test: found by actually running analyse.py against a real
    SigNoz instance and discovering batch.started/batch.finished never
    arrived, while row.parse_error/row.api_error (both ERROR) always did.
    Cause: this module's logger never had its level set, so it deferred to
    the root logger's default (WARNING) and silently dropped INFO records
    before they reached any handler - including the OTel exporter. Every
    other test in this file uses caplog.at_level(logging.INFO, ...), which
    itself lowers the effective level for the test and would never have
    caught this. This test checks the real effective level directly."""
    telemetry.logger.setLevel(logging.NOTSET)  # simulate pre-fix state
    monkeypatch.setattr(telemetry, "_initialized", False)  # force the body to run

    telemetry.init_telemetry()

    assert telemetry.logger.isEnabledFor(logging.INFO)


def test_init_telemetry_hides_llm_input_and_output_in_traces(monkeypatch):
    """Consultation responses (the LLM input) and model completions (the LLM
    output) may contain PII and must never reach trace spans in full — verify
    init_telemetry() passes a TraceConfig with both hidden to the instrumentor."""
    from openinference.instrumentation import TraceConfig
    from openinference.instrumentation.anthropic import AnthropicInstrumentor

    captured_kwargs = {}

    def _capture_instrument(self, **kwargs):
        captured_kwargs.update(kwargs)

    monkeypatch.setattr(AnthropicInstrumentor, "instrument", _capture_instrument)
    # Force init_telemetry()'s body to actually run even though an earlier
    # test in this file already flipped the module's idempotency guard.
    monkeypatch.setattr(telemetry, "_initialized", False)

    telemetry.init_telemetry()

    assert "config" in captured_kwargs
    config = captured_kwargs["config"]
    assert isinstance(config, TraceConfig)
    assert config.hide_inputs is True
    assert config.hide_outputs is True

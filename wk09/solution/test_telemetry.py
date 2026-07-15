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

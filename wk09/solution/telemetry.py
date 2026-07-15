"""OpenTelemetry wiring for analyse.py.

Traces come from AnthropicInstrumentor (auto-instrumented, zero manual span code).
Metrics and logs below are hand-written for the things auto-instrumentation can't
know: GBP spend, row outcome, response size, batch progress.
"""

import logging

SERVICE_NAME = "consultation-insights"
REDACT_SNIPPET_LEN = 80

logger = logging.getLogger("consultation_insights")


def _redact_snippet(text, max_len=REDACT_SNIPPET_LEN):
    """Truncate text for safe logging. Never returns the full string once it
    exceeds max_len — used so free-text consultation responses (which may
    contain PII despite being "public" input) never reach the telemetry
    backend in full."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"...[{len(text)} chars total]"


from spend.pricing import cost_gbp

_spend_counter = None
_rows_counter = None
_response_size_histogram = None
_batch_rows_gauge = None


def configure_metrics(meter_provider):
    """Bind this module's metric instruments to the given MeterProvider.
    Called by init_telemetry() (Task 4) with a real, OTLP-exporting provider;
    called directly by tests with an in-memory provider — this seam is what
    makes the metrics testable without a running SigNoz collector."""
    global _spend_counter, _rows_counter, _response_size_histogram, _batch_rows_gauge
    meter = meter_provider.get_meter(SERVICE_NAME)
    _spend_counter = meter.create_counter(
        "consultation.spend.gbp", unit="GBP", description="Anthropic API spend in GBP"
    )
    _rows_counter = meter.create_counter(
        "consultation.rows.total", unit="1",
        description="Consultation rows processed, by outcome",
    )
    _response_size_histogram = meter.create_histogram(
        "consultation.response.bytes", unit="By",
        description="Size of raw model response payloads",
    )
    _batch_rows_gauge = meter.create_gauge(
        "consultation.batch.rows_total", unit="1",
        description="Total rows in the current batch run",
    )


def record_row_outcome(outcome):
    """outcome: one of 'success', 'parse_error', 'api_error'."""
    _rows_counter.add(1, {"outcome": outcome})


def record_spend(model, input_tokens, output_tokens):
    """Computes GBP cost via spend.pricing.cost_gbp (the existing pricing table
    used by solution/spend/) and records it. Returns the GBP amount so callers
    can accumulate a run total without re-deriving it."""
    gbp = cost_gbp(model, input_tokens, output_tokens)
    _spend_counter.add(gbp, {"model": model})
    return gbp


def record_response_size(num_bytes):
    _response_size_histogram.record(num_bytes)


def record_batch_rows_total(row_count):
    _batch_rows_gauge.set(row_count)

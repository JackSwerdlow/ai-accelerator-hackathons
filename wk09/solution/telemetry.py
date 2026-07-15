"""OpenTelemetry wiring for analyse.py.

Traces come from AnthropicInstrumentor (auto-instrumented, zero manual span code).
Metrics and logs below are hand-written for the things auto-instrumentation can't
know: GBP spend, row outcome, response size, batch progress.
"""

import logging
import time

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


def log_batch_started(model, row_count):
    logger.info("batch.started", extra={"model": model, "row_count": row_count})
    record_batch_rows_total(row_count)
    return time.monotonic()


def log_batch_finished(start_time, outcomes, total_spend_gbp):
    duration_s = time.monotonic() - start_time
    logger.info(
        "batch.finished",
        extra={
            "duration_s": round(duration_s, 2),
            "total_spend_gbp": round(total_spend_gbp, 4),
            "rows_success": outcomes.get("success", 0),
            "rows_parse_error": outcomes.get("parse_error", 0),
            "rows_api_error": outcomes.get("api_error", 0),
        },
    )


def log_parse_error(row_id, raw_response, error):
    logger.error(
        "row.parse_error",
        extra={
            "row_id": row_id,
            "response_length": len(raw_response),
            "response_snippet": _redact_snippet(raw_response),
            "error": str(error),
        },
    )


def log_api_error(row_id, error):
    logger.error("row.api_error", extra={"row_id": row_id, "error": str(error)})


from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_telemetry():
    """Wire up real OTLP-exporting providers and AnthropicInstrumentor. Call
    once, before constructing the Anthropic client. Never raises: a telemetry
    setup failure must not take down the actual batch run, so every step is
    inside one try/except that logs and swallows."""
    try:
        resource = Resource.create({"service.name": SERVICE_NAME})

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)

        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter())],
        )
        metrics.set_meter_provider(meter_provider)
        configure_metrics(meter_provider)

        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(OTLPLogExporter())
        )
        set_logger_provider(logger_provider)
        logging.getLogger().addHandler(LoggingHandler(logger_provider=logger_provider))

        from openinference.instrumentation.anthropic import AnthropicInstrumentor

        AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
    except Exception:
        logger.exception("telemetry.init_failed")

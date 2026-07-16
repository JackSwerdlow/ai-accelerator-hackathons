"""OpenTelemetry wiring for analyse.py.

Traces come from AnthropicInstrumentor (auto-instrumented, zero manual span code).
Metrics and logs below are hand-written for the things auto-instrumentation can't
know: GBP spend, row outcome, response size, batch progress.
"""

import logging
import socket
import time

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

from spend.pricing import cost_gbp

SERVICE_NAME = "consultation-insights"
REDACT_SNIPPET_LEN = 80

logger = logging.getLogger("consultation_insights")

_spend_counter = None
_rows_counter = None
_response_size_histogram = None
_batch_rows_gauge = None
_cache_status_counter = None
_initialized = False


def _redact_snippet(text, max_len=REDACT_SNIPPET_LEN):
    """Truncate text for safe logging. Never returns the full string once it
    exceeds max_len — used so free-text consultation responses (which may
    contain PII despite being "public" input) never reach the telemetry
    backend in full."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"...[{len(text)} chars total]"


def configure_metrics(meter_provider):
    """Bind this module's metric instruments to the given MeterProvider.
    Called by init_telemetry() (Task 4) with a real, OTLP-exporting provider;
    called directly by tests with an in-memory provider — this seam is what
    makes the metrics testable without a running SigNoz collector."""
    global _spend_counter, _rows_counter, _response_size_histogram, _batch_rows_gauge
    global _cache_status_counter
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
    _cache_status_counter = meter.create_counter(
        "consultation.cache.status", unit="1",
        description="Prompt-cache outcome per API call (hit/write/miss)",
    )


def record_row_outcome(outcome):
    """outcome: one of 'success', 'parse_error', 'api_error'."""
    _rows_counter.add(1, {"outcome": outcome})


def record_spend(model, input_tokens, output_tokens, cache_creation_tokens=0,
                  cache_read_tokens=0, batch=False):
    """Computes GBP cost via spend.pricing.cost_gbp (the existing pricing table
    used by solution/spend/) and records it. Returns the GBP amount so callers
    can accumulate a run total without re-deriving it. cache_creation_tokens/
    cache_read_tokens/batch are passed straight through to cost_gbp so prompt-
    cache writes/reads and the Batch API's 50% discount are priced correctly;
    `batch` is also recorded as a metric label so batch vs standard spend are
    distinguishable on a dashboard."""
    gbp = cost_gbp(model, input_tokens, output_tokens,
                    cache_creation_tokens=cache_creation_tokens,
                    cache_read_tokens=cache_read_tokens, batch=batch)
    _spend_counter.add(gbp, {"model": model, "batch": batch})
    return gbp


def record_cache_status(status):
    """status: one of 'hit', 'write', 'miss' (see analyse.py's UsageRecord.cache_status)."""
    _cache_status_counter.add(1, {"status": status})


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
    # error is redacted too, not just raw_response: analyse.py's ParseError
    # messages embed the raw model output in the exception text itself
    # (e.g. "malformed JSON: ...; raw output: <full text>"), so str(error)
    # can carry the same full consultation-response text this function
    # exists to keep out of the telemetry backend.
    logger.error(
        "row.parse_error",
        extra={
            "row_id": row_id,
            "response_length": len(raw_response),
            "response_snippet": _redact_snippet(raw_response),
            "error": _redact_snippet(str(error)),
        },
    )


def log_api_error(row_id, error):
    logger.error("row.api_error", extra={"row_id": row_id, "error": _redact_snippet(str(error))})


def init_telemetry():
    """Wire up real OTLP-exporting providers and AnthropicInstrumentor. Call
    once, before constructing the Anthropic client. Never raises: a telemetry
    setup failure must not take down the actual batch run, so every step is
    inside one try/except that logs and swallows.

    Idempotent: only the first call in a process actually wires anything up.
    Without this guard, calling init_telemetry() more than once (as can happen
    across tests or re-entrant setup) would keep stacking duplicate root-logger
    handlers and re-set the global tracer/meter/logger providers.
    """
    global _initialized
    if _initialized:
        return
    try:
        # service.instance.id is deliberately pinned to the hostname, not left
        # for OTel to auto-generate a random UUID per process. analyse.py is a
        # batch CLI invoked repeatedly over time (cron, manual re-runs) - the
        # dashboard needs those runs to land on one continuous, queryable time
        # series per host, not fragment into a new single-point series every
        # invocation (which is exactly what happened before this fix: found by
        # importing the dashboard for real and seeing every rate/increase
        # panel come back empty, traced to >1000 distinct service.instance.id
        # values for these metrics in this shared SigNoz instance).
        resource = Resource.create({
            "service.name": SERVICE_NAME,
            "service.instance.id": socket.gethostname(),
        })

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
        # Without this, this logger's effective level defers to the root
        # logger's default (WARNING), so log_batch_started/log_batch_finished
        # (both INFO) get dropped before reaching any handler - never even
        # exported to SigNoz, let alone printed. Only the ERROR-level
        # log_parse_error/log_api_error worked before this fix. Tests didn't
        # catch this because caplog.at_level(logging.INFO, ...) temporarily
        # lowers the level for the duration of the test, masking the gap.
        logger.setLevel(logging.INFO)

        from openinference.instrumentation import TraceConfig
        from openinference.instrumentation.anthropic import AnthropicInstrumentor

        AnthropicInstrumentor().instrument(
            tracer_provider=tracer_provider,
            # Consultation responses (the LLM input) and model completions (the
            # LLM output) may contain PII — never let full prompt/completion
            # text reach the shared telemetry backend, matching the redaction
            # already applied to logs above.
            config=TraceConfig(hide_inputs=True, hide_outputs=True),
        )
    except Exception:
        logger.exception("telemetry.init_failed")
    finally:
        _initialized = True

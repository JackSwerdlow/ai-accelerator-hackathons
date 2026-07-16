import pytest
from opentelemetry.sdk.metrics import MeterProvider

import telemetry


@pytest.fixture(autouse=True)
def _never_export_telemetry_for_real(monkeypatch):
    """A few tests (test_init_telemetry_*) call the real telemetry.init_telemetry(),
    which constructs OTLPSpanExporter()/OTLPMetricExporter()/OTLPLogExporter() with
    no arguments - and those default to localhost:4317 with NO endpoint required.
    On a machine that happens to have anything listening on that port (as this one
    does, for local SigNoz development), every test run silently succeeds in
    exporting real telemetry to it. Found this by importing the SigNoz dashboard
    for real and discovering 1000+ distinct service.instance.id values had
    accumulated for these metrics - almost entirely test-run noise, not real usage.
    Pin the OTLP endpoint to a port nothing will ever be listening on so tests are
    hermetic regardless of what's running on the host; export failures are async
    and silent (BatchSpanProcessor/PeriodicExportingMetricReader/
    BatchLogRecordProcessor all swallow them), so this doesn't break any test."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:1")


@pytest.fixture(autouse=True)
def _configure_telemetry_metrics():
    """analyse.py calls telemetry.record_*() functions that need the module's
    metric instruments bound to a MeterProvider first (see
    telemetry.configure_metrics). Applied test-suite-wide so analyse.py's
    existing tests don't need to know telemetry.py exists at all — without
    this, any test that exercises analyse_response/call_single_sync/
    fetch_and_merge_results would hit AttributeError on the still-None
    instruments. Tests that need to inspect recorded values (test_telemetry.py)
    call telemetry.configure_metrics() again themselves with their own
    InMemoryMetricReader, which simply rebinds the instruments to that reader.
    """
    telemetry.configure_metrics(MeterProvider())

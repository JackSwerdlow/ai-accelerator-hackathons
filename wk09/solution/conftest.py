import pytest
from opentelemetry.sdk.metrics import MeterProvider

import telemetry


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

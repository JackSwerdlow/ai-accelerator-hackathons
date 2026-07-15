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

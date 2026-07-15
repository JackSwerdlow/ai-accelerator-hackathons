# SigNoz Observability for analyse.py — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Instrument `wk09/solution/analyse.py` with OpenTelemetry (traces, metrics, logs)
so its Anthropic API usage — calls, spend, latency, row outcomes, response size — is
visible in a self-hosted SigNoz instance, per the design in
`wk09/plans/signoz-observability-design-agent-tom.md`.

**Architecture:** Swap `langchain_anthropic.ChatAnthropic` for the raw `anthropic.Anthropic`
SDK client, auto-instrument it with `openinference-instrumentation-anthropic`'s
`AnthropicInstrumentor` (free trace spans with model/token/latency attributes), and
hand-write four OTel metrics plus two structured log events for what auto-instrumentation
can't know (£ spend, row outcome, response size, batch progress). Export all three
signals via OTLP/gRPC to `localhost:4317` (self-hosted SigNoz, no ingestion key).

**Tech Stack:** Python, `anthropic` SDK 0.109.2, `opentelemetry-api`/`sdk`/`exporter-otlp`
1.38.0, `openinference-instrumentation-anthropic`, `pytest` 8.3.4 (all confirmed
available/installed in this environment during planning).

## Global Constraints

- All work happens in `wk09/solution/`; `wk09/starter/` and `wk09/context/` are
  read-only (repo root `CLAUDE.md`, `wk09/CLAUDE.md`).
- Confirm current library syntax via Context7 MCP before writing library-specific code
  (`wk09/CLAUDE.md`) — this plan's OTel/Anthropic SDK code was verified against the
  actually-installed package versions in this environment (see each task's "Verified
  against" note) rather than from memory alone.
- Run the type checker, tests, and linter before calling any task done (`wk09/CLAUDE.md`).
- No full consultation `response_text` (free-text public input, not guaranteed PII-free)
  may appear in any metric label or log attribute — truncate/redact per
  `_redact_snippet()` in Task 1 (design doc, "PII/redaction rule").
- Self-hosted SigNoz only: OTLP/gRPC to `http://localhost:4317`, no ingestion-key
  header (design doc, "Architecture").
- Out of scope, do not implement as part of this plan: retries/checkpoints/resume,
  the Anthropic Batch API workflow, changes to `viewer.py` or `solution/spend/`,
  alerting rules, a vendored `docker-compose.yaml` (design doc, "Explicitly out of
  scope").
- Commit messages: `[Agent-Tom] <summary>` with a body explaining what changed and why
  (repo root `CLAUDE.md`). Stage only the files each task touches.
- Add a `solution/AI_LOG.md` entry only for tasks that require substantive
  iteration/correction, not one-shot successes (`wk09/CLAUDE.md`).

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `wk09/solution/requirements.txt` | modify | dependency list |
| `wk09/solution/telemetry.py` | create | all OTel wiring + emit functions; the only file that imports `opentelemetry.*` or `openinference.*` |
| `wk09/solution/test_telemetry.py` | create | unit tests for `telemetry.py`, using `InMemoryMetricReader` and `caplog` — no network, no real SigNoz needed |
| `wk09/solution/analyse.py` | modify | swap SDK, call into `telemetry.py`, per-row error handling |
| `wk09/solution/test_analyse.py` | create | unit tests for `analyse.py`'s row-processing logic, using a fake Anthropic client — no network |
| `wk09/solution/OBSERVABILITY.md` | create | one-time SigNoz setup + manual verification checklist |

---

### Task 1: `telemetry.py` — redaction helper + dependencies

**Files:**
- Modify: `wk09/solution/requirements.txt`
- Create: `wk09/solution/telemetry.py`
- Test: `wk09/solution/test_telemetry.py`

**Interfaces:**
- Produces: `telemetry._redact_snippet(text: str, max_len: int = 80) -> str`

- [ ] **Step 1: Update `requirements.txt`**

Replace the full file contents of `wk09/solution/requirements.txt` with:

```
flask
anthropic
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp
openinference-instrumentation-anthropic
pytest
pandas
matplotlib
streamlit
plotly
```

(`langchain-anthropic` is removed — Task 5 swaps `analyse.py` off it. `flask`,
`pandas`, `matplotlib`, `streamlit`, `plotly` are unchanged, used by `viewer.py` and
`solution/spend/`, which are out of scope.)

- [ ] **Step 2: Install dependencies**

Run: `cd wk09/solution && pip install -r requirements.txt`
Expected: installs `openinference-instrumentation-anthropic` (the only package not
already present); everything else is already satisfied in this environment.

- [ ] **Step 3: Write the failing test**

Create `wk09/solution/test_telemetry.py`:

```python
import telemetry


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
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: FAIL (or ERROR) — `telemetry` module doesn't exist yet / has no
`_redact_snippet`.

- [ ] **Step 5: Create `telemetry.py` with the redaction helper**

Create `wk09/solution/telemetry.py`:

```python
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
cd wk09/solution
git add requirements.txt telemetry.py test_telemetry.py
git commit -m "[Agent-Tom] Add telemetry module with redaction helper

- requirements.txt: swap langchain-anthropic for anthropic + opentelemetry
  packages + openinference-instrumentation-anthropic + pytest
- telemetry.py: redaction helper so free-text consultation responses never
  reach the telemetry backend in full
- test_telemetry.py: unit tests for the redaction helper"
```

---

### Task 2: `telemetry.py` — metrics (spend, row outcome, response size, batch size)

**Files:**
- Modify: `wk09/solution/telemetry.py`
- Test: `wk09/solution/test_telemetry.py`

**Interfaces:**
- Consumes: `spend.pricing.cost_gbp(model: str, input_tokens: int, output_tokens: int) -> float` (existing, `wk09/solution/spend/pricing.py`)
- Produces:
  - `telemetry.configure_metrics(meter_provider) -> None`
  - `telemetry.record_row_outcome(outcome: str) -> None`
  - `telemetry.record_spend(model: str, input_tokens: int, output_tokens: int) -> float`
  - `telemetry.record_response_size(num_bytes: int) -> None`
  - `telemetry.record_batch_rows_total(row_count: int) -> None`

**Verified against installed `opentelemetry-sdk` 1.38.0:** `MeterProvider.get_meter(name)`
takes a positional name; `meter.create_counter(name, unit=..., description=...)`,
`meter.create_histogram(...)`, and `meter.create_gauge(...)` (synchronous, settable via
`.set(value, attributes)`) all confirmed working with `InMemoryMetricReader` —
`reader.get_metrics_data().resource_metrics[0].scope_metrics[0].metrics[0]` exposes
`.name` and `.data.data_points` (each with `.attributes` and `.value`).

- [ ] **Step 1: Write the failing tests**

Append to `wk09/solution/test_telemetry.py`:

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

import telemetry


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: the 4 new tests FAIL with `AttributeError: module 'telemetry' has no
attribute 'configure_metrics'` (or similar) — the 3 Task 1 tests still PASS.

- [ ] **Step 3: Implement the metrics layer**

Append to `wk09/solution/telemetry.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
cd wk09/solution
git add telemetry.py test_telemetry.py
git commit -m "[Agent-Tom] Add spend/row-outcome/response-size/batch-size metrics

- telemetry.py: configure_metrics() binds instruments to a MeterProvider
  (real or in-memory, for testability); record_spend reuses
  spend/pricing.py's cost_gbp() rather than duplicating the pricing table
- test_telemetry.py: verify each metric via InMemoryMetricReader, no
  network or running SigNoz instance needed"
```

---

### Task 3: `telemetry.py` — structured logs (batch start/finish, row errors)

**Files:**
- Modify: `wk09/solution/telemetry.py`
- Test: `wk09/solution/test_telemetry.py`

**Interfaces:**
- Consumes: `telemetry._redact_snippet` (Task 1), `telemetry.record_batch_rows_total` (Task 2)
- Produces:
  - `telemetry.log_batch_started(model: str, row_count: int) -> float` (returns a `time.monotonic()` start timestamp)
  - `telemetry.log_batch_finished(start_time: float, outcomes: dict, total_spend_gbp: float) -> None` (`outcomes` has keys `"success"`, `"parse_error"`, `"api_error"`)
  - `telemetry.log_parse_error(row_id: str, raw_response: str, error: Exception) -> None`
  - `telemetry.log_api_error(row_id: str, error: Exception) -> None`

- [ ] **Step 1: Write the failing tests**

Append to `wk09/solution/test_telemetry.py`:

```python
import logging

import telemetry


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


def test_log_api_error_records_row_id_and_error(caplog):
    with caplog.at_level(logging.ERROR, logger="consultation_insights"):
        telemetry.log_api_error("row-9", RuntimeError("rate limited"))

    error_record = next(r for r in caplog.records if r.message == "row.api_error")
    assert error_record.row_id == "row-9"
    assert "rate limited" in error_record.error
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: the 4 new tests FAIL with `AttributeError: module 'telemetry' has no
attribute 'log_batch_started'` (or similar) — all 8 prior tests still PASS.

- [ ] **Step 3: Implement the logging layer**

Append to `wk09/solution/telemetry.py`:

```python
import time


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
cd wk09/solution
git add telemetry.py test_telemetry.py
git commit -m "[Agent-Tom] Add batch start/finish and row-error structured logs

- telemetry.py: log_batch_started/finished give a single record of whether
  a run completed and what it cost; log_parse_error/log_api_error turn the
  known 'crash on bad JSON' defect into a searchable event instead of a
  silent process death, without logging full response text
- test_telemetry.py: verify structured attributes via caplog, including
  that a long response's full text never appears in the log record"
```

---

### Task 4: `telemetry.py` — `init_telemetry()` (real OTLP export + AnthropicInstrumentor)

**Files:**
- Modify: `wk09/solution/telemetry.py`
- Test: `wk09/solution/test_telemetry.py`

**Interfaces:**
- Consumes: `telemetry.configure_metrics` (Task 2)
- Produces: `telemetry.init_telemetry() -> None`

**Verified against installed packages in this environment:**
- `opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter`,
  `...metric_exporter.OTLPMetricExporter`, and
  `...proto.grpc._log_exporter.OTLPLogExporter` all confirmed importable.
- `OTLPSpanExporter()` with no arguments defaults to endpoint `localhost:4317` (no env
  vars required for local self-hosted use; `OTEL_EXPORTER_OTLP_ENDPOINT` /
  `OTEL_EXPORTER_OTLP_INSECURE` still override it per standard OTel env var behavior —
  documented in `OBSERVABILITY.md`, Task 7).
- `openinference-instrumentation-anthropic` was not yet installed when this plan was
  written; Task 1 added it to `requirements.txt`. Its documented usage (SigNoz docs,
  `anthropic-monitoring` page) is `from openinference.instrumentation.anthropic import
  AnthropicInstrumentor` then `AnthropicInstrumentor().instrument(tracer_provider=...)`.

- [ ] **Step 1: Write the failing test**

Append to `wk09/solution/test_telemetry.py`:

```python
def test_init_telemetry_never_raises_even_if_instrumentor_fails(monkeypatch):
    from openinference.instrumentation.anthropic import AnthropicInstrumentor

    def _boom(self, **kwargs):
        raise RuntimeError("simulated instrumentor failure")

    monkeypatch.setattr(AnthropicInstrumentor, "instrument", _boom)

    telemetry.init_telemetry()  # must not raise


def test_init_telemetry_configures_metrics_so_recording_works_after():
    telemetry.init_telemetry()
    telemetry.record_row_outcome("success")  # must not raise (instruments exist)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: the 2 new tests FAIL — `telemetry` has no attribute `init_telemetry` — all
12 prior tests still PASS.

- [ ] **Step 3: Implement `init_telemetry()`**

Append to `wk09/solution/telemetry.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd wk09/solution && python -m pytest test_telemetry.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
cd wk09/solution
git add telemetry.py test_telemetry.py
git commit -m "[Agent-Tom] Add init_telemetry(): OTLP export + AnthropicInstrumentor

- telemetry.py: init_telemetry() wires TracerProvider/MeterProvider/
  LoggerProvider to OTLP/gRPC (localhost:4317 by default, self-hosted, no
  ingestion key) and auto-instruments the Anthropic SDK client. Wrapped in
  try/except so a telemetry setup failure can never crash the actual batch
  run over 20,000 rows
- test_telemetry.py: verify init_telemetry() survives an instrumentor
  failure and leaves metrics usable afterward"
```

---

### Task 5: `analyse.py` — swap to raw Anthropic SDK, per-row error handling

**Files:**
- Modify: `wk09/solution/analyse.py`
- Test: `wk09/solution/test_analyse.py`

**Interfaces:**
- Consumes: `telemetry.record_row_outcome`, `telemetry.record_spend`,
  `telemetry.record_response_size`, `telemetry.log_parse_error`,
  `telemetry.log_api_error` (all from Tasks 2–3); also
  `telemetry.configure_metrics` (Task 2) in the test file's `autouse` fixture, since
  `analyse_response`'s metric calls need instruments bound to a `MeterProvider`
  before they're called — without it they're still `None` from module load.
- Produces:
  - `analyse.make_client() -> anthropic.Anthropic`
  - `analyse.analyse_response(client, row_id: str, text: str) -> tuple[str, dict | None, float]`
    — returns `(outcome, analysis, spend_gbp)` where `outcome` is `"success"` /
    `"parse_error"` / `"api_error"`, `analysis` is the parsed dict on success else
    `None`, and `spend_gbp` is `0.0` when the API call itself failed. **Never raises**
    — API and JSON errors are caught, recorded via `telemetry`, and returned as a
    failed outcome so the caller can skip the row and continue.

**Verified against installed `anthropic` SDK 0.109.2:**
- `client.messages.create(model=..., max_tokens=..., messages=[{"role": "user",
  "content": ...}])` returns a `Message` whose `.content` is a list of blocks (use
  `.content[0].text` for the text, confirmed via `TextBlock.model_fields`) and whose
  `.usage` has `.input_tokens` / `.output_tokens` (confirmed via `Usage.model_fields`).
  This differs from `langchain_anthropic`'s `response.content`, which was already a
  plain string — the reason `json.loads(response.content)` in the original code needs
  to become `json.loads(message.content[0].text)`.
- `anthropic.AnthropicError` is the SDK's root exception (confirmed:
  `anthropic.AnthropicError('boom')` constructs with just a message, unlike
  `anthropic.APIError` which requires an `httpx.Request`) — caught here as the
  broadest reasonable "the API call itself failed" signal, covering both connection
  and API-level errors.

- [ ] **Step 1: Write the failing tests**

Create `wk09/solution/test_analyse.py`:

```python
from types import SimpleNamespace

import anthropic
import pytest
from opentelemetry.sdk.metrics import MeterProvider

import analyse
import telemetry


@pytest.fixture(autouse=True)
def _configure_telemetry_metrics():
    """analyse_response() calls telemetry.record_*() functions that need the
    module's metric instruments bound to a MeterProvider first (Task 2's
    configure_metrics) — without this, they're still None from telemetry.py's
    module load and every call raises AttributeError."""
    telemetry.configure_metrics(MeterProvider())


class FakeMessages:
    def __init__(self, message=None, error=None):
        self._message = message
        self._error = error

    def create(self, **kwargs):
        if self._error is not None:
            raise self._error
        return self._message


class FakeClient:
    def __init__(self, message=None, error=None):
        self.messages = FakeMessages(message=message, error=error)


def _fake_message(text, input_tokens=10, output_tokens=20):
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def test_analyse_response_success_returns_parsed_analysis():
    message = _fake_message(
        '{"summary": "neutral", "themes": ["privacy"], "sentiment": "mixed"}'
    )
    client = FakeClient(message=message)

    outcome, analysis, spend_gbp = analyse.analyse_response(client, "row-1", "some text")

    assert outcome == "success"
    assert analysis == {
        "summary": "neutral",
        "themes": ["privacy"],
        "sentiment": "mixed",
    }
    assert spend_gbp > 0


def test_analyse_response_bad_json_returns_parse_error_not_raise():
    message = _fake_message("not valid json at all")
    client = FakeClient(message=message)

    outcome, analysis, spend_gbp = analyse.analyse_response(client, "row-2", "some text")

    assert outcome == "parse_error"
    assert analysis is None
    assert spend_gbp > 0  # tokens were still spent on this call


def test_analyse_response_api_error_returns_api_error_not_raise():
    client = FakeClient(error=anthropic.AnthropicError("rate limited"))

    outcome, analysis, spend_gbp = analyse.analyse_response(client, "row-3", "some text")

    assert outcome == "api_error"
    assert analysis is None
    assert spend_gbp == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd wk09/solution && python -m pytest test_analyse.py -v`
Expected: FAIL — `analyse.analyse_response` either doesn't exist yet with this
signature, or importing `analyse` fails because it still builds a `ChatAnthropic`
client at import time.

- [ ] **Step 3: Rewrite `analyse.py`**

Replace the full contents of `wk09/solution/analyse.py` with:

```python
# Consultation Insights - batch analyser
# Analyses consultation responses one at a time and saves the results.

import csv
import json
import os

import anthropic

import telemetry

MODEL = "claude-sonnet-5"

# Full instructions sent with every single response - keeps each call
# self-contained so there's no state to worry about.
INSTRUCTIONS = """You are analysing responses to the UK government consultation
'Digital Identity in Public Services: Call for Views' run by the Department for
Science, Innovation and Technology.

The consultation asked the public and organisations for views on introducing
a certified, reusable digital identity for accessing public services, including
questions on privacy, inclusion, security, business impact, and governance.

For the consultation response below, produce a JSON object with exactly these
fields:
- "summary": a one-sentence neutral summary of the response
- "themes": a list of 1-3 themes from this fixed list ONLY:
  ["privacy", "digital exclusion", "security", "business efficiency",
   "accessibility", "governance", "fraud reduction", "cost", "trust",
   "implementation"]
- "sentiment": one of "supportive", "opposed", "mixed", "neutral"

Respond with ONLY the JSON object, no other text.

RESPONSE TO ANALYSE:
"""


def make_client():
    return anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", "PASTE-YOUR-KEY-HERE")
    )


def analyse_response(client, row_id, text):
    """Analyse one consultation response. Returns (outcome, analysis, spend_gbp):
      - outcome: "success" | "parse_error" | "api_error"
      - analysis: the parsed dict on success, else None
      - spend_gbp: cost of this call in GBP, 0.0 if the API call itself failed
    Never raises: API and JSON-parse failures are caught, recorded via
    telemetry (metric + log), and returned as a failed outcome so the caller
    can skip this row and continue with the rest of the batch.
    """
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": INSTRUCTIONS + text}],
        )
    except anthropic.AnthropicError as error:
        telemetry.record_row_outcome("api_error")
        telemetry.log_api_error(row_id, error)
        return "api_error", None, 0.0

    raw_text = message.content[0].text
    telemetry.record_response_size(len(raw_text.encode("utf-8")))
    spend_gbp = telemetry.record_spend(
        MODEL, message.usage.input_tokens, message.usage.output_tokens
    )

    try:
        analysis = json.loads(raw_text)
    except json.JSONDecodeError as error:
        telemetry.record_row_outcome("parse_error")
        telemetry.log_parse_error(row_id, raw_text, error)
        return "parse_error", None, spend_gbp

    telemetry.record_row_outcome("success")
    return "success", analysis, spend_gbp


def main():
    telemetry.init_telemetry()

    with open("../data/responses_sample.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Analysing {len(rows)} responses...")
    client = make_client()
    start_time = telemetry.log_batch_started(MODEL, len(rows))

    results = []
    outcomes = {"success": 0, "parse_error": 0, "api_error": 0}
    total_spend_gbp = 0.0

    for i, row in enumerate(rows, start=1):
        outcome, analysis, spend_gbp = analyse_response(
            client, row["id"], row["response_text"]
        )
        outcomes[outcome] += 1
        total_spend_gbp += spend_gbp
        if analysis is not None:
            results.append(
                {
                    "id": row["id"],
                    "respondent_type": row["respondent_type"],
                    "response_text": row["response_text"],
                    **analysis,
                }
            )
        print(f"  [{i}/{len(rows)}] {outcome}")

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    telemetry.log_batch_finished(start_time, outcomes, total_spend_gbp)
    print(
        f"Saved results.json ({outcomes['success']} succeeded, "
        f"{outcomes['parse_error']} parse errors, {outcomes['api_error']} API "
        f"errors, £{total_spend_gbp:.4f} spent)"
    )


if __name__ == "__main__":
    main()
```

Note what changed from the original and why: `ChatAnthropic` → `anthropic.Anthropic`
(design decision, enables `AnthropicInstrumentor` and keeps the Batch API reachable
later); client construction moved out of module scope into `make_client()`, called
from `main()` — a minimal, necessary change so `analyse.py` is importable (and
`analyse_response` testable with a fake client) without a real `ANTHROPIC_API_KEY` set,
not a resilience feature. Rows that fail are no longer written to `results.json` (there
is no valid analysis for them) but are still counted and logged — this is "continue
past one bad row within a single run," not the checkpoint/resume/retry logic that
Task-plan Global Constraints mark out of scope.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd wk09/solution && python -m pytest test_analyse.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
cd wk09/solution
git add analyse.py test_analyse.py
git commit -m "[Agent-Tom] Swap analyse.py to raw anthropic SDK with telemetry hooks

- analyse.py: langchain_anthropic.ChatAnthropic -> anthropic.Anthropic (raw
  SDK), so AnthropicInstrumentor can auto-trace calls and the Batch API
  stays reachable later without re-instrumenting; analyse_response() now
  catches API and JSON-parse failures instead of crashing the whole run,
  recording each via telemetry.py and returning a failed outcome so the
  caller skips that row and continues
- test_analyse.py: cover success / bad-JSON / API-error outcomes with a
  fake client, no network calls"
```

---

### Task 6: `analyse.py` — end-to-end row-loop integration test

**Files:**
- Modify: `wk09/solution/test_analyse.py`

**Interfaces:**
- Consumes: `analyse.analyse_response` (Task 5)

This task verifies the loop in `main()` handles a mix of outcomes correctly by
exercising the same per-row logic across a small batch, without needing to touch
`main()`'s file I/O (CSV/`results.json` reading and writing is a thin, already-obvious
wrapper around `analyse_response`, per YAGNI — the interesting logic under test is
"a mix of outcomes accumulates correctly," which this test isolates directly).

- [ ] **Step 1: Write the failing test**

Append to `wk09/solution/test_analyse.py`:

```python
def test_mixed_batch_accumulates_outcomes_and_spend_without_stopping():
    good_message = _fake_message('{"summary": "s", "themes": ["cost"], "sentiment": "mixed"}')
    bad_json_message = _fake_message("not json")

    rows = [
        ("row-1", FakeClient(message=good_message)),
        ("row-2", FakeClient(message=bad_json_message)),
        ("row-3", FakeClient(error=anthropic.AnthropicError("down"))),
        ("row-4", FakeClient(message=good_message)),
    ]

    outcomes = {"success": 0, "parse_error": 0, "api_error": 0}
    results = []
    total_spend_gbp = 0.0

    for row_id, client in rows:
        outcome, analysis, spend_gbp = analyse.analyse_response(client, row_id, "text")
        outcomes[outcome] += 1
        total_spend_gbp += spend_gbp
        if analysis is not None:
            results.append(analysis)

    assert outcomes == {"success": 2, "parse_error": 1, "api_error": 1}
    assert len(results) == 2  # only the successful rows produced output
    assert total_spend_gbp > 0  # rows 1, 2, 4 all made a billed API call
```

- [ ] **Step 2: Run the test**

Run: `cd wk09/solution && python -m pytest test_analyse.py -v`
Expected: 4 passed (this test plus the 3 from Task 5). Unlike Tasks 1–5, this step
is not expected to fail first — it adds no new production code, only a test that
exercises `analyse_response` (already implemented in Task 5) across a mixed batch. If
it fails, that means Task 5's `analyse_response` doesn't actually isolate one row's
failure from the next — re-check its three outcome branches (`success` /
`parse_error` / `api_error`) each return instead of raising.

- [ ] **Step 3: Run the full test suite**

Run: `cd wk09/solution && python -m pytest -v`
Expected: 17 passed (13 from `test_telemetry.py` + 4 from `test_analyse.py`)

- [ ] **Step 4: Commit**

```bash
cd wk09/solution
git add test_analyse.py
git commit -m "[Agent-Tom] Add mixed-outcome batch integration test

- test_analyse.py: exercise success/parse_error/api_error together across
  one simulated batch, proving one bad row doesn't stop the others from
  being processed and counted"
```

---

### Task 7: `OBSERVABILITY.md` — SigNoz setup and manual verification

**Files:**
- Create: `wk09/solution/OBSERVABILITY.md`

This task has no automated test — standing up SigNoz itself is a one-time, external,
manual step (per the design doc, not vendored into this repo). The "test" is a manual
checklist a human runs once to confirm telemetry actually arrives.

- [ ] **Step 1: Write `OBSERVABILITY.md`**

Create `wk09/solution/OBSERVABILITY.md`:

```markdown
# Observability setup (SigNoz)

`analyse.py` exports traces, metrics, and logs via OpenTelemetry (OTLP/gRPC) to a
self-hosted SigNoz instance. This is a one-time setup on whichever machine runs
`analyse.py` — SigNoz itself is not part of this repo.

## 1. Start SigNoz (self-hosted, once)

```bash
git clone https://github.com/SigNoz/signoz.git
cd signoz/deploy
./install.sh
```

Verify it's up:

```bash
curl http://localhost:8080/api/v1/health
# expect: {"status":"ok"}
```

Open the UI at <http://localhost:8080>.

## 2. Set environment variables before running analyse.py

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_INSECURE=true
export ANTHROPIC_API_KEY=your-key-here
```

(No `signoz-ingestion-key` header is needed for self-hosted SigNoz — that's only for
SigNoz Cloud.)

## 3. Run the analyser

```bash
python analyse.py
```

## 4. Verify telemetry arrived (manual checklist)

- [ ] **Traces:** SigNoz UI → Traces. You should see one trace per
      `messages.create()` call, with `model`, token counts, and latency as span
      attributes (from `AnthropicInstrumentor` — no manual span code).
- [ ] **Metrics:** SigNoz UI → Dashboards. Import the built-in Anthropic/LangChain LLM
      dashboard template (calls-by-model, token usage, p95 latency). Separately, build
      a "Consultation Batch Run" dashboard from: `consultation.spend.gbp`,
      `consultation.rows.total` (by `outcome` label), `consultation.response.bytes`,
      `consultation.batch.rows_total`.
- [ ] **Logs:** SigNoz UI → Logs. Search for `batch.started` / `batch.finished` to
      confirm one pair per run. If you want to see the parse-error path, temporarily
      lower `max_tokens` in `analyse.py` to force a truncated (non-JSON) response, run
      once, then search for `row.parse_error` — confirm the log shows a `response_length`
      and a truncated `response_snippet`, never the full response text.

## What this does not cover

- Retries, checkpoints, or resume across a crashed run — telemetry only makes
  failures *visible*, it doesn't make the script survive them.
- The Anthropic Batch API — `analyse.py` still makes one synchronous call per row.
- Validating at the full 20,000-row scale — only `data/responses_sample.csv` (40 rows)
  is available in this repo; the full export lives on the shared drive per
  `solution/README.md`.
```

- [ ] **Step 2: Commit**

```bash
cd wk09/solution
git add OBSERVABILITY.md
git commit -m "[Agent-Tom] Add SigNoz setup and manual verification doc

- OBSERVABILITY.md: one-time self-hosted SigNoz setup, required env vars,
  and a manual checklist for confirming traces/metrics/logs actually
  arrive — not vendored as a docker-compose.yaml per the design doc's
  'avoid infrastructure cosplay' call"
```

---

## Final check before calling this plan done

- [ ] Run the full suite once more: `cd wk09/solution && python -m pytest -v` — 17 passed
- [ ] Run the type checker and linter per `wk09/CLAUDE.md`'s working rules (whatever is
      configured for this repo — check for a `mypy`/`ruff`/`flake8` config before
      assuming none exists)
- [ ] Confirm `solution/spend/` and `solution/viewer.py` are untouched (`git status`)
- [ ] Confirm no full `response_text` appears in any committed code path's log/metric
      attributes (re-read `telemetry.py`'s `log_parse_error`)
- [ ] Add a `solution/AI_LOG.md` entry only if any task above required real iteration
      beyond what's written here (per repo root `CLAUDE.md`'s one-shot-success rule)

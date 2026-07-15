# SigNoz Observability Design — Consultation Insights (Agent-Tom)

## Purpose

The brief (`context/hackathon-brief-2-consultation-insights.pdf`) names **Visibility** —
"you can see what the system is doing and what it costs. Numbers, not vibes." — as one
of the five things that must be demonstrated by Wednesday afternoon. Today
`analyse.py` gives none of that: cost, call volume, latency, and failure rate are all
invisible until the process crashes or finishes. This design instruments `analyse.py`
so those numbers exist, and specifies how SigNoz (an open-source OpenTelemetry-native
observability platform) turns them into dashboards, traces, and logs.

This is a **design/spec document** — the step before an implementation plan (see
"Next steps" at the end). It does not contain code.

## Scope

**In scope:** `solution/analyse.py` only — the batch tool that makes one Anthropic API
call per consultation response and burns the shared departmental budget.

**Out of scope** (see "Explicitly out of scope" below for the reasoning):
- `solution/viewer.py` (makes no API calls; not instrumented)
- `solution/spend/` (tracks the *team's own* Claude Code session cost, a different
  concern from the *application's* production API spend)
- Implementing retries, checkpoints, or resume logic
- Implementing the Anthropic Batch API workflow itself
- Vendoring the SigNoz stack into this repo
- Alerting rules
- Validating at full 20,000-row scale (only `data/responses_sample.csv`, 40 rows, is
  available in this repo; the full export lives on the shared drive per
  `solution/README.md`)

## Baseline behaviour this design responds to

From `solution/analyse.py` (currently an unrefined copy of `starter/analyse.py`,
confirmed byte-identical):

- One synchronous `llm.invoke()` call per row, via `langchain_anthropic.ChatAnthropic`
  (`solution/analyse.py:11-15,43`).
- `json.loads(response.content)` with no error handling (`solution/analyse.py:44`) —
  a non-JSON completion crashes the entire run with zero record of which row or why.
- Results accumulate in memory and are written once at the end
  (`solution/analyse.py:64-66`) — nothing observable mid-run.
- No cost, latency, or call-count visibility of any kind today.

## Architecture

```
analyse.py
   │
   ├─ refactor: langchain_anthropic.ChatAnthropic  →  anthropic.Anthropic (raw SDK)
   │   same behaviour as today (one sync call per row); chosen so the
   │   instrumentation point also covers the Anthropic Batch API later
   │   (client.messages.batches.*), without redoing this work
   │
   ├─ AnthropicInstrumentor (pip package: openinference-instrumentation-anthropic)
   │   AnthropicInstrumentor().instrument(tracer_provider=provider)
   │   auto-patches client.messages.create() — one line, placed before any
   │   Anthropic call — and produces trace spans with model, prompt/completion,
   │   token counts, and latency without further code changes
   │
   ├─ manual OTel metrics (opentelemetry-sdk, hand-written — see "Signal design")
   ├─ manual OTel logs (Python `logging` + OTel LoggingHandler)
   │
   ▼ OTLP/gRPC, insecure (self-hosted, no ingestion key needed)
   OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
   OTEL_EXPORTER_OTLP_INSECURE=true
   │
   ▼
SigNoz OTel Collector → ClickHouse → Query Service → SigNoz UI (:8080)
```

**Why swap `langchain_anthropic` for the raw `anthropic` SDK:** OpenInference (the
project behind `AnthropicInstrumentor`) instruments the specific client method
(`messages.create`); Batch API is invoked through the same client
(`messages.batches.create/retrieve/results`). Instrumenting the raw SDK now means a
future Batch API migration — an explicitly separate, later piece of work — attaches to
telemetry that's already in place, rather than needing its own instrumentation pass.
This is the only change to `analyse.py`'s existing behaviour this design makes; it is
not a rewrite of the call pattern (still one synchronous call per row, same
`INSTRUCTIONS` prompt, same output shape).

**Self-hosted, not SigNoz Cloud:** Docker/podman-compose is already available on this
machine. Self-hosting avoids an external account and ongoing cost. Setup is
documented, not vendored into this repo (see "Operability" below) —
`git clone https://github.com/SigNoz/signoz.git && cd signoz/deploy && ./install.sh`,
verified with `curl http://localhost:8080/api/v1/health` → `{"status":"ok"}`.

## Signal design

What becomes a metric vs. a trace vs. a log, and why — this is the core question the
observability effort needs to answer, not just a list of things to instrument.

| Signal | Name | Captures | Why this shape |
|---|---|---|---|
| **Trace** (auto) | one span per `messages.create()` call | model, input/output token counts, latency, status | Auto-instrumented at the SDK boundary — zero manual code. Traces answer "which specific call": when one row is slow or fails, you inspect that span, not an aggregate. |
| **Metric** (manual) | `consultation.spend.gbp` — Counter, label `model` | £ cost per call, computed via the existing `solution/spend/pricing.py:cost_gbp()` | SigNoz's built-in LLM dashboard only offers a generic token-based "cost proxy." This repo already has real Anthropic pricing — reuse it for an actual £ figure. Answers "what does this cost" and, via rate × 20,000, "what would the full run cost." |
| **Metric** (manual) | `consultation.rows.total` — Counter, label `outcome` (`success` \| `parse_error` \| `api_error`) | one increment per row processed | This is the row-count/error-rate ask directly. Today there is no error rate at all — a bad response crashes the whole run instead of being counted. |
| **Metric** (manual) | `consultation.response.bytes` — Histogram | size of the raw model response payload | The "results data size" ask. Also a cheap drift signal: if the model stops respecting the one-sentence-summary instruction, response size grows before anything else shows it. |
| **Metric** (manual) | `consultation.batch.rows_total` — Gauge, set once at run start | total rows in this run's CSV | Denominator for "% of this run complete" — `rows.total` alone can't express progress without it. |
| **Log/Event** (manual) | `batch.started` / `batch.finished` — INFO | row count, model, duration, total £ spend | The single record of "did this run complete and what did it cost" — currently only reconstructable from terminal scrollback. |
| **Log/Event** (manual) | `row.parse_error` — ERROR | row id, **redacted** (length + truncated snippet, not full text) | The named defect: a non-JSON completion currently crashes silently. This makes it a searchable, alertable event — without shipping full free-text consultation responses to a shared backend (see PII note below). |

Rule of thumb applied throughout: **a metric when the trend in aggregate matters, a
log/event when one occurrence matters, a trace when the journey through one call
matters.** Row count is a metric because the running total is what's useful; one row's
parse failure is a log because the specific occurrence — which row, why — is what's
useful, not just that a counter went up.

**PII/redaction rule:** "public consultation" does not mean PII-free — a respondent can
still type a name, address, or other personal detail into free text. No log or metric
in this design carries full `response_text` as an attribute. `row.parse_error` logs
carry a length and a truncated/redacted snippet only. This follows the general
principle that telemetry, once exported, is shared, queryable by many people, and hard
to delete — its risk profile is not the same as a local variable.

## Dashboards

1. **Imported LLM dashboard** — SigNoz ships a pre-built Anthropic/LangChain-family
   template (calls-by-model, token usage over time, p95 latency,
   responses-by-finish-reason) that populates automatically once
   `AnthropicInstrumentor` is wired in. Import, don't rebuild.
2. **Custom "Consultation Batch Run" dashboard**, built from the manual metrics above:
   - Cumulative £ spend this run, plus a projected cost for 20,000 rows
     (current £/row rate × 20,000)
   - Row progress: success / parse_error / api_error as a stacked area against the
     `batch.rows_total` gauge — live progress during a large run instead of a
     scrolling terminal
   - Error rate (parse_error + api_error as % of rows processed) — currently
     undefined; today any error is a crash, not a percentage
   - Response size distribution
3. **Saved log view** — all `row.parse_error` / ERROR-severity logs: "show me every
   crash," replacing re-reading terminal scrollback after the fact.

## Explicitly out of scope

Named here so this doesn't creep into "the great rewrite" the brief warns against:

- **Retries/checkpoints/resume** — the brief's separate "Resilience" pillar. This
  design only makes failures *visible* (an `api_error` counter, an ERROR log); it does
  not make the script survive them.
- **The Batch API workflow itself** (submit/poll/retrieve) — only the SDK swap happens
  here, to avoid blocking that work later, not to start it now.
- **`viewer.py` and `solution/spend/`** — different concerns (no API calls; dev-tooling
  cost, not production cost), left uninstrumented.
- **Alerting rules** — SigNoz supports threshold alerts; noted as a natural next step,
  not built as part of this design.
- **Full 20,000-row validation** — only the 40-row sample is available in this repo.

## Operability

Setup instructions (clone SigNoz, run `install.sh`, verify health endpoint, set the
two `OTEL_EXPORTER_OTLP_*` env vars) will live in a new `solution/OBSERVABILITY.md`,
not as a vendored `docker-compose.yaml` in this repo — so `solution/` stays focused on
the analyser rather than carrying an infrastructure manifest nothing here runs
end-to-end. This mirrors the brief's warning against "infrastructure cosplay."

## Next steps

This document is the approved design. The next step is a step-by-step implementation
plan (via the `writing-plans` process) covering: the `anthropic` SDK swap, the
OTel SDK wiring (resource, tracer/meter/logger providers, exporters), the four manual
metrics and two manual log events, the `OBSERVABILITY.md` setup doc, and verification
against `data/responses_sample.csv`.

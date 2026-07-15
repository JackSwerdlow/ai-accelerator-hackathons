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

`analyse.py` has three modes (`--mode sequential|concurrent|batch`, see its own
`--help` and module docstring) — all three are instrumented:

```bash
python analyse.py                    # sequential
python analyse.py --mode concurrent
python analyse.py --mode batch
```

## 4. Verify telemetry arrived (manual checklist)

- [ ] **Traces:** SigNoz UI → Traces. For `--mode sequential`/`--mode concurrent`
      you should see one trace per `client.messages.create()` call, with `model` and
      latency as span attributes (from `AnthropicInstrumentor` — no manual span
      code). Prompt/completion content is intentionally hidden from these spans
      (`TraceConfig(hide_inputs=True, hide_outputs=True)` in `telemetry.init_telemetry()`)
      — consultation responses may contain PII, so only metadata is traced, never
      the text itself. **`--mode batch` produces no traces**: `AnthropicInstrumentor`
      only patches `messages.create`, not the Batch API's
      `messages.batches.create/retrieve/results` — batch mode is metrics/logs only.
- [ ] **Metrics:** SigNoz UI → Dashboards. Import the built-in Anthropic/LangChain LLM
      dashboard template (calls-by-model, token usage, p95 latency — populated by
      sequential/concurrent traces only, per above). Separately, build a
      "Consultation Batch Run" dashboard from: `consultation.spend.gbp` (labels:
      `model`, `batch` — true for Batch API spend, false otherwise, so the 50%
      discount is visible as a split), `consultation.cache.status` (labels: `status`
      = `hit`/`write`/`miss` — the prompt-cache payoff), `consultation.rows.total`
      (by `outcome` label: `success`/`parse_error`/`api_error`),
      `consultation.response.bytes`, `consultation.batch.rows_total`.
- [ ] **Logs:** SigNoz UI → Logs. Search for `batch.started` / `batch.finished` to
      confirm one pair per run (across all three modes). If you want to see the
      parse-error path, temporarily lower `--max-tokens` to force a truncated
      (non-JSON) response, run once, then search for `row.parse_error` — confirm the
      log shows a `response_length` and a truncated `response_snippet`, and that
      `error` is also truncated (the parser's own exception messages embed the raw
      model output, so both fields are redacted, not just one).

## What this does not cover

- Retries, checkpoints, resume, and the Batch API itself are already implemented in
  `analyse.py` (see its module docstring) — this document is about *observing* that
  behaviour, not building it.
- Validating at the full 20,000-row scale — only `data/responses_sample.csv` (40 rows)
  is available in this repo; the full export lives on the shared drive per
  `solution/README.md`. Use `--limit N` for a cheap smoke test at any scale in between.
- Alerting rules — SigNoz supports threshold alerts on any of the metrics above (e.g.
  "page if `consultation.rows.total{outcome=api_error}` rate exceeds X"); none are
  configured here.

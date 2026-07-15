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

# FOI Multi-Agent CLI — wk06

A CLI system that automates the repeatable parts of UK Freedom of Information (FOIA 2000) request
handling. For each request it runs: **triage** → **RAG policy retrieval** → **compliance analysis
with cited evidence** → **response drafting** → **hybrid PII redaction** → **human-in-the-loop
approval gate** → **dual-format audit trail**.

Built with LangChain-Anthropic, ChromaDB, nomic-embed-text-v1.5, Pydantic v2, Rich.

---

## Quick start

### 1. Prerequisites

- Python 3.10+
- An `ANTHROPIC_API_KEY` environment variable (or a `.env` file — copy `.env.example`)

### 2. Set up the virtual environment (CPU-only torch — avoids 1.9 GB CUDA download)

```bash
cd wk06/solution
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --no-cache-dir --upgrade pip
python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install --no-cache-dir "langchain-anthropic>=1.1.0" langchain-core \
  langchain-text-splitters chromadb sentence-transformers einops rich \
  "pydantic>=2" python-dotenv pytest ruff mypy
pip install -e .
```

The nomic-embed-text-v1.5 embedding model (~274 MB) downloads automatically on first run.
If your environment blocks remote code, edit `foi_system/config.py` to switch `EMBED_MODEL`
to the `EMBED_FALLBACK` value (`sentence-transformers/all-MiniLM-L6-v2`).

### 3. Verify the build

```bash
pytest -q           # expect 69 passing
ruff check .
mypy .
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key. The system hard-fails at startup if this is absent. |
| `OPERATOR_ID` | No | Pre-fill the operator identifier so you don't need `--operator` on every run. The flag still overrides this value; the CLI rejects an empty resolved value. |

---

## Usage

### Index policy documents

Before processing any requests, index the policy documents into the vector store:

```bash
foi index --policies corpus/policies
# Indexed 17 chunks from corpus/policies.
```

The index persists in `output/chroma_db/`. Re-run `foi index` whenever policies are updated.
The `process` command auto-indexes `corpus/policies` if the collection is empty, so this step
is optional for a first run against the default corpus.

To use a custom policy directory:

```bash
foi index --policies /path/to/your/policies
```

Policy files must be `.txt` format. The indexer splits them into 512-token chunks with 64-token
overlap. A staleness warning is printed if any policy file has not been re-indexed within 30 days.

### Process a single request

```bash
foi process corpus/requests/r03-s40-s43-mixed.txt --operator "j.smith@dept.gov.uk"
```

The `--operator` flag is **required** and must be non-empty. It identifies the officer who is
accountable for the approval decision; it is written to every audit entry. You may pre-fill it
via the `OPERATOR_ID` environment variable, but the CLI still hard-fails if the resolved value
is empty.

### Process a folder of requests

```bash
foi process corpus/requests/ --operator "j.smith@dept.gov.uk"
```

Processes every `.txt` file in the folder in alphabetical order. One request failure never aborts
the rest. A Rich live-progress display updates per request; a cost summary table is printed at
the end.

### Use a custom policy directory with process

```bash
foi process corpus/requests/ --operator "j.smith@dept.gov.uk" --policies /path/to/policies
```

The `--policies` flag is only used for the auto-index path (when the collection is empty).
If you have already indexed custom policies with `foi index`, this flag is ignored.

### Run the evaluation harness

```bash
foi eval --gold corpus/gold/gold_answers.jsonl
```

Runs triage + compliance (no gate, no response, no redaction) over the gold set and prints
accuracy, recall, false-positive rate, and citation-grounding pass-rate. The default gold file
is `corpus/gold/gold_answers.jsonl`; pass `--gold` to use a different file.

---

## The human-in-the-loop approval gate

Every FOI request must be reviewed by a named operator before a response is finalised. The gate
runs interactively in the terminal after the AI pipeline completes.

### What you see

The gate renders a series of panels in order:

1. **OPERATOR DECISION REQUIRED** — the AI's recommendation (`RELEASE`, `PARTIAL_RELEASE`, or
   `WITHHOLD`) in a yellow border. This is the first thing you see so you can anchor your review.

2. **Triage** — topic category, complexity, and the AI's confidence score (0–1). If confidence
   is below 0.5 a red `LOW CONFIDENCE — manual review strongly advised` banner appears. If the
   AI detected an ambiguous request a `CLARIFICATION RECOMMENDED` banner shows the reason.

3. **THIRD-PARTY NOTIFICATION** (when applicable) — a red banner if the compliance agent flagged
   that a third party may need to be notified before release (typically s41 / s40(2) cases).

4. **Exemption Findings** — a table listing every exemption the compliance agent considered:
   statutory section (e.g. `s40`), whether it is absolute or qualified, the rationale, a verbatim
   quote from the policy evidence, and any public interest test reasoning.

5. **Retrieved Evidence** — up to five policy chunks retrieved by the RAG layer, each with its
   source file, section, and cosine distance (lower = more relevant).

6. **AI-GENERATED DRAFT** — the redacted letter the system proposes to send, in a magenta border.
   This is what the requester would receive if you approve.

### Decision options

After reviewing the panels you are prompted:

```
[a]pprove / [r]eject / [m]odify:
```

- **approve** — accept the AI draft as-is. You are then asked for optional notes (press Enter to
  skip). The case is marked `processed` and the letter is finalised.

- **reject** — decline to release any response. A rejection reason is required (cannot be empty).
  The case is marked `rejected`. The draft is not sent.

- **modify** — replace the AI draft with your own text. You are prompted to enter the revised
  letter on a single line. The modification (before and after) is recorded in the audit trail.

Any other input re-prompts. `Ctrl-C` at the gate terminates the batch with an error entry in
the audit trail; partial results are still written.

### What is audited

The gate writes exactly one `decision` audit entry recording: the decision, the original
AI recommendation, your operator ID, a timestamp, any notes or rejection reason, and the
evidence chunk references the compliance agent used. The operator ID and evidence refs are
deliberately included so the decision can be traced back to the specific policy passages that
supported it.

---

## Output

| Path | Contents |
|------|----------|
| `output/results/<request_id>.json` | Per-request `CaseRecord` (triage, compliance, response, redaction, decision, costs) |
| `output/audit_trail.jsonl` | Append-only JSONL audit (all events, compliance-queryable) |
| `output/audit_trail.txt` | Append-only human-readable audit (one line per event) |
| `output/chroma_db/` | Persistent ChromaDB vector store (policy index) |

All `output/` paths are gitignored. **Audit files accumulate across runs — they are never reset.**
To start a fresh audit trail, delete or rename `output/audit_trail.jsonl` and
`output/audit_trail.txt`.

### Reading a result JSON

Each `output/results/<request_id>.json` is a `CaseRecord` with this structure:

```json
{
  "request_id": "r03-s40-s43-mixed",
  "request_file": "r03-s40-s43-mixed.txt",
  "request_text": "...",
  "status": "processed",          // "processed" | "rejected" | "error" | "pending"
  "triage": {
    "topic": "personal_data",     // finance_spending | staffing_hr | procurement_commercial |
                                  // internal_deliberations | personal_data | other
    "complexity": "high",         // low | medium | high
    "summary": "...",
    "confidence": 0.85,           // 0–1; below 0.5 triggers LOW CONFIDENCE banner
    "clarification_recommended": false,
    "clarification_reason": null
  },
  "retrieved": [...],             // up to 5 policy chunks used as evidence
  "compliance": {
    "exemptions": [
      {
        "section": "s40",
        "kind": "absolute",       // absolute | qualified
        "applies": true,
        "rationale": "...",
        "public_interest_test": null,
        "citations": [{"section": "s40", "quote": "...", "source": "...", "chunk_index": 2}]
      }
    ],
    "recommendation": "withhold", // release | partial_release | withhold
    "policy_sources": ["data-handling-policy.txt"],
    "third_party_notification_required": false,
    "grounded": true              // false if retrieval returned nothing or citation check failed
  },
  "response": {"letter": "...", "exemptions_cited": ["s40"], "evidence_summary": "..."},
  "redaction": {
    "redacted_draft": "...",
    "schedule": [{"category": "email", "exemption_section": "s40", "reason": "..."}],
    "redaction_complete": true,
    "needs_mandatory_review": false
  },
  "decision": {
    "decision": "approve",        // approve | reject | modify
    "operator": "j.smith@dept.gov.uk",
    "timestamp": "2026-06-25T14:02:00Z",
    "notes": "",
    "original_recommendation": "withhold",
    "modification": null,
    "rejection_reason": null,
    "evidence_refs": ["foi-exemptions-guide.txt#2", "data-handling-policy.txt#0"]
  },
  "costs": [
    {"agent": "triage", "model": "claude-haiku-4-5-20251001", "input_tokens": 312,
     "output_tokens": 89, "cost_usd": 0.00076},
    ...
  ],
  "errors": []                   // non-empty when a stage failed and used its fallback
}
```

Key fields to check after each run:

- `status` — `error` means at least one stage used its fallback. Check `errors` for details.
- `compliance.grounded` — `false` means the compliance analysis had no policy evidence; treat
  the recommendation with extra caution.
- `redaction.needs_mandatory_review` — `true` means the AI redaction pass was incomplete;
  a human must review the draft before it is sent.
- `triage.confidence` — below 0.5 warrants careful manual review regardless of the recommendation.

### Reading the audit trail

`output/audit_trail.txt` has one line per event:

```
2026-06-25T14:01:58Z  triage     request=r03-s40-s43-mixed  agent=-  operator=-  topic=personal_data complexity=high confidence=0.85
2026-06-25T14:02:05Z  compliance request=r03-s40-s43-mixed  agent=-  operator=-  recommendation=withhold grounded=True exemption_count=2
2026-06-25T14:02:12Z  response   request=r03-s40-s43-mixed  agent=-  operator=-  exemptions_cited=['s40','s43'] letter_length=1742
2026-06-25T14:02:15Z  redaction  request=r03-s40-s43-mixed  agent=-  operator=-  redaction_complete=True needs_mandatory_review=False
2026-06-25T14:02:30Z  decision   request=r03-s40-s43-mixed  agent=-  operator=j.smith@dept.gov.uk  decision=approve original_recommendation=withhold evidence_refs=[...]
2026-06-25T14:02:30Z  cost_summary request=r03-s40-s43-mixed  agent=-  operator=-  total_usd=0.025 per_agent={...}
```

`output/audit_trail.jsonl` contains the same events in structured JSON — suitable for
compliance queries, dashboards, or log aggregation tools.

---

## Cost tracking

Every LLM call is cost-tracked. After a folder run a summary table is printed to stdout showing
total spend and per-agent breakdown. The same data is also in:

- `output/results/<request_id>.json` → `costs` array (per-request, per-agent breakdown)
- `output/audit_trail.*` → `cost_summary` events

Model costs used (as of 2026-06-24):

| Model | Input | Output |
|-------|-------|--------|
| `claude-haiku-4-5-20251001` (triage, redaction) | $1.00 / MTok | $5.00 / MTok |
| `claude-sonnet-4-6` (compliance, response) | $3.00 / MTok | $15.00 / MTok |

A typical single request costs around $0.02–$0.04. Cost is intentionally hidden from the HITL
gate display to prevent it influencing approval decisions; it appears only in the audit trail and
the end-of-run summary.

---

## Corpus

| Path | Contents |
|------|----------|
| `corpus/policies/` | Policy documents used for RAG (copied from starter, can be extended) |
| `corpus/requests/` | 8 synthetic FOI request files (5 valid cases + 3 edge cases) |
| `corpus/gold/gold_answers.jsonl` | 25 labelled requests for eval (committed) |
| `corpus/gold/held_out.jsonl` | 5 held-out items (gitignored — kept out of the tuning loop) |

### Adding custom policies

1. Copy your policy `.txt` files into `corpus/policies/` (or any other directory).
2. Re-index: `foi index --policies corpus/policies`
3. The index is rebuilt from scratch on each `foi index` run.

### Adding custom requests

Request files are plain `.txt` files — no special format is required beyond being readable UTF-8.
Place them in any directory and pass that path to `foi process`.

### Edge cases handled

The system degrades gracefully on the three edge-case files in `corpus/requests/`:

| File | Condition | Behaviour |
|------|-----------|-----------|
| `r06-edge-empty.txt` | Empty file | Triage falls back to `other/high/0.0 confidence`; compliance withholds with `grounded=false` |
| `r07-edge-garbled.txt` | Malformed text | Pipeline runs on best effort; `clarification_recommended=true` likely |
| `r08-edge-oversized.txt` | Very large request | Pipeline runs; token costs will be higher than typical |

---

## Architecture

```
request.txt
  → triage (Haiku)        — topic / complexity / confidence / clarification-duty
  → retrieve (nomic RAG)  — top-5 policy chunks by cosine distance
  → compliance (Sonnet)   — IRAC-light: exemption analysis + verbatim citation + PIT
      └─ verify_citations  — L1 id-membership + L2 quote-coverage ≥ 0.85
  → response (Sonnet)     — formal FOIA-2000 letter grounded in findings
  → redaction (Haiku)     — hybrid: regex (email/phone/postcode/staff-number) + model pass
  → HITL gate             — operator sees: RECOMMENDATION headline, evidence, REDACTED DRAFT
      → approve / reject / modify
  → audit                 — dual-format JSONL + .txt; payload secrets scrubbed
  → result JSON           — CaseRecord.model_dump() written even on rejection/error
```

**Reliability layers:** `.with_retry(stop_after_attempt=4)` on every LLM call → per-stage typed
fallback → circuit breaker (3 failures → degrade stage) → per-stage try/except → batch isolation.

**Governance:** operator identity required (non-empty, never defaulted); cost hidden at the gate
(audit + end-of-run summary only); evidence_refs copied into the decision audit entry.

---

## Troubleshooting

**`ANTHROPIC_API_KEY` not set** — Copy `.env.example` to `.env` and add your key. Make sure you
are in `wk06/solution/` when running `foi` so the `.env` file is found.

**`Error: --operator is required`** — Pass `--operator "your.name@org.gov.uk"` or set
`OPERATOR_ID=your.name@org.gov.uk` in your `.env` file.

**`Warning: stale policy documents`** — Run `foi index` to refresh the ChromaDB index from the
current files on disk.

**`compliance.grounded: false`** — The retrieval returned no matching policy chunks, so the
compliance analysis ran without evidence. Check that `foi index` has been run and that
`output/chroma_db/` exists. If the vector store is corrupt, delete `output/chroma_db/` and
re-index.

**`redaction.needs_mandatory_review: true`** — Automated redaction flagged that the draft may
still contain PII. A human must review the `redacted_draft` field before sending.

**Embedding model download fails** — If `nomic-ai/nomic-embed-text-v1.5` cannot be downloaded
(e.g. air-gapped environment), edit `foi_system/config.py` and set:
```python
EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
```
This fallback is smaller and does not require `trust_remote_code`.

**Gate fails with `EOFError`** — The HITL gate requires an interactive terminal. Do not pipe
stdin into `foi process` or run it in a non-interactive shell.

---

## Development

```bash
pytest -q                    # run all 69 tests
ruff check . && ruff format .   # lint + format
mypy .                       # type-check
```

All tests are offline (no network, no API key required). Agent LLMs are injected via
`RunnableLambda` in tests; the HITL gate uses a monkeypatched `input_fn`.

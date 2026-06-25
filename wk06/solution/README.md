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

## Usage

### Index policy documents

```bash
foi index --policies corpus/policies
# Indexed 17 chunks from corpus/policies.
```

The index persists in `output/chroma_db/`. Re-run `foi index` whenever policies are updated.

### Process a single request

```bash
foi process corpus/requests/r03-s40-s43-mixed.txt --operator "j.smith@dept.gov.uk"
```

The `--operator` flag is **required** and must be non-empty. You may pre-fill it via the
`OPERATOR_ID` environment variable, but the flag still hard-fails if the resolved value is empty.
If the policy index is empty, the CLI auto-indexes `corpus/policies` before processing.

### Process a folder of requests

```bash
foi process corpus/requests/ --operator "j.smith@dept.gov.uk"
```

Processes every `.txt` file in the folder. One request failure never aborts the rest.
A Rich live-progress display updates per request; a cost summary table is printed at the end.

### Run the evaluation harness

```bash
foi eval --gold corpus/gold/gold_answers.jsonl
```

Runs triage + compliance (no gate, no response, no redaction) over the gold set and prints
accuracy, recall, false-positive rate, and citation-grounding pass-rate.

---

## Output

| Path | Contents |
|------|----------|
| `output/results/<request_id>.json` | Per-request `CaseRecord` (triage, compliance, response, redaction, decision, costs) |
| `output/audit_trail.jsonl` | Append-only JSONL audit (all events, compliance-queryable) |
| `output/audit_trail.txt` | Append-only human-readable audit (one line per event) |
| `output/chroma_db/` | Persistent ChromaDB vector store (policy index) |

All `output/` paths are gitignored. Audit files **accumulate across runs** — they are never reset.

---

## Corpus

| Path | Contents |
|------|----------|
| `corpus/policies/` | Policy documents used for RAG (copied from starter, can be extended) |
| `corpus/requests/` | 8 synthetic FOI request files (5 valid cases + 3 edge cases) |
| `corpus/gold/gold_answers.jsonl` | 25 labelled requests for eval (committed) |
| `corpus/gold/held_out.jsonl` | 5 held-out items (gitignored — kept out of the tuning loop) |

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

## Development

```bash
pytest -q                    # run all 69 tests
ruff check . && ruff format .   # lint + format
mypy .                       # type-check
```

All tests are offline (no network, no API key required). Agent LLMs are injected via
`RunnableLambda` in tests; the HITL gate uses a monkeypatched `input_fn`.

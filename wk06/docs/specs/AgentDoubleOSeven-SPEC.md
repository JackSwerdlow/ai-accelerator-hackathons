# FOI Multi-Agent System — Technical Specification

**Author:** AgentDoubleOSeven · **Date:** 2026-06-24 · **Status:** Draft for comparison
**Provenance:** Every decision below traces to the design-brainstorm planner
(`wk06/docs/research/foi-spec-planner.html`) and the operator's exported JSON. No other
agent's documents were used as input.

---

## 0. Orchestration decision — confirmed

| Decision | Outcome |
|----------|---------|
| **Orchestration framework** | **Plain Python + Anthropic SDK — confirmed by the operator.** Considered against LangChain (the operator's note leaned that way and asked for a steer): the rubric scores per-call cost capture, the interactive HITL pause, and deterministic fallbacks — all of which a framework abstracts away from a fixed 4-stage pipeline, while LangChain's strength (dynamic, model-driven routing) isn't needed here. |

Everything below is locked from the JSON.

---

## 1. Overview

A CLI application that automates the repeatable parts of UK Freedom of Information (FOI)
request handling. For a folder of FOI request files it runs, per request:

1. **Triage** — classify topic + complexity.
2. **Compliance** — retrieve relevant policy via RAG, identify FOIA exemptions, run the
   public-interest test where required, recommend an outcome.
3. **Response drafting** — compose a reply grounded in the triage + compliance findings.
4. **Redaction** — mask personal data in the draft before human review.
5. **Human-in-the-loop (HITL) gate** — pause, present the **decision** for approval, accept
   approve / reject / modify; nothing is finalised without a human.
6. **Persist** — write a structured JSON result and append to a human-readable audit log.

A **supervisor** orchestrates the sequence, wraps every stage in error handling, and
accumulates cost. Every LLM call is cost-tracked; an end-of-run summary prints per agent and
per request.

**Locked context:** Provider = Anthropic / Claude · Scope = the full brief (7 requirements +
all 4 lower-priority goals) · Build mode = small team, parallel, AI-driven · Target =
Excellent on all four rubric axes (Automation value, Reliability, Governance, Cost awareness).

---

## 2. Architecture

### 2.1 Pipeline

```
                         ┌─────────── supervisor (code-orchestrated) ───────────┐
 request.txt ──▶ triage ─▶ compliance(RAG) ─▶ response ─▶ redaction ─▶ HITL gate ─▶ persist
                  Haiku      Sonnet              Sonnet      Haiku       human       result.json
                  4.5        4.6                 4.6         4.5         decision     + audit.txt
                         └── try/except + fallback per stage; cost logged per call ──┘
```

The supervisor calls each agent as a **pure function of typed input → typed output**. There is
no model-driven routing: the order is fixed and deterministic, which is what makes the cost
attribution, the HITL pause, and the demo reliable.

### 2.2 Module layout (`wk06/solution/`)

| File | Responsibility |
|------|----------------|
| `main.py` | Typer CLI entry: `index`, `process <path>`. |
| `config.py` | Per-agent model IDs, price table, paths, retrieval `k`, cost cap, fallback chains. |
| `schemas.py` | All Pydantic data contracts (the inter-agent interface). |
| `llm.py` | Thin Anthropic-SDK wrapper: one `call_structured()` seam that does structured output + retry + model fallback + cost logging. **Every LLM call goes through here.** |
| `agents/triage.py` | Triage agent. |
| `agents/compliance.py` | Compliance agent (RAG-backed, rule-assisted). |
| `agents/response.py` | Response-drafting agent. |
| `agents/redaction.py` | Redaction agent (hybrid). |
| `rag/indexer.py` | `chunk_text` (section-aware), `index_policies`, `search_policies`. |
| `cost.py` | `CostTracker` — per-call log, per-agent + per-request rollup, end-of-run summary. |
| `audit.py` | Append-only `.txt` audit writer. |
| `hitl.py` | `human_checkpoint()` — Rich evidence panel + approve/reject/modify. |
| `supervisor.py` | Orchestration, per-stage error wrapping, result assembly. |
| `documents/` | `foi_requests/` (sample + dummy), `policies/` (copied from starter). |
| `output/` | `*-result.json` per request + `audit.txt` for the run. |

---

## 3. Data contracts (`schemas.py`)

Schemas are defined **first** and are the only coupling between stages. They double as the
native structured-output schema (§7) and the result-file shape (§9).

```python
from pydantic import BaseModel
from typing import Literal

Topic = Literal["spending","procurement","staffing","policy",
                "personal_data","correspondence","other"]
Complexity = Literal["low","medium","high"]
Recommendation = Literal["release","partial_release","withhold"]

class TriageResult(BaseModel):
    topic: Topic
    complexity: Complexity
    complexity_drivers: list[str]   # e.g. ["likely_exemptions","third_party_personal_data"]
    summary: str

class ExemptionFinding(BaseModel):
    section: str                    # "s12","s21","s36","s40","s41","s43"
    kind: Literal["absolute","qualified"]
    applies: bool
    reasoning: str
    policy_ref: str                 # "<source>#<section>" — maps to a retrieved chunk

class ComplianceResult(BaseModel):
    exemptions: list[ExemptionFinding]
    recommendation: Recommendation
    public_interest_test: str | None    # populated only for qualified exemptions (s36, s43)
    policy_sources: list[str]           # chunk ids / source sections cited
    confidence: Literal["low","medium","high"]

class DraftResult(BaseModel):
    draft_response: str
    evidence_summary: str           # decision-centred summary for the human reviewer

class RedactionResult(BaseModel):
    redacted_response: str
    redactions: list[str]           # what was masked (categories, not the values)
    needs_mandatory_review: bool    # True if the redaction pass itself failed/uncertain

class Decision(BaseModel):
    decision: Literal["approved","rejected","modified"]
    operator: str
    timestamp: str                  # ISO-8601 UTC
    notes: str
    evidence_refs: list[str]        # chunk ids / source sections shown at the gate
    final_response: str             # the text actually approved (post-edit if modified)

class CostEntry(BaseModel):
    agent: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    est_cost_usd: float
```

> The result-file JSON shape (§9) is the operator's proposed schema, **carried over unreviewed**
> by their own note. It is provisional and may be revised once reviewed.

---

## 4. Agents

All agents are stateless functions; their model is read from `config.py`. All LLM calls go
through `llm.call_structured(model, schema, system, user)`.

### 4.1 Triage — `claude-haiku-4-5`

Classifies a request into the taxonomy below (operator deferred taxonomy design to the AI, so
this is a **proposed** scheme, to be validated against real requests):

- `topic` ∈ {spending, procurement, staffing, policy, personal_data, correspondence, other}
- `complexity` ∈ {low, medium, high}, justified by `complexity_drivers` ∈ {likely_exemptions,
  data_volume, cross_team, public_interest_test, third_party_personal_data}.

Returns `TriageResult`. Haiku is sufficient and cheap for classification.

### 4.2 Compliance — `claude-sonnet-4-6` (RAG-backed, rule-assisted)

The reasoning core. Procedure:

1. `search_policies(request_text, k)` → retrieve top section chunks (§6).
2. Build a prompt with the retrieved chunks as context + the request + the triage result.
3. Instruct the model to: identify candidate exemptions; tag each **absolute** (e.g. s40, s41)
   vs **qualified** (s36, s43); for qualified exemptions run a **public-interest test**;
   recommend `release` / `partial_release` / `withhold`; cite the specific chunk for each
   exemption.
4. Return `ComplianceResult`, including `public_interest_test` text only where a qualified
   exemption is in play, and `policy_sources` listing the cited chunks.

Sonnet 4.6 (per the operator's downgrade from Opus) is the reasoning model here; adaptive
thinking may be enabled for this stage to improve exemption reasoning.

### 4.3 Response drafting — `claude-sonnet-4-6`

Composes a formal FOI response that references the classification and compliance findings, and
respects the recommendation (e.g. a `withhold` draft explains the exemption and the
public-interest reasoning; a `partial_release` draft notes what is withheld and why). Produces a
**decision-centred `evidence_summary`** for the reviewer. Returns `DraftResult`.

### 4.4 Redaction — `claude-haiku-4-5` (hybrid)

Runs **before** the human gate. Two passes:

1. **Deterministic regex** for structured PII: emails, phone numbers, UK postcodes.
2. **LLM (Haiku)** for names and contextual personal data regex cannot catch.

Returns `RedactionResult`. If the LLM pass errors or is uncertain, the draft is passed through
**unredacted but flagged** (`needs_mandatory_review = True`) so the human cannot miss it. Maps
directly to the s40 personal-data exemption.

### 4.5 Supervisor — `supervisor.py`

Sequences the agents, wraps each call in try/except (§8), assembles the full result, drives the
HITL gate (§5), and writes artefacts (§9). One bad request never aborts the batch.

---

## 5. Human-in-the-loop gate (`hitl.py`)

**One gate**, placed at the point **after the LLM has made its decision** (post-compliance,
post-draft, post-redaction). Per the operator's note, the **compliance decision is centre-stage**
— the draft is supporting context, not the headline.

**Displayed at the gate** (operator's evidence toggles):

1. **Recommendation — front and centre**: `release` / `partial_release` / `withhold`.
2. Triage classification (topic + complexity).
3. Exemption findings + reasoning + the public-interest test.
4. Retrieved policy chunks (source + section) backing each exemption.
5. The (redacted) draft response — secondary.
6. A prominent banner if `needs_mandatory_review` is set.

**Not displayed:** per-request cost (operator: not needed at the gate — but it **is** written to
the logs, §8/§10).

**Operator actions** (approve / reject / modify):

- **approve** → the (possibly edited) response is finalised.
- **reject** → discarded; operator gives a reason.
- **modify** → operator either **edits the draft text inline** or **gives instructions for a
  regeneration** (the response agent re-runs with those instructions).

The gate **blocks** on operator input and records a `Decision` (operator id, ISO-8601 timestamp,
evidence refs, notes, final response). Rendered as a Rich panel.

---

## 6. RAG design (`rag/indexer.py`)

- **Store:** ChromaDB (brief-mandated). Indexed **at the start of each `process` run** in the
  same process, to avoid the documented in-memory-collection-lost-between-commands pitfall.
- **Embeddings:** Chroma's default local sentence-transformer model. No embedding API key, runs
  without a hosted embedding call. (First run downloads the model — see §11 fallback.)
- **Chunking — section-aware:** the FOI exemptions guide is already structured by section
  (`SECTION 12`, `… 21`, `… 36`, `… 40`, `… 41`, `… 43`, plus `PUBLIC INTEREST TEST`,
  `PARTIAL DISCLOSURE`, `RESPONSE TIMELINE`). `chunk_text` splits on those headings so **one
  exemption == one chunk**, giving clean, quotable citations. The data-handling policy is
  chunked the same way on its headings.
- **Retrieval:** `search_policies(query, k=3-4)`; the **request text itself** is the query (not a
  summary or a label). Each result carries `{source, section, text, chunk_id}`.

---

## 7. Structured output

Every agent uses **native structured outputs** (`output_config.format` with the agent's Pydantic
JSON schema), validated at the API layer. This eliminates the "unparseable response" failure
class. Schemas are flat (no recursion / numeric bounds), which suits the structured-outputs
constraints. Supported on both chosen models (Sonnet 4.6, Haiku 4.5).

---

## 8. Error handling & fallback (layered — all five layers enabled)

Centralised in `llm.py` and `supervisor.py`:

1. **SDK auto-retry** — the Anthropic SDK retries 429 / 5xx / network with backoff.
2. **Per-agent typed fallback** — on persistent failure each agent returns a safe default:
   - triage → `complexity="high"`, `topic="other"` (route to human, fail safe);
   - compliance → `recommendation="withhold"`, `confidence="low"` (safest outcome), flagged;
   - response → placeholder draft "Automated drafting failed — manual response required";
   - redaction → pass through unredacted with `needs_mandatory_review=True`.
3. **Model fallback** — on a model error, retry on the configured fallback chain (e.g. compliance
   `sonnet-4-6 → haiku-4-5`); the downgrade is logged.
4. **Cost-threshold fallback** — if a request's cumulative cost exceeds the configured cap,
   subsequent calls for that request downgrade to the cheapest model; logged.
5. **Per-stage try/except** in the supervisor so one bad request never kills the run.

Every failure, fallback, and downgrade is written to the audit log.

---

## 9. Persistence

- **Per-request result — JSON** (`output/<stem>-result.json`): classification, exemptions, draft,
  human decision, and cost breakdown. Proposed shape (provisional, operator unreviewed):

  ```json
  {
    "request_file": "request-001.txt",
    "classification": { "topic": "spending", "complexity": "medium", "summary": "..." },
    "compliance": {
      "exemptions": [
        { "section": "s43", "kind": "qualified", "applies": true,
          "reasoning": "...", "policy_ref": "foi-exemptions-guide.txt#s43" }
      ],
      "recommendation": "partial_release",
      "public_interest_test": "..."
    },
    "draft_response": "...",
    "human_decision": { "decision": "approved", "operator": "jdoe",
                        "timestamp": "2026-06-24T10:31:00Z", "notes": "",
                        "evidence_refs": ["chunk_12","chunk_07"] },
    "cost": { "by_agent": { "triage": 0.0003, "compliance": 0.0121, "response": 0.0044 },
              "total": 0.0168 }
  }
  ```

- **Run-wide audit log — `.txt`** (`output/audit.txt`, operator's explicit format choice):
  append-only, human-readable, one timestamped line per event — every agent decision, human
  override, and cost entry. Example:

  ```
  2026-06-24T10:31:00Z | request-001.txt | TRIAGE     | model=claude-haiku-4-5  | topic=spending complexity=medium | tok in=412 out=88 | $0.0008
  2026-06-24T10:31:05Z | request-001.txt | COMPLIANCE | model=claude-sonnet-4-6 | rec=partial_release exemptions=[s43] | tok in=1840 out=260 | $0.0094
  2026-06-24T10:31:07Z | request-001.txt | REDACTION  | model=claude-haiku-4-5  | masked=[email,name] | tok in=520 out=210 | $0.0016
  2026-06-24T10:31:20Z | request-001.txt | HUMAN      | operator=jdoe decision=approved evidence_refs=[chunk_12,chunk_07] notes=""
  ```

---

## 10. Cost tracking (`cost.py`)

- `CostTracker.log_call(agent, model, usage)` records a `CostEntry` per call, computing
  estimated cost from the price table (operator's values, $/1M tokens):
  `claude-haiku-4-5 (1.00, 5.00)` · `claude-sonnet-4-6 (3.00, 15.00)` · `claude-opus-4-8 (5.00, 25.00)`.
- Rolls up **per agent** and **per request**; per-request totals are embedded in each result JSON.
- Prints an **end-of-run summary** (Rich table): per-agent totals, per-request totals, grand total.
- Cost is **logged everywhere** but **not shown at the HITL gate** (operator's instruction).

---

## 11. CLI, configuration & data

- **CLI (Typer):** `python -m solution.main index` (build the policy index) and
  `python -m solution.main process <folder|file>` (run the pipeline). **Rich** renders the HITL
  panel, the live batch progress, and the cost summary.
- **Batch (sequential + progress):** requests processed one at a time — the natural fit for an
  interactive gate. A Rich live display shows per-request status, cumulative cost, and ETA.
- **Models / config:** per-agent model IDs, fallback chains, price table, retrieval `k`, and the
  cost cap live in `config.py`.
- **Sample + dummy data** (operator: ensure runnable data exists): copy the three starter
  requests, and add dummy requests that exercise distinct paths — (a) a **personal-data** request
  naming individuals (exercises s40 + redaction), (b) a **broad/expensive** request (exercises
  s12 cost limit), (c) a **clean releasable** request (exercises the `release` path). The policy
  documents are copied from the read-only starter.
- **Embedding fallback:** if the local sentence-transformer model can't download, document the
  switch to a hosted embedding provider as an escape hatch (does not affect the Claude provider
  choice).

---

## 12. Mapping to the rubric

| Axis | How this design earns "Excellent" |
|------|-----------------------------------|
| **Automation value** | Rule-assisted exemption reasoning with absolute/qualified split + public-interest test; every finding cites a retrieved policy chunk → evidence-backed, end-to-end with one human touch. |
| **Reliability** | Five-layer defence; native structured outputs remove the parse-failure class; one bad request never kills the batch. |
| **Governance** | Single decision-centred gate with rich evidence; append-only `.txt` audit trail of every decision, override and cost, with operator identity, timestamps and evidence refs. |
| **Cost awareness** | Per-call logging rolled up per-agent and per-request, deliberate model tiering, end-of-run summary. |

---

## 13. Out of scope / assumptions

- No "neither confirm nor deny" handling, no statutory-deadline tracking beyond what the policy
  corpus states.
- Operator identity is a supplied string (no auth system).
- The triage taxonomy and the result-JSON shape are AI proposals pending operator validation.

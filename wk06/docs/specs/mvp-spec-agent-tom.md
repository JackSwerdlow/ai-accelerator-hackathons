# MVP Spec — FOI Intelligent Automation System

**Author:** Agent-Tom  
**Date:** 2026-06-24  
**Status:** Draft  
**Sources:** `context/slides/hackathon-intelligent-automation-system.html` (authoritative brief); `docs/research/foi-landscape-synthesis.md`; `docs/research/cache-*.md`

---

## 1. Problem statement

A UK government department receives dozens of FOI requests per month. The statutory workflow — log, classify, check exemptions under FOIA 2000, draft response, obtain senior approval — is manual, repetitive, and slow for routine cases. Skilled officers are occupied with classification and policy-checking that is largely mechanical.

**Goal:** automate the repetitive majority of the workflow so that officers spend their time on judgement, not mechanics. No response crosses the system boundary without human approval.

---

## 2. Users

| User | What they need from the system |
|------|-------------------------------|
| **FOI officer (operator)** | A clear decision point with enough evidence to approve, reject, or modify a draft response confidently — not raw agent output |
| **Oversight / audit** | A complete, attributed record of what the AI produced and what the human decided |

---

## 3. Functional requirements

### 3.1 Agent pipeline

The system must implement a multi-agent pipeline with at least the following distinct roles, orchestrated by a supervisor:

| Agent role | Input | Required output |
|------------|-------|-----------------|
| **Triage** | FOI request text | Classification: topic, complexity, summary, confidence score (0–1) |
| **Compliance** | Request text + triage classification | Applicable FOIA exemptions with citations to retrieved policy excerpts; a recommendation (release / partial release / withhold) |
| **Response drafting** | Request text + compliance findings | Draft FOI response letter |
| **Supervisor** | All of the above | Sequences agents, enforces HITL gate, writes outputs |

The pipeline must process a folder of FOI request files in batch and support single-file processing.

### 3.2 RAG integration (mandatory)

The compliance agent must:
- Retrieve relevant excerpts from policy documents stored in **ChromaDB** before making any exemption recommendation
- Cite at least one retrieved policy excerpt in the exemption analysis
- Never make an exemption assertion it cannot ground in a retrieved excerpt

### 3.3 Human-in-the-loop gate (mandatory)

The approval gate must:
- Pause pipeline execution and present evidence to the operator before any decision is finalised
- Display: retrieved policy excerpts, triage classification, compliance reasoning, draft response — the draft must be labelled as AI-generated
- Accept an **approve / reject / modify** decision from the operator
- Require the operator to actively choose — no auto-approval, no timeout-to-approve, no default decision
- On **modify**: accept the operator's revised text and record both the original AI draft and the override
- On **reject**: record the rejection as a decision on the audit trail; no response is released
- Write a timestamped decision log entry for every decision, including operator identity and the IDs of policy excerpts displayed at the gate

### 3.4 Error handling (mandatory)

For each pipeline stage:
- If the agent returns an API error, unparseable response, or empty result, log the error and continue with a safe fallback — do not crash
- The fallback for the compliance agent must default to **withhold** (not release) — fail safe
- A failure in one request must not abort batch processing of remaining requests

### 3.5 Cost tracking (mandatory)

Every LLM call must log:
- Model used
- Prompt token count
- Completion token count
- Estimated cost in USD

An end-of-run summary must print: per-agent and per-request breakdown of model, tokens, and estimated cost; run total.

### 3.6 Structured output (mandatory)

Each processed request must produce a JSON result file containing at minimum:
- Triage classification
- Exemption findings with policy citations
- Draft response text
- Human decision (approve / reject / modify) and operator identity
- Cost breakdown

---

## 4. Governance requirements

### 4.1 Audit trail

The audit trail must be:
- Append-only — never overwritten across runs
- Attributed — every entry carries operator identity (a non-empty named individual or role)
- Complete — records both the AI's original recommendation and any operator override
- Traceable — includes references to the specific policy excerpts shown to the operator at the gate

### 4.2 Personal data — s.40 FOIA 2000

When the compliance agent identifies that the personal data exemption (s.40) applies, the response drafting agent must be instructed not to name or describe identifiable individuals in the draft response. Paraphrasing retrieved content that could identify someone is not acceptable.

Rationale: a draft letter disclosing third-party personal data constitutes a reportable data breach under UK GDPR / DPA 2018 regardless of whether the officer notices before approving. (Source: `docs/research/foi-landscape-synthesis.md §2.3`)

### 4.3 Third-party notification flag

When the compliance agent identifies that s.41 (information provided in confidence) applies, or that s.40(2) obligations may require third-party notification before disclosure, this must be surfaced as a visible warning at the HITL gate. The operator decides the action.

### 4.4 AI_LOG.md

An AI assistance log must be maintained throughout development with a minimum of three entries covering: Date, Task, What AI Generated, What You Changed + Why. Entries must cover at least one doc/process task and at least two code tasks.

---

## 5. Quality requirements

### 5.1 Accuracy

- Triage classification must be consistent with the policy corpus for known sample requests
- Exemption findings must correctly identify applicable sections for the sample requests
- Every exemption claim must cite a retrieved excerpt; unsupported assertions are a failure

### 5.2 Reliability

- The system must handle without crashing: API failures, rate limit errors, unparseable LLM responses, empty retrieval results, malformed/empty request files
- Malformed or ambiguous requests must be flagged for operator review rather than rejected outright (FOIA duty to assist — s.16 FOIA 2000)

### 5.3 Generalisation

- The system must be built for the use-case, not tuned to the visible sample requests
- Performance on requests not seen during development is the meaningful measure of success

---

## 6. Scope

### In scope (MVP — required for "Excellent" on all rubric axes)

| Rubric axis | Deliverable |
|-------------|-------------|
| **Automation value** | Full triage → compliance (RAG) → response pipeline; evidence-backed exemption analysis |
| **Reliability** | Per-stage safe fallbacks; batch isolation; error logging; malformed input handling |
| **Governance** | Rich-evidence HITL gate; A/R/M decisions; timestamped, operator-attributed, append-only audit trail |
| **Cost awareness** | Per-call, per-agent, per-request, and run-total cost breakdown |

### Minimum Viable Submission (floor, not target)

A submission meeting the rubric minimum must demonstrate:
1. Triage agent classifies at least one FOI request with structured output
2. Compliance agent retrieves at least one policy chunk from ChromaDB and cites it
3. HITL gate pauses, displays evidence, and accepts an A/R/M decision
4. End-of-run cost summary with model and token breakdown per call

### Out of scope for MVP

The following are not required for "Excellent" but add further value:
- Citation verification (post-compliance check) → see `stretch-spec-agent-tom.md`
- Triage override + pipeline re-run at HITL gate → `stretch-spec-agent-tom.md`
- Policy document staleness warning → `stretch-spec-agent-tom.md`
- Duplicate / similar request detection → `stretch-spec-agent-tom.md`
- ATRS record auto-generation → `stretch-spec-agent-tom.md`
- Production deployment, security hardening, bias monitoring → `production-spec-agent-tom.md`

---

## 7. Constraints

- **Vector store:** ChromaDB (brief-mandated)
- **Interface:** CLI (brief-mandated)
- **Data:** synthetic only — no real PII or real case data
- **Operator:** single human per run
- **LLM / embeddings:** tooling decisions — see `docs/architecture/tooling-agent-tom.md`

---

## 8. Acceptance criteria

The system is accepted as MVP-complete when:

- [ ] 3+ sample FOI requests process end-to-end without error
- [ ] Each request produces a correctly structured JSON result file
- [ ] The HITL gate displays retrieved chunks, classification, compliance reasoning, and the labelled AI draft before accepting a decision
- [ ] All three operator paths (approve, reject, modify) work and produce correct audit entries
- [ ] An API failure in one agent does not crash the pipeline
- [ ] A malformed or empty request file does not crash the pipeline
- [ ] The end-of-run cost summary correctly totals tokens and cost per agent and per request
- [ ] The audit trail is append-only across multiple runs
- [ ] When s.40 applies, the draft contains no named individuals from retrieved content
- [ ] AI_LOG.md contains ≥ 3 entries with all four required fields

---

## 9. Pipeline overview

```
 FOI request file
        │
        ▼
 ┌─────────────┐
 │   Triage    │  Classify: topic, complexity, summary
 └──────┬──────┘
        │
        ▼
 ┌─────────────────┐
 │  RAG retrieval  │  Retrieve policy excerpts from ChromaDB
 └────────┬────────┘
          │
          ▼
 ┌────────────────┐
 │  Compliance    │  Identify exemptions; cite retrieved excerpts;
 │                │  recommend release / partial / withhold
 └───────┬────────┘
         │
         ▼
 ┌───────────────┐
 │   Response    │  Draft FOI response letter
 └──────┬────────┘
        │
        ▼
 ┌──────────────┐
 │  HITL gate   │  Display evidence; operator A/R/M;
 │              │  write timestamped audit entry
 └──────┬───────┘
        │
        ▼
 output JSON + audit trail
```

Each stage: per-agent cost tracking, structured fallback on failure.
The supervisor is a deterministic orchestrator — not itself an LLM agent.

---

## 10. Triage confidence score (requirement)

The triage classification must include a confidence score (float, 0–1). At the HITL gate:
- The confidence score is displayed alongside the classification
- If confidence is below a configurable threshold, a warning banner is shown and the operator must enter a mandatory review comment before approving

Rationale: triage errors cascade downstream (wrong topic → wrong RAG query → wrong compliance analysis). Making low confidence visible and forcing a comment provides a forcing function without blocking the pipeline.

The threshold value is a configuration parameter (e.g. `TRIAGE_LOW_CONFIDENCE_THRESHOLD = 0.7`).

---

## 11. Resolved questions

| Question | Decision |
|----------|----------|
| Triage confidence score | Required; float 0–1; low-confidence triggers mandatory operator comment at HITL gate (see §10) |
| Non-FOI / garbled input | Triage classifies as `topic="unclear"`, sets `clarification_recommended=True`. Pipeline continues to HITL gate with warning. No auto-rejection (FOIA s.16 duty to assist). |
| RAG top-k | Default k=5, configurable. Profile on multi-exemption test case after chunk validation; adjust if coverage is thin. |
| Chunk size/overlap | Validate empirically before coding `rag.py` — see `docs/RAID-log-agent-tom.md` issue I7. |
| Retry strategy | Tenacity only, wrapping each agent function. No native `ChatAnthropic max_retries` used. |
| Chroma API pattern | Confirm via Context7 MCP before coding `rag.py` — see `docs/RAID-log-agent-tom.md` issue I8. |

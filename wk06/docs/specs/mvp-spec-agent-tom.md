# MVP Spec — FOI Multi-Agent CLI

**Author:** agent-tom
**Status:** Consolidated — gates implementation. Companion to `Agent-Jack-SPEC.md`.
**Date:** 2026-06-24
**Scope:** Requirements for "Excellent" on all four rubric axes. Anything not in this document is either in `stretch-spec-agent-tom.md` or `production-spec-agent-tom.md`.

---

## Scope table

| Rubric axis | What this spec delivers |
|-------------|------------------------|
| **Automation value** | Full triage → RAG → compliance → response pipeline; evidence-backed exemption analysis with mandatory citation grounding |
| **Reliability** | Structured fallbacks per step; retry with exponential backoff; circuit breaker; no crashes on API errors or malformed input; batch isolation |
| **Governance** | HITL gate with rich evidence display; mandatory operator decision (A/R/M); append-only audit trail with operator identity, evidence refs, and AI recommendation vs human decision |
| **Cost awareness** | Per-agent token + cost tracking; per-request breakdown in output JSON; end-of-run cost summary |

## Explicit out-of-scope for MVP

- Citation verification after compliance → `stretch-spec-agent-tom.md` S1
- Triage override with pipeline re-run at HITL → `stretch-spec-agent-tom.md` S2
- Policy staleness warning → `stretch-spec-agent-tom.md` S3
- Duplicate/similar request detection → `stretch-spec-agent-tom.md` S4
- Extended vexatious/malformed flagging → `stretch-spec-agent-tom.md` S5
- ATRS record generation → `stretch-spec-agent-tom.md` S6
- Bias monitoring, drift detection, precedent store, multi-department routing → `production-spec-agent-tom.md`

---

## 1. Pipeline requirements

The system must implement four sequential stages over a shared case record:

| Stage | Must produce |
|-------|-------------|
| **Triage** | Topic classification, complexity rating, one-line summary, classification confidence |
| **Compliance (RAG)** | Exemptions found (each with section, rationale, citation, verbatim quote), recommendation (release/partial_release/withhold), chunk IDs of evidence used |
| **Response** | A formal FOI response letter grounded only in the compliance findings |
| **HITL gate** | An operator decision (approve/reject/modify) with timestamp, operator attribution, and evidence references |

No implementation detail (file layout, prompt text, model IDs) belongs in this spec — those are in `architecture/` and `plans/`.

### Triage requirements

- Must classify: topic (one of: `finance_spending`, `staffing_hr`, `procurement_commercial`, `internal_deliberations`, `personal_data`, `other`), complexity (`low`/`medium`/`high`), and a one-sentence summary.
- Complexity describes handling effort and risk, not a releasability pre-judgement (release decisions are the compliance stage's responsibility).
- Must produce a confidence score (0–1).
- Must set `clarification_recommended: bool` and `clarification_reason` when the request is ambiguous, misquotes legislation, or is of unclear scope. A flagged request is **never auto-rejected** — it proceeds through the pipeline; the operator makes the final call.
- **Failure fallback:** `topic="unknown"`, `complexity="high"`, `clarification_recommended=True` — conservative, forcing human review.

### Compliance requirements

- Must retrieve relevant policy corpus excerpts before reasoning (RAG, not memory).
- Every exemption claim must cite at least one retrieved chunk and carry a verbatim supporting quote — no grounded citation, no assertion.
- Where multiple exemptions apply, each has its own basis.
- For qualified exemptions (s36, s43), must apply the public interest test. For s36, must note the qualified-person opinion (s36(5)) precondition as conditional.
- Must set `third_party_notification_required: bool` when s41 or s40(2) exemptions may require notifying a third party before disclosure.
- **Failure fallback:** recommend `"withhold"` — never guess, never silently release.

### Response requirements

- Draft letter must be grounded **only** in the compliance findings — no claims beyond what the compliance stage found.
- When `"s40" in exemptions_found`, the response **must not name or describe identifiable individuals** (see §6 below).
- **Failure fallback:** a minimal templated holding response flagged for manual completion.

---

## 2. HITL gate requirements

- Must display rich evidence before accepting a decision: retrieved policy chunks (with source and similarity score), classification, compliance reasoning, and the draft response — explicitly labelled "AI-generated draft".
- Must support three decision types: **Approve** (draft sent as-is), **Reject** (pipeline halts for that request; no response released; rejection is logged), **Modify** (operator edits the draft; both AI original and operator version are preserved in the audit trail).
- **No auto-approve.** No default decision. No timeout-to-approve. The operator must actively choose. (Lesson from the Robodebt scheme: a rubber-stamp checkpoint amplifies AI error at scale.)
- Every decision must be logged with: ISO 8601 UTC timestamp, operator identity (non-empty string), the AI's original recommendation, the human's decision, and references to the evidence chunks shown.
- When `clarification_recommended` is True, a warning banner must be shown before the decision prompt.
- When `third_party_notification_required` is True, a warning banner must be shown before the decision prompt.
- Operator identity must be captured for every decision. An empty operator identity is an error, not a default.
- In batch mode: one rejected or failed request must not abort the run; processing continues with the next request.

---

## 3. Audit trail requirements

- Append-only: the audit trail file is never overwritten or reset across runs. Each run appends to the same file.
- Every entry is operator-attributed (non-empty operator string required).
- Every entry captures: the AI's original recommendation (compliance recommendation field) and any operator override (decision type + modification content).
- Rejected requests are also logged — rejection is a decision on record, not an absence.
- Each entry carries `cost_usd`: total pipeline cost for that request.
- Each entry captures `triage_topic` and `triage_confidence` for subsequent performance monitoring.
- When decision is `"rejected"`, a `rejection_reason` field is captured (optional free text, but the field is present).

---

## 4. Cost tracking requirements

- Every LLM call logs: model ID, prompt tokens, completion tokens, estimated cost in USD.
- Cost tracking must use Anthropic (Claude) pricing — not the OpenAI pricing in the starter reference.
- Per-agent, per-request, and run-total cost breakdowns must be produced.
- An end-of-run cost summary must be displayed after batch processing.

---

## 5. s.40 personal data requirement

When the compliance stage identifies the s40 (personal data) exemption, the response stage **must not** name or describe identifiable individuals in the draft letter. Where personal data is relevant, it must be referred to in aggregate or anonymised terms only (e.g. "staff members", not named individuals). This requirement is not optional — a draft that names individuals whose data is protected under s.40 could constitute a data breach.

---

## 6. Additional required fields

Beyond the base pipeline, the following fields are required by this spec:

| Field | Model | Purpose |
|-------|-------|---------|
| `clarification_recommended: bool` | `TriageResult` | Flag ambiguous/misquoted requests for operator attention |
| `clarification_reason: str \| None` | `TriageResult` | Brief explanation of why clarification is recommended |
| `third_party_notification_required: bool` | `ComplianceResult` | Flag s41/s40(2) third-party notification obligations |
| `triage_topic: str` | `AuditEntry` | Captures topic at decision point for performance monitoring |
| `triage_confidence: float` | `AuditEntry` | Captures confidence at decision point |
| `rejection_reason: str \| None` | `AuditEntry` | Operator's stated reason when decision is "rejected" |
| `cost_usd: float` | `AuditEntry` | Total pipeline cost for this request |

Exact schema definitions (Python/Pydantic) live in `plans/implementation-agent-tom.md` — that is the single source of truth for field types and defaults.

---

## 7. Reference documents

- `docs/specs/Agent-Jack-SPEC.md` — authoritative for agent behavioural contracts, domain glossary (§3), governance principles, evaluation criteria, and scope boundaries. Read this alongside the present spec.
- `docs/specs/stretch-spec-agent-tom.md` — requirements for S1–S9 stretch goals; implement after MVP is working.
- `docs/specs/production-spec-agent-tom.md` — real deployment requirements; out of scope for the hackathon.
- `docs/architecture/system-design-agent-tom.md` — pipeline topology decisions and HITL design rationale.
- `docs/architecture/tooling-agent-tom.md` — technology choices and research findings.
- `docs/plans/implementation-agent-tom.md` — all implementation detail (schemas, file layout, code).

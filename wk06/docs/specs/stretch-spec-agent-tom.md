# Stretch Spec — FOI Multi-Agent CLI

**Author:** agent-tom
**Status:** Reference — implement after MVP is complete and working
**Date:** 2026-06-24
**Prerequisite:** `mvp-spec-agent-tom.md` must be fully implemented before any stretch goal is started.
**Source grounding:** `docs/research/foi-landscape-synthesis.md` (S1–S9) plus team review.

These goals add meaningful value beyond the hackathon rubric's minimum. Tier 1 items are
architecturally close to the MVP. Tier 2 items require more effort. Tier 3 items are
significant enough to be their own work items.

Implementation detail (code, schema extensions, effort estimates) lives in `plans/implementation-agent-tom.md`. This document states **what** each stretch goal must do — not how.

---

## Tier 1 — High value, architecturally close

### S1. Citation Verification (Post-Compliance Check)

**Why:** LLMs hallucinate 13–21% of legal citations even with RAG (arXiv 2606.00898). An
incorrect exemption section number in a draft letter is legally indefensible.

**Requirements:**
- After compliance returns its result, the system must check whether each cited section reference (e.g. `s.43`, `s.40`) appears verbatim in the text of at least one retrieved chunk used as evidence.
- Any section reference not found verbatim in the retrieved chunks must be recorded as an unverified citation.
- Unverified citations must be surfaced to the operator at the HITL gate as a prominent warning banner before the decision prompt.
- The pipeline must **not** be blocked by unverified citations — they are surfaced for human review; the operator decides how to proceed.
- The operator must be able to approve, reject, or modify regardless of unverified citations.

---

### S2. Triage Override with Pipeline Re-Run

**Why:** Triage errors cascade downstream (wrong topic → wrong RAG query → wrong compliance
analysis → wrong draft). The MVP HITL gate is review-only; operators cannot correct a
mis-classification without re-running the whole pipeline manually.

**Requirements:**
- At the HITL gate, before the A/R/M decision, the operator must be able to indicate that the triage classification is incorrect.
- If the operator corrects the classification, they must be able to specify the correct topic and/or complexity.
- The operator's classification supersedes the AI's — the pipeline must not re-call the triage LLM for the override.
- After a triage override, stages 2–4 (RAG retrieve, compliance, response) must re-run with the corrected classification.
- The HITL gate must then display the new compliance analysis and draft.
- The audit trail must record both the AI's original triage and the operator's override, and must flag that a triage override occurred.

---

### S3. Policy Document Staleness Warning

**Why:** The RAG store is indexed once at setup. FOI exemption guidance changes. Compliance
reasoning from outdated policy documents could cite superseded guidance.

**Requirements:**
- When the system indexes documents, it must record the timestamp of that index operation.
- When processing requests, the system must check the age of the current index.
- If the index age exceeds a configurable threshold (default: 30 days), the system must display a warning before processing begins.
- The warning must identify the age of the index and suggest a re-index command.
- Processing must **not** be blocked by a stale index warning — it is advisory only; the operator decides whether to re-index first.
- The staleness threshold must be configurable without code changes (environment variable or config).

---

## Tier 2 — Meaningful additions, moderate effort

### S4. Duplicate / Similar Request Detection

**Why:** Real FOI teams waste significant effort re-processing requests that are nearly
identical to previously answered ones. Surfacing a past decision before the pipeline
runs saves processing cost and promotes consistent responses.

**Requirements:**
- Before running the triage pipeline, the system must check whether the incoming request is semantically similar to any previously processed request.
- If a sufficiently similar past request is found (above a configurable similarity threshold), the system must surface a summary of that past decision to the operator at the HITL gate: the reference ID, date, decision, and exemptions applied.
- The pipeline must still run fully — duplicate detection informs the operator; it does not skip processing.
- After an `approved` or `modified` decision, the request must be added to the similarity index for future comparisons.
- Rejected requests must not be added to the precedent index.
- The similarity threshold must be configurable.

---

### S5. Extended Vexatious / Malformed Request Flagging

**Why:** The ICO's May 2026 guidance identifies AI-drafted requests that misquote
legislation as a rising operational problem. The MVP `clarification_recommended` flag is
a start; this stretch goal adds structured detection categories.

**Requirements:**
- The triage stage must detect and classify the following flag types, in addition to the existing `clarification_recommended` boolean:
  - `malformed_legislation` — the request cites a non-existent FOIA section (e.g. FOIA 2000 sections run to s.88; anything citing s.89+ is malformed)
  - `ambiguous_scope` — no time period, no subject area, or other missing scope element
  - `overbroad` — unreasonably broad request (e.g. "all internal communications ever sent")
  - `bulk_identical` — pattern matching bulk/identical requests (requires S4 to be meaningful)
  - `wrong_body` — request is clearly addressed to a different public authority
- The existing `clarification_recommended: bool` must remain as the top-level flag (set True whenever any flag is present).
- The specific flags must add specificity beyond the top-level boolean, for operator guidance.
- The HITL display must list detected flags when any are present.

---

### S6. ATRS Record Auto-Generation

**Why:** Any public authority deploying a tool with "significant influence on a
decision-making process with public effect" must publish an ATRS (Algorithmic Transparency
Recording Standard) record before going live. This has been mandatory for all central
government departments since February 2024.

**Requirements:**
- The system must provide a CLI subcommand (e.g. `atrs-record`) that generates a partially pre-filled ATRS Tier 1 record.
- The generated record must be written to a file in the output directory.
- The record must be populated from system metadata where possible: tool name, description, date, operator contact (from config), human oversight mechanism, third-party suppliers (Anthropic, HuggingFace, ChromaDB), audit trail location.
- The generated record must clearly note which Tier 2 fields (bias testing, performance metrics, training data description, equality impact assessment) require manual completion before submission.
- The command must not make any LLM calls — pure template substitution from system metadata.
- The record must include a link to the ATRS submission register.

---

## Tier 3 — Larger scope, plan as future work

### S7. Precedent Store

**What it must do:** After a request is approved or modified, persist the decision as a
precedent entry. Before the compliance stage runs, retrieve semantically similar past
decisions as few-shot examples to promote consistency.

**Why it is Tier 3:** Requires careful design to avoid poisoning the compliance agent with
past errors. The retrieval logic (how many examples, how to weight recency vs similarity)
needs empirical testing. Architecturally it adds a data dependency between runs that
complicates testing and reproducibility. Depends on S4.

---

### S8. Multi-Department Routing

**What it must do:** Detect when an FOI request crosses departmental boundaries and flag
it for routing to the correct team rather than processing immediately.

**Why it is Tier 3:** Requires a maintained taxonomy of departmental areas and
sub-authorities. Without that taxonomy, detection is speculative. Out of scope for a
single-department hackathon demo.

---

### S9. Proactive Disclosure Flagging

**What it must do:** After a request is approved, assess whether the response could be
pre-emptively published to a disclosure log to reduce future duplicate requests on the
same topic. Flag as a proactive disclosure candidate in the audit entry.

**Why it is Tier 3:** The decision to publish proactively requires legal and policy
judgement beyond the compliance agent. The flag would need to be acted on by a separate
publication workflow. Valuable but well beyond hackathon scope.

---

## Stretch Goal Summary

| ID | Goal | Tier | Dependency |
|----|------|------|------------|
| S1 | Citation verification | 1 | None |
| S2 | Triage override + re-run | 1 | None |
| S3 | Policy staleness warning | 1 | None |
| S4 | Duplicate detection | 2 | None |
| S5 | Extended vexatious/malformed flagging | 2 | None (S4 for `bulk_identical`) |
| S6 | ATRS record auto-generation | 2 | None |
| S7 | Precedent store | 3 | S4 |
| S8 | Multi-department routing | 3 | External taxonomy |
| S9 | Proactive disclosure flagging | 3 | External workflow |

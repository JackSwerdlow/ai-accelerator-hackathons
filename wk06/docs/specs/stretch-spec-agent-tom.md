# Stretch Spec — FOI Intelligent Automation System

**Author:** Agent-Tom  
**Date:** 2026-06-24  
**Status:** Draft — implement after MVP is complete and accepted  
**Sources:** `context/slides/hackathon-intelligent-automation-system.html` (brief stretch goals); `docs/research/foi-landscape-synthesis.md`

---

## Overview

Stretch goals add value beyond the rubric's "Excellent" threshold. They are not required to pass but demonstrate deeper thinking and improve the system's usefulness in a real operational context.

The brief explicitly identifies four stretch goals. Additional goals arise from FOI domain research. Both are listed here as requirements — implementation detail lives in `docs/plans/`.

**Prerequisite:** MVP spec (`mvp-spec-agent-tom.md`) must be fully implemented and accepted before any stretch goal is started.

---

## Brief-specified stretch goals

### S-B1. Redaction agent

**What:** Add an agent that identifies and masks personal information in draft responses before they reach the HITL gate.

**Acceptance criteria:**
- The agent scans the draft response and masks: names, addresses, email addresses
- Masked content is replaced with a consistent placeholder (e.g. `[REDACTED]`) rather than deleted, so the operator can see what was removed
- A redaction schedule is produced alongside the draft: one entry per redaction, recording the category of data removed and the applicable exemption section
- Where the compliance agent has identified s.40, the redaction agent is automatically triggered
- If the agent errors, the draft is flagged "redaction incomplete — manual check required" rather than released unredacted

### S-B2. Batch processing with progress display

**What:** When processing a folder of requests, display progress information throughout the run.

**Acceptance criteria:**
- Per-request status is displayed as each request completes (e.g. `[3/8] request-003.txt — approved`)
- Cumulative cost is shown after each request
- Estimated time remaining is displayed based on elapsed time per request
- The progress display does not interfere with the HITL gate interaction

### S-B3. Structured audit log

**What:** Record every agent decision, human override, and cost entry as structured JSON, suitable for compliance reporting.

**Acceptance criteria:**
- One JSON object per event (agent output, human decision, cost entry)
- Append-only: the log survives across runs and is never truncated or overwritten
- Each entry is timestamped and attributed (operator identity where applicable)
- The log is complete enough to reconstruct the full decision history for any request

Note: this overlaps with the MVP audit trail requirement (§4.1 of `mvp-spec-agent-tom.md`). If the MVP audit trail already satisfies these criteria, S-B3 is met by the MVP. If not, the gap must be closed here.

### S-B4. Model fallback

**What:** If the primary LLM returns an error or exceeds a per-call cost threshold, automatically retry on a cheaper/alternate model.

**Acceptance criteria:**
- Each agent has a configured primary model and a fallback model
- If a call to the primary model errors, the system retries automatically on the fallback model
- If a single call would exceed a configurable cost threshold, it retries on the fallback model instead
- The fallback event is recorded in the audit trail (which model was used, and why it fell back)
- The operator is not required to intervene for a fallback — it is automatic

---

## Research-derived stretch goals

The following goals are not in the brief but are identified from FOI domain research (`docs/research/foi-landscape-synthesis.md`) as high-value additions.

### S-R1. Citation verification

**What:** After the compliance agent produces exemption findings, verify that cited section numbers actually appear in the retrieved policy excerpts.

**Why:** Research indicates LLMs hallucinate 13–21% of legal citations even with RAG. An incorrect exemption section number in a draft response is legally indefensible.

**Acceptance criteria:**
- For each exemption section cited (e.g. "s.43"), the system checks whether that reference appears verbatim in the retrieved chunk text
- Any citation not found in retrieved text is flagged as unverified
- Unverified citations are surfaced prominently at the HITL gate as a warning banner
- The operator can still approve with an unverified citation — surfacing is mandatory, blocking is not

### S-R2. Triage override with pipeline re-run

**What:** Allow the operator to correct the triage classification at the HITL gate, triggering a re-run of compliance and response with the corrected classification.

**Why:** Triage errors cascade — a wrong topic sends the wrong RAG query, which produces wrong exemption analysis. Currently the operator can only accept the mis-classified output.

**Acceptance criteria:**
- At the HITL gate, before making an A/R/M decision, the operator can view and edit the triage classification (topic, complexity)
- If the classification is changed, compliance and response agents re-run with the corrected classification
- The original and corrected classifications are both recorded in the audit entry
- The re-run produces a new draft which is then presented for the A/R/M decision

### S-R3. Policy document staleness warning

**What:** Warn the operator if the indexed policy documents are older than a configurable threshold.

**Why:** The compliance agent reasons from whatever is in the ChromaDB index. Outdated guidance leads to incorrect exemption analysis without any visible signal.

**Acceptance criteria:**
- The system records when the policy corpus was last indexed
- Before processing any request, if the index age exceeds a configurable threshold (e.g. 30 days), a visible warning is printed
- The warning names the index age and prompts the operator to consider re-indexing
- Processing is not blocked — the warning is informational

### S-R4. Duplicate / similar request detection

**What:** Before running the full pipeline on a new request, check whether a similar request has been processed before and surface the past decision for reference.

**Why:** FOI teams waste effort re-processing near-duplicate requests. A past decision on a similar topic provides a consistency reference.

**Acceptance criteria:**
- The new request is compared against past processed requests using embedding similarity
- If a past request exceeds a configurable similarity threshold, it is surfaced at the start of processing (or at the HITL gate) as a reference
- The past decision (topic, exemptions, outcome) is shown — the operator is not required to follow it
- The full pipeline still runs; the past decision is a reference, not a shortcut

---

## Prioritisation

| ID | Goal | Source | Priority |
|----|------|--------|----------|
| S-B1 | Redaction agent | Brief | High — brief-specified |
| S-B2 | Batch progress display | Brief | High — brief-specified |
| S-B3 | Structured audit log | Brief | High — brief-specified (may be met by MVP) |
| S-B4 | Model fallback | Brief | High — brief-specified |
| S-R1 | Citation verification | Research | High — addresses HIGH risk from research |
| S-R2 | Triage override + re-run | Research | Medium — improves robustness |
| S-R3 | Policy staleness warning | Research | Low — small effort, useful signal |
| S-R4 | Duplicate detection | Research | Low — adds value but adds complexity |

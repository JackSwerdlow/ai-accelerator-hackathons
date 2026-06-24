# Page Cache: AI FOI Request Triage — Privacy Consultancies at Scale

**Source:** https://vidizmo.ai/blog/ai-foi-request-triage-privacy-consultancies  
**Retrieved:** 2026-06-24  
**Relevance:** Describes production-grade FOI triage automation in commercial use. The six-stage triage model is more comprehensive than our current single-stage triage agent and surfaces several gaps in our design.

---

## The Six Triage Stages (Before Redaction Begins)

Industry practice identifies six distinct steps that occur *before* a single line is redacted:

| Stage | What happens | AI approach |
|-------|-------------|-------------|
| 1. Request classification | Categorise by type (general, personal, repeat, vexatious) | NLU / text classification |
| 2. Entity extraction | Identify names, addresses, organisations, dates across records | Named-entity recognition (NER) |
| 3. Duplicate detection | Group near-duplicate content (especially email reply threads) | Document clustering |
| 4. Third-party surfacing | Surface names in records requiring statutory notification | NER + filtering |
| 5. Effort estimation | Estimate workload from record count, file types, entity density | Regression / heuristics |
| 6. Sensitivity flagging | Flag content referencing litigation, executives, complaints, media | Keyword + semantic search |

**Our current design covers stage 1 (classification) only.** Stages 2–6 are unaddressed.

## Critical Finding: Triage Errors Cascade Downstream

> *"Triage errors cascade downstream more expensively than redaction errors."*

If a request is misclassified at triage, the error propagates through compliance analysis and draft generation, producing a fundamentally wrong output. Getting classification right — and making it easy for operators to correct it — is the highest-leverage investment.

## What AI Cannot Do (Must Remain Human)

AI cannot:
- Apply the statutory framework to a specific record
- Determine which exemptions apply to specific content
- Assess the public interest balance
- Evaluate legal privilege claims
- Make the final release/withhold decision

These remain with the operator at the HITL gate. The article is explicit: **"full automation without human judgment loses defensibility under oversight body review."**

## Failure Modes Documented

- Manual triage doesn't scale across multi-client portfolios due to "tribal knowledge requirements"
- Surge periods create upstream backlogs that cascade to downstream redaction teams
- Triage outputs must feed into redaction with shared audit logging to avoid duplication errors

## Integration Note

The VIDIZMO architecture feeds triage outputs (in-scope records, third-party lists, PII categories, effort estimates) **directly into the redaction stage** via REST API, with shared audit logging and entity detection. This is a more integrated architecture than our current design, which treats triage, compliance, and response as largely independent agents.

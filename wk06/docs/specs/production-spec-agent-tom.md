# Production Spec — FOI Multi-Agent CLI

**Status:** Out of scope for hackathon — reference for real deployment  
**Date:** 2026-06-24  
**Prerequisite:** `mvp-spec-agent-tom.md` fully implemented; stretch goals evaluated

This document captures what a production deployment of this system would require beyond
the hackathon MVP. None of these items are needed to score "Excellent" at the hackathon,
but a public authority deploying this system in production would need to address all of
them. They are documented here to inform architecture decisions and avoid traps during MVP
design (e.g. the audit trail append-only design is already correct for production).

---

## 1. Regulatory Compliance

### 1.1 ATRS Registration (Legal Requirement)

Any public authority deploying a tool with "significant influence on a decision-making
process with public effect" must publish an ATRS record before going live. This has been
mandatory for all central government departments since February 2024.

**What is required:**
- **Tier 1 record:** Tool name, description, scope, significant influence statement,
  human oversight mechanism, third-party suppliers, publication date. Must be submitted
  to the ATRS register at https://www.gov.uk/government/collections/algorithmic-transparency-recording-standard-hub
- **Tier 2 record:** Additionally requires bias testing results, performance metrics,
  training data description, equality impact assessment.

**Hackathon shortcut:** `stretch-spec-agent-tom.md S6` auto-generates a Tier 1 draft. Tier 2 requires
human completion and legal review. Do not deploy to production without completing both.

### 1.2 Data (Use and Access) Act 2025 — Automated Decision Rights

The DUAA 2025 (in force February 2026) creates new individual rights around
AI-assisted decisions with "legal or similarly significant effects." FOI decisions
almost certainly qualify.

**Data subjects have the right to:**
- Be informed that AI contributed to the decision affecting them
- Make representations before the decision is finalised
- Request human review of the AI output

**What the MVP already covers:** The audit trail records operator identity and the
full AI-generated content shown to them (satisfying the "human review" requirement).
The HITL gate makes the AI's role explicit to the operator.

**What production adds:**
- The FOI response letter should include a disclosure line: "This response was drafted
  with AI assistance and reviewed and approved by [operator name]."
- A data subject rights procedure must exist (not in the system — organisational).
- Evidence of the AI's role must be stored in the audit trail for the life of the record.

### 1.3 UK GDPR / DPA 2018 — s.40 Personal Data at Scale

The MVP s.40 handling (extra instruction to response agent) is a minimum. At production
scale, systematic personal data mishandling constitutes a notifiable data breach.

**Additional production requirements:**
- Data Protection Impact Assessment (DPIA) before deployment
- Named Data Protection Officer oversight
- Retention policy for audit trail entries (how long to keep per ICO guidance)
- Mechanism for data subjects to request audit entries relating to them under DSAR
- Secure storage for `output/` and `chroma_db/` (access controls, encryption at rest)

---

## 2. Algorithmic Governance

### 2.1 Bias and Drift Monitoring

The UK AI Playbook (Principle 5) and ATRS Tier 2 require ongoing performance monitoring
after deployment. The hackathon MVP has no mechanism for this.

**Metrics to track per-deployment:**
- Triage classification accuracy (requires labelled ground truth or operator feedback)
- Operator override rate: `sum(operator_overrode_triage) / total_requests`
- Operator modification rate: `sum(decision == "modified") / total_requests`
- Operator rejection rate: `sum(decision == "rejected") / total_requests`
- Compliance recommendation distribution by topic (are some topics systematically over/under-exempted?)
- Citation verification failure rate (once S1 is implemented)

**How to implement:**
- Existing audit trail provides the raw data for all of the above except triage accuracy.
- Add a `main.py report` subcommand that reads `output/audit_trail.jsonl` and prints
  summary statistics and a per-topic breakdown.
- Triage accuracy requires a ground-truth labelling step (human review of a sample).

### 2.2 Performance Benchmarking

Before production deployment, establish a benchmark on a labelled test set:
- At least 50 representative FOI requests (range of topics, complexity, exemption types)
- Ground truth: correct exemptions, correct recommendation for each
- Measure: compliance recommendation accuracy, exemption recall/precision, citation accuracy
- Re-run benchmark on each major update

### 2.3 Equality Impact Assessment

Required before deploying a tool that affects public-facing decisions. Must assess
whether the AI's behaviour differs systematically across protected characteristics.
In the FOI context this means:
- Are requests from certain demographic groups (identifiable from request language/topic)
  more likely to be recommended for withholding?
- Does triage confidence differ by request topic in ways that disadvantage certain types
  of requesters?

This is largely an organisational/policy exercise, not a software task.

---

## 3. Security and Infrastructure

### 3.1 Secrets Management

The hackathon uses `.env` files for API keys. Production requires:
- Secrets management service (e.g. AWS Secrets Manager, Azure Key Vault, HashiCorp Vault,
  or GDS Secrets Management)
- No API keys in environment variables on shared systems
- Rotation policy for `ANTHROPIC_API_KEY`
- Audit log of secret access (separate from application audit log)

### 3.2 Containerisation and Deployment

The hackathon runs locally on the developer's machine. Production deployment requires:
- Docker container (or equivalent) with pinned dependencies and locked `requirements.txt`
- CI/CD pipeline: automated tests on every commit; container image build on merge to main
- Container registry (e.g. GCR, ECR, or government container registry)
- Deployment target: cloud VM, Kubernetes, or serverless — depends on department infrastructure
- Network policy: restrict outbound calls to `api.anthropic.com` only; HuggingFace
  model downloaded into the container image at build time (no runtime outbound for
  embeddings)

### 3.3 Access Controls and Audit

Production operator access requires:
- Authentication (SSO / Active Directory — not just an `OPERATOR_ID` env var)
- Role-based access control: who can process requests, who can view audit trail, who
  can re-index policy documents
- Tamper-evident audit trail: `output/audit_trail.jsonl` should be write-protected and
  ideally stored in an append-only log service (e.g. CloudTrail, GCP Audit Logs)
- Backup and restore procedures for `chroma_db/` and `output/`

### 3.4 Availability and Rate Limit Management

Production systems handling real FOI volumes (UKHSA processes ~500 FOI requests per year;
large departments 2,000+) must account for:
- Anthropic API rate limits at scale — consider request queuing rather than on-demand
  sequential processing
- SLA for response time: the system adds latency; operators need to know expected
  processing time per request
- Graceful degradation: if the Anthropic API is unavailable, the system should queue
  requests rather than fail silently

---

## 4. Full Six-Stage Triage (VIDIZMO Production Model)

The MVP triage agent performs Stage 1 (classification) only. A production system
addressing the full VIDIZMO six-stage model requires additional agents or processing steps:

| Stage | Current MVP status | Production requirement |
|-------|--------------------|----------------------|
| 1. Request classification | ✓ Implemented | Extend with S5 flagging |
| 2. Entity extraction | ✗ Not implemented | NER over request text and related records |
| 3. Duplicate detection | ✗ Not implemented | S4 (stretch) + precedent store (S7) |
| 4. Third-party surfacing | ✗ Not implemented | NER + cross-reference against known third parties |
| 5. Effort estimation | ✗ Not implemented | Heuristic: record count × complexity weighting |
| 6. Sensitivity flagging | Partial (`clarification_recommended`) | Structured detection across litigation/media/exec |

Stages 2 and 4 require Named Entity Recognition — either a local NER model or an
additional LLM call. Stage 5 (effort estimation) requires the system to know how many
source documents are involved in the response, which depends on the records management
context.

---

## 5. Case Management Integration

The hackathon system processes standalone `.txt` files. Production FOI systems are
integrated with case management platforms:

- **GovDesk / Civica FOI Pro / Octopus**: departmental case management tools that manage
  the FOI workflow (receipt, acknowledgement, deadline tracking, correspondence, closure)
- **What integration requires:** REST API to pull request text, push draft responses,
  update case status; OAuth2 for authentication; webhook for new request notifications
- **What this means for architecture:** `main.py` becomes an API service (FastAPI or
  similar), not a CLI; the HITL gate becomes a web interface

This is a significant architectural change. The CLI architecture chosen for the hackathon
is appropriate for a standalone tool but would need substantial redesign for case
management integration.

---

## 6. Knowledge Management

### 6.1 Policy Document Management

The hackathon uses a static folder of `.txt` policy documents. Production requires:
- A governed process for adding, updating, and retiring policy documents in the RAG store
- Versioning: policy chunks should carry a version reference so the audit trail records
  which version of guidance was in effect when the decision was made
- Re-indexing workflow: who can trigger a re-index, what quality check runs after
- Integration with the document management system (e.g. SharePoint, Confluence) used by
  the authority to manage its policy library

### 6.2 FOIA Exemption Knowledge Graph (Stretch of a Stretch)

Research (arXiv 2606.00898) shows that cross-referencing exemption numbers against a
structured taxonomy significantly reduces LLM citation hallucination compared to flat RAG.

A production knowledge graph would represent:
- FOIA 2000 sections and subsections as nodes
- Relationships: "requires public interest test", "absolute exemption", "qualified exemption"
- Cross-references to UK GDPR articles (for s.40)
- ICO guidance documents linked to section nodes

This would replace or augment the flat-text RAG approach for exemption reasoning.
Significant effort; likely a standalone workstream.

---

## 7. Operator Training and Change Management

The arXiv 2512.02774 study found that the top barrier to AI adoption in FOI teams is
**"training shortcomings — staff lack expertise to oversee and validate AI-driven outputs."**
No amount of technical investment overcomes this without:

- Operator training on FOIA exemptions (to spot compliance errors)
- Training on AI hallucination risks and how to use the evidence display
- Clear escalation path: when to escalate to a senior officer or legal team
- Guidance on not rubber-stamping AI outputs (Robodebt risk — see
  `docs/research/foi-landscape-synthesis.md §2.5`)
- Review of the first 200 processed requests by a senior officer before routine
  unmonitored use

---

## Summary: Hackathon vs Production

| Area | Hackathon MVP | Production requirement |
|------|---------------|----------------------|
| Regulatory | HITL gate satisfies governance intent | ATRS registration, DPIA, DUAA rights disclosure |
| Security | `.env` file, local `output/` folder | Secrets management, access controls, tamper-evident audit |
| Infrastructure | CLI on developer machine | Containerised, CI/CD, rate-limit-aware, HA |
| Triage | Stage 1 classification | All 6 stages; NER; effort estimation |
| Integration | Standalone file processing | Case management REST API; web HITL interface |
| Monitoring | Per-request cost log | Bias monitoring, accuracy benchmarking, drift detection |
| Knowledge | Static policy `.txt` files | Versioned policy store; FOIA knowledge graph |
| People | Demo | Operator training; change management; legal oversight |

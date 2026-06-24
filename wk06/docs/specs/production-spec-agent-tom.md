# Production Requirements — FOI Intelligent Automation System

**Author:** Agent-Tom  
**Date:** 2026-06-24  
**Status:** Draft — out of scope for hackathon; reference for real deployment  
**Sources:** `docs/research/foi-landscape-synthesis.md`; `docs/research/cache-atrs-requirements.md`; `docs/research/cache-uk-ai-playbook-governance.md`; `docs/research/cache-ico-ai-foi-guidance-2026.md`

---

## Purpose

This document captures requirements that a public authority would need to satisfy before deploying this system in production. None of these items are required for "Excellent" at the hackathon, but they are documented here because:

1. Some should inform hackathon design decisions (e.g. the append-only audit trail is already correct for production)
2. Any team considering a real deployment needs to know what the full picture looks like

---

## 1. Regulatory compliance requirements

### 1.1 Algorithmic Transparency Recording Standard (ATRS)

**Requirement:** Any public authority deploying a tool with "significant influence on a decision-making process with public effect" must publish an ATRS record before going live. This has been mandatory for central government departments since February 2024.

**What must be submitted:**
- **Tier 1 record** (mandatory): tool name, description, scope, statement of significant influence, human oversight mechanism, named third-party suppliers, publication date — submitted to the ATRS register
- **Tier 2 record** (for tools in wider use): additionally requires bias testing results, performance metrics, training data description, equality impact assessment

**Implication for design:** The audit trail (capturing operator identity, AI output, and human decision for every processed request) is the primary evidence that the "human oversight mechanism" is operational. This must be preserved.

### 1.2 Data (Use and Access) Act 2025 (DUAA 2025)

**Requirement:** In force February 2026. Creates individual rights around AI-assisted decisions with "legal or similarly significant effects." FOI decisions almost certainly qualify.

**Data subjects have the right to:**
- Be informed that AI contributed to the decision
- Make representations before the decision is finalised
- Request human review of the AI output

**What production adds to the hackathon design:**
- The FOI response letter must include a disclosure statement (e.g. "This response was drafted with AI assistance and reviewed and approved by [operator name]")
- The authority must have a data subject rights procedure for requests about the AI's role
- Evidence of the AI's role must be stored for the retention period of the record

### 1.3 UK GDPR / DPA 2018 — personal data

**Requirements:**
- A Data Protection Impact Assessment (DPIA) must be completed before deployment
- A named Data Protection Officer must have oversight
- A retention policy must be set for audit trail entries
- Mechanism must exist for data subjects to request audit entries relating to them under Subject Access Requests (SAR)
- Secure storage for all outputs (access controls, encryption at rest)

### 1.4 FOIA duty to assist (s.16 FOIA 2000)

**Requirement:** The authority has a duty to advise and assist requesters. A system that auto-rejects ambiguous or malformed requests would breach this duty. (The MVP already addresses this by flagging for operator review rather than rejecting — this requirement confirms that design is correct.)

---

## 2. Governance requirements

### 2.1 Bias and drift monitoring

**Requirement:** Required under UK AI Playbook Principle 5 and ATRS Tier 2.

Post-deployment, the authority must track:
- Triage classification consistency over time (a shift in exemption rates may indicate model drift)
- Operator override rate (high override rate signals poor compliance recommendations)
- Operator modification rate (high modification rate signals poor draft quality)
- Distribution of exemptions applied by topic (checks for systematic over/under-exemption)

**What this requires beyond the hackathon:**
- A reporting mechanism over the audit trail (e.g. `main.py report` command)
- A baseline established at launch and reviewed periodically
- A process for investigating anomalies

### 2.2 Equality impact assessment

**Requirement:** Before deploying a tool that affects public-facing decisions, assess whether the AI's behaviour differs systematically across protected characteristics (Equality Act 2010).

For the FOI context: does the system's recommendation differ by request topic in ways that could disadvantage certain types of requester?

This is largely an organisational exercise rather than a software task, but it requires the audit trail to be queryable by topic over time.

### 2.3 Human oversight — anti-rubber-stamping

**Requirement:** The HITL gate must be genuinely effective, not cosmetic. Research on government automation (the Robodebt scheme — $2.4bn in compensation) shows that when operators are under pressure, a gate that technically requires a click becomes rubber-stamping.

**What production adds:**
- Operator training on FOIA exemptions (to spot errors in compliance recommendations)
- Training on AI hallucination risks and how to use the evidence display
- Defined escalation paths (when to refer to a senior officer or legal team)
- Monitoring of approval-without-modification rate as an early warning indicator

---

## 3. Security requirements

### 3.1 Secrets management

**Requirement:** Production cannot use `.env` files for API keys on shared infrastructure.

Requires:
- Secrets management service (e.g. AWS Secrets Manager, Azure Key Vault, GDS Secrets Management)
- Rotation policy for LLM API keys
- Audit log of secret access (separate from application audit log)

### 3.2 Access controls

**Requirement:** The hackathon uses an `OPERATOR_ID` environment variable. Production requires:
- Authentication via SSO / Active Directory — operator identity cannot be self-asserted
- Role-based access: who can process requests, who can view audit trail, who can re-index policy documents
- Tamper-evident audit trail storage (append-only log service, not a local file)

### 3.3 Data handling

**Requirement:**
- `output/` and the ChromaDB index must be access-controlled (not world-readable)
- The system must not write personal data to application logs (only aggregate tokens/costs)
- Backup and restore procedures for the ChromaDB index and audit trail

---

## 4. Infrastructure requirements

### 4.1 Containerisation

**Requirement:** The hackathon runs locally on a developer machine. Production requires:
- Container image with pinned dependencies
- CI/CD pipeline: automated tests on commit, container build on merge
- Container registry
- The HuggingFace embedding model baked into the container image (no runtime download from external services)

### 4.2 Rate limit management at scale

**Requirement:** The hackathon processes a handful of requests sequentially. A real FOI team processing ~500+ requests per year needs:
- Request queuing to smooth API rate limit exposure
- SLA transparency: operators need to know expected processing time per request
- Graceful degradation: if the LLM API is unavailable, queue requests rather than fail silently

### 4.3 Availability

**Requirement:** The system is a decision-support tool for a statutory obligation (20-working-day response clock). Downtime that causes missed deadlines is a regulatory breach. Production deployment must define:
- Target availability
- Failover/recovery procedures
- Manual fallback process when the system is unavailable

---

## 5. Operational requirements

### 5.1 Policy corpus management

**Requirement:** The hackathon uses a static set of `.txt` policy documents. Production requires:
- A governed process for adding, updating, and retiring policy documents
- Versioning: policy chunks must carry a version reference so the audit trail records which version of guidance was in effect at decision time
- Integration with the authority's document management system (SharePoint, Confluence, or equivalent)
- Re-indexing workflow with quality checks

### 5.2 Operator training

**Requirement:** Research (arXiv 2512.02774) found that the top barrier to AI adoption in FOI teams is staff lacking expertise to validate AI outputs. Production deployment requires:
- Training on FOIA exemptions (staff must be able to spot incorrect compliance recommendations)
- Training on AI limitations (hallucination, evidence-grounding requirements)
- Clear escalation paths to senior officers and legal team
- Supervised rollout: first ~200 decisions reviewed by a senior officer before unmonitored operation

### 5.3 Case management integration

**Requirement:** Production FOI teams use case management platforms (GovDesk, Civica FOI Pro, Octopus) that track receipt, acknowledgement, deadline management, and correspondence. The hackathon CLI would need to become an API service to integrate with these platforms.

---

## 6. Summary: hackathon vs production

| Area | Hackathon design | Production requirement |
|------|-----------------|----------------------|
| Regulatory | HITL gate satisfies governance intent | ATRS registration, DPIA, DUAA disclosure |
| Security | `.env` file, local output folder | Secrets management, SSO, access controls |
| Infrastructure | CLI on developer machine | Containerised, CI/CD, rate-limit-aware |
| Monitoring | Per-request cost log | Bias monitoring, drift detection, audit reporting |
| Policy corpus | Static `.txt` files | Versioned, governed, integrated with DMS |
| People | Demo | Operator training, escalation paths, supervised rollout |

# FOI Automation Landscape — Research Synthesis

**Author:** Agent-Jack  
**Date:** 2026-06-24  
**Sources:** See `wk06/docs/research/cache-*.md` files for cached pages; full URLs listed per finding.

This document synthesises research into similar manual and AI-assisted FOI request workflow implementations. It surfaces new questions, potential issues, stretch goals, governance requirements, and practical implementation details relevant to the wk06 system design.

---

## 1. New Questions for the Team

### 1.1 Triage scope is too narrow
Industry practice (VIDIZMO, `cache-vidizmo-foi-triage.md`) describes **six triage stages** before redaction begins; our system performs only stage 1 (topic classification). Do we want to add any of:
- **Effort estimation** — output a rough handling-time estimate for the operator's dashboard
- **Vexatious flag** — the ICO now explicitly flags AI-generated vexatious requests as a growing problem; should our triage agent detect them?
- **Sensitivity flag** — flag requests touching litigation, media, or executive personnel, warranting a senior reviewer rather than a standard operator

### 1.2 What happens when exemptions conflict?
Our compliance agent returns a single `recommendation` value. Real FOI decisions often involve **multiple overlapping exemptions** (e.g., s.40 personal data *and* s.43 commercial interests on the same document). Does our compliance agent rank or weight them? Does it surface when they conflict with each other?

### 1.3 Third-party notification obligations
Some exemptions (notably s.41 — information provided in confidence) require the authority to **notify third parties** before disclosure. Our system has no mechanism for this. At minimum, the compliance agent should flag when a third-party notification may be required.

### 1.4 How do we handle malformed/AI-generated requests?
The ICO's May 2026 guidance (`cache-ico-ai-foi-guidance-2026.md`) identifies a new operational problem: AI-drafted requests frequently **misquote legislation or contain ambiguous scope**. Should the triage agent classify and flag these? The system should not reject them (that would breach the FOIA duty to assist), but surfacing "this request appears malformed — clarification recommended" would help the operator.

### 1.5 Are our chunk parameters right for dense legal text?
Our current spec sets `chunk_size=500, chunk_overlap=100`. Legal exemption guidance is dense and cross-referential. Has anyone validated whether 500-token chunks preserve enough context for the compliance agent to reason correctly about qualified exemptions (which require a public interest test)? This should be tested empirically before implementation.

### 1.6 What is the right k for RAG retrieval?
We use `RAG_TOP_K=5`. For requests that might engage several exemptions, is 5 chunks sufficient? Is there a cost-accuracy trade-off worth profiling?

---

## 2. Potential Issues and Risks

### 2.1 LLM hallucination on legal citations (HIGH)
**Finding:** Commercial LLMs hallucinate 13–21% of legal citations even with RAG (arXiv 2606.00898). RAG-augmented generation achieves the *best* accuracy but errors remain.  
**Risk for us:** The compliance agent citing non-existent exemption sections (e.g., "s.47(2)(b)") or misattributing policy text would produce legally indefensible draft responses.  
**Mitigations:**
- Require the compliance agent to include verbatim quotes from retrieved chunks alongside exemption citations
- Add a post-generation check: verify that every cited section number appears in the retrieved chunk text
- Display chunk text alongside the compliance reasoning in the HITL gate so the operator can spot-check citations

### 2.2 Triage errors cascade (HIGH)
**Finding:** VIDIZMO production experience confirms "triage errors cascade downstream more expensively than redaction errors" (`cache-vidizmo-foi-triage.md`). A misclassified topic sends the wrong RAG query, which retrieves irrelevant chunks, which leads the compliance agent to a wrong exemption analysis.  
**Risk for us:** The triage agent is the weakest link architecturally; an error is amplified not corrected by downstream agents.  
**Mitigations:**
- Expose triage confidence scores prominently in the HITL display
- Let the operator edit the triage classification *before* approving the response (requires pipeline re-run or allowing manual override)
- Treat low-confidence triage results as a trigger for mandatory operator review comment

### 2.3 Section 40 personal data handling (HIGH)
**Finding:** s.40 (personal data of third parties) is the most-commonly applied FOI exemption and the one most tightly regulated by UK GDPR / the DPA 2018. Our compliance agent identifies s.40 applicability but doesn't identify *which* personal data in the response draft requires redaction.  
**Risk for us:** A draft letter that discloses a third party's personal data — even paraphrased from policy chunks — could constitute a data breach.  
**Mitigation:** s.40 compliance should trigger a specific instruction to the response agent to avoid naming or describing identifiable individuals from retrieved chunks.

### 2.4 Automated Decision-Making under the Data (Use and Access) Act 2025 (MEDIUM)
**Finding:** The DUAA 2025 (in force February 2026) creates new individual rights around AI-assisted decisions with "legal or similarly significant effects." If our system is used by a public authority, FOI decisions likely qualify.  
**Risk:** Data subjects may invoke rights to: (a) be informed of the AI's role, (b) make representations, (c) request human review of the AI's output.  
**Implication:** Our audit trail is an asset here — it records exactly what AI output the operator saw and what decision they made. But the system documentation needs to make the AI's role explicit.

### 2.5 Robodebt-style automation bias risk (MEDIUM)
**Finding:** Australia's Robodebt scheme ($2.4bn in compensation) demonstrated that automated government decision pipelines without adequate human oversight can systematically harm citizens and destroy public trust.  
**Risk for us:** If the HITL gate becomes a rubber stamp (operators approve without reading), the system amplifies AI errors at scale.  
**Mitigation:** The current design requires the operator to actively choose A/R/M — passive approval is not possible. This is the right design; document it explicitly in the ATRS record and any governance submission.

### 2.6 Policy document staleness (MEDIUM)
**Finding:** The RAG store is indexed once at startup. FOI exemption guidance and departmental policies change.  
**Risk:** The compliance agent reasons from outdated policy documents, citing superseded guidance.  
**Mitigation:** Add a `last_indexed` timestamp to the ChromaDB metadata; surface a warning in the HITL display if policy docs haven't been re-indexed within a configurable period (e.g., 30 days).

### 2.7 ATRS registration obligation (LOW for hackathon, HIGH for real deployment)
**Finding:** Any public authority deploying an algorithmic tool with "significant influence on a decision-making process with public effect" must publish an ATRS record (`cache-atrs-requirements.md`). This became mandatory for all government departments in February 2024.  
**Risk for us:** Not a hackathon blocker, but a real-world deployment without ATRS registration would be non-compliant from day one.

---

## 3. Stretch Goals (Prioritised)

### Tier 1 — High value, architecturally close
**S1. Self-citation verification**  
After the compliance agent produces its output, run a secondary check: verify that each cited exemption section number appears verbatim in the retrieved chunks. Reject and re-prompt if not. Addresses the #1 hallucination risk with minimal added cost.

**S2. Triage override with pipeline re-run**  
At the HITL gate, allow the operator to edit the triage classification (topic, complexity). If changed, re-run the RAG retrieval and compliance analysis with the corrected classification before the operator makes their final decision. Currently the HITL gate is review-only.

**S3. Policy document staleness warning**  
Track `last_indexed` per document and surface a warning if the store is stale. One `main.py index --check-freshness` command could report stale docs without re-indexing.

### Tier 2 — Meaningful additions, moderate effort
**S4. Duplicate/similar request detection**  
Before running the full pipeline, embed the incoming request and compare against past `output/*.json` files. If similarity > threshold, surface the past decision to the operator as a reference. Reduces duplicated work and promotes consistency across similar requests.

**S5. Vexatious / malformed request flagging**  
Add a vexatious/malformed classification to the triage agent output: `vexatious_flag: bool` and `malformed_flag: bool`. Vexatious requests can be handled more efficiently; malformed requests should prompt operator-composed clarification before the pipeline runs.

**S6. ATRS record auto-generation**  
Add a `main.py atrs-record` command that outputs a pre-filled ATRS Tier 1 record (tool name, description, third-party suppliers, human oversight point) as a markdown or JSON file. Turns a compliance burden into a one-command artefact.

### Tier 3 — Larger scope, future work
**S7. Precedent store**  
Persist approved audit entries to a second ChromaDB collection. Before compliance analysis, retrieve similar past decisions as few-shot examples for the compliance agent. Promotes consistency and learns from operator corrections over time.

**S8. Multi-department routing**  
Detect when a request crosses departmental boundaries and flag for routing to the correct team. Requires an authority/department taxonomy.

**S9. Proactive disclosure flagging**  
Identify requests where the response could be pre-emptively published to a disclosure log (like WhatDoTheyKnow / Alaveteli), reducing future duplicate requests on the same topic.

---

## 4. Governance Requirements

These are not optional for a real-world public authority deployment. For the hackathon, they inform design decisions and documentation.

| Requirement | Source | Design implication |
|-------------|--------|--------------------|
| HITL gate is mandatory — no auto-approval | UK AI Playbook Principle 4; ICO guidance | Already in design (`hitl.py` re-raises `KeyboardInterrupt` rather than auto-approving) |
| AI-assisted draft must be identified as such | UK AI Playbook; ICO guidance | Audit trail records `decision` and `operator`; HITL display should label the draft "AI-generated draft" |
| ATRS record required for public-effect algorithmic tools | ATRS mandatory policy (Feb 2024) | Not needed for hackathon; required for real deployment — see S6 stretch goal |
| Automated decision rights under DUAA 2025 | Data (Use and Access) Act 2025, s.80 | Operator attribution in every audit entry satisfies the "human review" requirement |
| Bias monitoring and drift detection post-deployment | UK AI Playbook Principle 5 | No monitoring in MVP; add as a stretch goal post-hackathon |
| Transparency about third-party suppliers | ATRS Tier 2 | Document Anthropic, HuggingFace, ChromaDB in any governance submission |
| Data subjects' s.40 personal data not disclosed | UK GDPR / DPA 2018 | Compliance agent must explicitly instruct response agent to avoid naming individuals |
| Audit trail must be append-only and attributed | ICO enforcement practice; ATRS | Already in design: `output/audit_trail.jsonl` with `operator` field |

---

## 5. Practical Implementation Details

### 5.1 The industry triage model is six stages, not one
Our triage agent does topic classification. Production systems also do entity extraction, duplicate detection, third-party surfacing, effort estimation, and sensitivity flagging. **For the MVP, classify + confidence score + vexatious flag is a realistic scope extension.** The other four stages are stretch goals.

### 5.2 LLM hallucination mitigation patterns
From arXiv surveys on RAG grounding:
- **Force citation format:** Require the compliance agent to quote verbatim text alongside every exemption it cites. If it cannot quote, it cannot cite.
- **Hedging language:** Prompt templates that require the agent to use "based on the retrieved policy text..." language reduce overconfidence.
- **Step-by-step reasoning scaffolding:** Breaking compliance analysis into sub-steps (identify exemption → find evidence → assess public interest) reduces hallucination versus a single free-form output.
- **Knowledge graph augmentation** (stretch): Cross-referencing exemption numbers against a structured FOIA exemption taxonomy significantly reduces citation hallucination vs. flat RAG.

### 5.3 Alaveteli as a reference for workflow management
The mySociety Alaveteli platform (1M+ requests across 25+ jurisdictions) focuses on *workflow management* rather than AI: automated notifications, reminders, publication of responses. Its key design principle — **"hide the complexity behind the FOI process"** — is a useful frame. Our system should adopt the same philosophy for operators: surface a clear, actionable decision, not a wall of agent outputs.

### 5.4 Existing AI redaction tools in UK government use
- **RedactXpert** (Simpson Associates): Azure Cognitive Services, used by UK public sector
- **VIDIZMO Redactor**: Used by law enforcement and government; integrates via REST API
- **CircleT**: Used by Department of Veterans' Affairs (Australia) for medical record redaction

None of these address the *compliance analysis* and *response drafting* stages — the gap our system fills.

### 5.5 AI-generated FOI request volume is rising
The 94,526 requests in 2025 (ICO data) represents a 14% year-on-year increase, partly attributed to AI-assisted request drafting. Systems processing these requests are therefore likely to see **increasing proportions of malformed, ambiguous, or over-broad requests** — reinforcing the value of our triage agent's classification output and the operator clarification pathway.

### 5.6 Multi-agent cross-checking reduces hallucinations
From the regulatory compliance literature: **multi-agent systems where one agent verifies another's output are more accurate than single-agent pipelines**. Our supervisor → triage → compliance → response chain already embodies this, but we don't have an explicit verification agent. Adding a lightweight "citation verifier" agent (or structured post-generation check) between compliance and response would be architecturally consistent with what the research shows works.

---

## Source Index

| Cache file | Source URL |
|------------|------------|
| `cache-ico-ai-foi-guidance-2026.md` | https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/2026/05/new-guidance-to-support-public-authorities-dealing-with-ai-generated-foi-requests/ |
| `cache-uk-ai-playbook-governance.md` | https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government/artificial-intelligence-playbook-for-the-uk-government-html |
| `cache-atrs-requirements.md` | https://www.gov.uk/government/publications/guidance-for-organisations-using-the-algorithmic-transparency-recording-standard/algorithmic-transparency-recording-standard-guidance-for-public-sector-bodies |
| `cache-vidizmo-foi-triage.md` | https://vidizmo.ai/blog/ai-foi-request-triage-privacy-consultancies |
| `cache-ai-redaction-uk-authorities-arxiv.md` | https://arxiv.org/abs/2512.02774 |

Additional sources consulted but not cached (lower specificity):
- https://www.publicsectorexecutive.com/articles/new-guidance-public-authorities-dealing-ai-generated-foi-requests
- https://cddo.blog.gov.uk/2025/03/10/developing-frameworks-and-tools-to-support-responsible-data-and-ai-use-across-the-public-sector/
- https://dataingovernment.blog.gov.uk/2025/05/08/making-the-algorithmic-transparency-recording-standard-atrs-mandatory-across-government/
- https://alaveteli.org/
- https://arxiv.org/html/2606.00898 (LLM citation hallucination — legal domain)
- https://arxiv.org/html/2601.19927v1 (RAG attribution hallucination survey)

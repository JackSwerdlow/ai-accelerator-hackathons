# Page Cache: Algorithmic Transparency Recording Standard (ATRS) — Requirements

**Source:** https://www.gov.uk/government/publications/guidance-for-organisations-using-the-algorithmic-transparency-recording-standard/algorithmic-transparency-recording-standard-guidance-for-public-sector-bodies  
**Retrieved:** 2026-06-24  
**Relevance:** A real-world deployment of our FOI processing system by a public authority would trigger a mandatory ATRS publication. Understanding the required fields informs what our system needs to log and expose.

---

## What Triggers a Mandatory ATRS Record

The ATRS is **mandatory** if all of the following apply:
1. The organisation is a government department or arm's-length body (ALB) delivering public/frontline services or interacting directly with the public.
2. The algorithmic tool has **"significant influence on a decision-making process with public effect"**.

An AI system that classifies, analyses, or drafts responses to FOI requests would meet criterion 2, since FOI decisions are public-effect decisions affecting citizens' rights to information.

## Mandatory Fields

### Tier 1 (Public-facing, accessible to general public)
- Tool name and brief plain-English description
- Owning organisation, contact details, and public website

### Tier 2 (Technical detail, for specialist audiences)
- **Senior responsible owner** role and accountability chain
- **Third-party suppliers** and their specific contributions to the tool
- **Operational mechanics** — how the tool works and where human oversight occurs
- **Technical architecture** and data flow specifications
- **Model performance metrics**, including bias evaluations
- **Training/validation data** composition and sensitivity attributes
- **Risk assessments** and mitigation strategies documented

## Exemptions (Partial Redaction Permitted)

Authorities may redact specific fields (not withhold the whole record) where disclosure would reveal:
- Operational security details (e.g., thresholds that users could game to avoid flagging)
- Cybersecurity attack vectors from system architecture details
- Supplier intellectual property (though only high-level information is requested)

**Principle:** Partial publication with redaction explanations is preferable to withholding entire records — consistent with the spirit of FOI.

## Update and Decommission Requirements

- Records must be **updated when substantive details change**: pilot-to-production transitions, new training datasets, process modifications.
- Organisations must **notify the ATRS team on decommissioning**.

## Design Implications for Our System

| ATRS field | What our system should log/expose |
|------------|-----------------------------------|
| Operational mechanics + human oversight | The HITL gate in `hitl.py` and its mandatory nature |
| Third-party suppliers | Anthropic API, HuggingFace embeddings, ChromaDB |
| Model performance metrics | Accuracy of triage classification, compliance recommendation correctness |
| Training/validation data | Policy documents indexed; FOI request samples used in testing |
| Risk assessments | Hallucination rate; triage error cascade risk; data handling of s.40 content |

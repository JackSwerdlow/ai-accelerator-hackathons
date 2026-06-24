# Page Cache: AI-Driven Document Redaction in UK Public Authorities (arXiv 2512.02774)

**Source:** https://arxiv.org/abs/2512.02774  
**Retrieved:** 2026-06-24  
**Relevance:** The only empirical study specifically examining AI adoption for FOI document handling in UK public authorities. Findings directly inform our risk assessment and the gap our system is addressing.

---

## Study Design

Survey of 44 UK public authorities across healthcare, government, and higher education sectors. Conducted via FOI requests, making it methodologically unique (studying AI adoption in FOI systems *using* FOI requests).

## Key Quantitative Findings

- **Only 1 of 44 authorities** reported using AI tools for document redaction
- **50% reported "information not held"** when asked about redaction policies — indicating widespread absence of formal processes, not just AI
- AI adoption in FOI document handling in UK public sector is at near-zero baseline

## Three Core Implementation Gaps

1. **Record-keeping deficiencies** — Organisations lack documentation systems needed to even support automated processes
2. **Standardisation absence** — No formal redaction policies; highly inconsistent practice across authorities
3. **Training shortcomings** — Staff lack expertise to oversee and validate AI-driven outputs

## Regulatory Tension Identified

The study identifies a structural tension between two legal obligations:
- **FOIA 2000** — transparency and disclosure obligations push for efficient, complete processing
- **UK GDPR / Data Protection Act 2018** — personal data protection obligations require careful identification and redaction before release

Manual processes struggle to satisfy both at scale; AI processes introduce new risks of over/under-redaction.

## Human Oversight Imperative

Authors call for a **"socio-technical approach that balances technological automation with meaningful human expertise"**. AI tools cannot operate independently — skilled human validation remains essential, particularly for:
- Section 40 (personal data) determinations
- Borderline cases where exemptions require public interest balancing
- Novel or complex request types not well-represented in training data

## Recommendations from the Authors

1. Improved record-keeping practices across public authorities
2. Standardised redaction guidelines at a national level
3. Enhanced specialised training for public sector FOI staff

## Implication for Our Design

Our system addresses the *response drafting* side rather than redaction per se, but the same socio-technical principle applies: the mandatory HITL gate is the mechanism that satisfies the "meaningful human expertise" requirement. The study confirms there is a large, currently unaddressed market for this type of tooling.

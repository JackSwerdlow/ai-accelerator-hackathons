# Page Cache: ISO/IEC 42001:2023 Clause 6.1.4 — AI System Impact Assessment

**Sources:**
- https://crestadvisoryafrica.com/article.php?id=1396 (checklist of clause 6.1.4 requirements and evidence)
- https://iso-docs.com/blogs/iso-42001-standards/clause-6-1-4-ai-system-impact-assessment-iso-42001-artificial-intelligence-management-system-aims
- https://www.schellman.com/blog/iso-certifications/how-to-assess-and-treat-ai-risks-and-impacts-with-iso42001
- https://watchdogsecurity.io/iso-42001/conduct-ai-system-impact-assessments

**Retrieved:** 2026-07-22
**Relevance:** Tom asked what's required to satisfy ISO/IEC 42001 clause 6.1.4 for the FOI system. We don't hold the licensed standard text, so this is synthesised from compliance-consultancy summaries (cross-checked across independent sources, not a single vendor's paraphrase) rather than the primary document — treat wording as indicative, not a verbatim quote of the standard.

---

## What clause 6.1.4 requires (synthesised, cross-source)

Clause 6.1.4 sits under 6.1 "Actions to address risks and opportunities", alongside 6.1.2
(AI risk assessment) and 6.1.3 (AI risk treatment). It requires the organisation to define
and document a **repeatable process for assessing the impact of an AI system on individuals,
groups, and society** across its lifecycle, and to feed that assessment into risk management.

Recurring elements across sources:
1. A **documented, repeatable methodology** for impact assessment (not ad hoc).
2. **Lifecycle coverage** — before deployment, and re-run when the system, its use case, or
   its operating environment materially changes.
3. **Scope definition** — which systems/use cases are in scope.
4. **Consequence identification** for individuals, groups, and society — including intended
   use, reasonably foreseeable misuse, and failure modes.
5. **Contextual analysis** — technical (model type, data, autonomy, accuracy, explainability)
   and societal/legal/cultural context of deployment.
6. **Stakeholder identification** — who is affected (data subjects, operators, requesters).
7. A **feedback loop into 6.1.2/6.1.3** — impact findings must inform risk assessment and
   treatment, not sit as a standalone document.
8. **Documented outcomes**: methodology, findings, decisions (go/no-go, mitigations), and
   review/update triggers.
9. **Management oversight** of the assessment and its conclusions.
10. Availability to relevant interested parties "where appropriate" (transparency).

## Mapping to the FOI system

| 6.1.4 element | Already covered by current design | Gap to close for formal compliance |
|---|---|---|
| Consequence identification (individuals/groups/society) | `docs/specs/production-spec-agent-tom.md` §1–2 already names concrete harms: wrongful disclosure of exempt material, wrongful withholding, disparate treatment by request topic | No single document frames these as an *impact assessment* artefact — they're scattered across ATRS/DUAA/equality-impact subsections |
| Foreseeable misuse / failure modes | §1.4 (duty to assist) and the fail-safe defaults in `system-design-agent-tom.md` §5 (triage failure → forces review; compliance failure → withhold) already encode this reasoning | Not written up as "failure mode analysis" with likelihood/severity |
| Technical context (model, autonomy, explainability) | Pipeline topology, per-agent model choice, and evidence-display design in `system-design-agent-tom.md` §1–4 document this | Not indexed against clause 6.1.4 specifically |
| Stakeholder identification | Implicit (requesters, operators, the authority) | Not an explicit, named list |
| Feedback into risk assessment/treatment (6.1.2/6.1.3) | The HITL gate and conservative fallback defaults *are* risk treatments | No 6.1.2-style risk register exists yet to feed into |
| Documentation of methodology + outcomes | AI_LOG.md and audit_trail.jsonl capture *decision* history, not *impact assessment* history | No standalone impact assessment report exists |
| Review triggers on change | Not addressed | No defined trigger (e.g. "re-run assessment when policy corpus changes or model is swapped") |
| Management oversight | N/A at hackathon scale | Would need a named accountable owner in production |

## Design implication

At hackathon scope, an ISO 42001 certification exercise is out of scope (the rubric's
"Governance" axis is about the HITL gate, not AIMS certification), and `production-spec-agent-tom.md`
already frames itself as "requirements a public authority would need to satisfy before
deploying this system in production." Clause 6.1.4 is the same category of requirement as
ATRS/DUAA/DPIA already documented there — it belongs alongside them, not as a separate
implementation task in `solution/`.

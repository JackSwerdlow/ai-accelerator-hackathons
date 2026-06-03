# AI Assistance Log

Record every instance where you use AI to generate, refactor, or debug code. Four fields per entry: what you asked for, what the AI produced, what you changed, and why you changed it. There is an example provided of how the format for each should look.

## Example: Prompt 0: Eligibility logic for married couple's allowance edge case

| Field | Detail |
|-------|--------|
| **Date + Time** | YYYY-MM-DD HH-MM-SS |
| **Task** | Scaffolded eligibility check for married couple's allowance |
| **What AI Generated** | if/else chain covering 5 scenarios: single owner, joint owner, private renter, housing association renter, and council tenant. Used hardcoded age threshold of 65 for pension-credit eligibility. Did not include civil-partnership status. Error message on ineligible path was generic ("You are not eligible"). |
| **What You Changed + Why** | Removed hardcoded age threshold (was 65, should be state-pension-age variable) -- hardcoded age breaks if policy changes. Added missing civil-partnership case alongside married status -- civil partnership is a legal requirement since 2004. Changed error message from generic to specific ("You are not eligible because your household income exceeds the threshold") -- generic errors do not help users correct their input. |

## Prompt 1: [Agent-Jack] Content plan for the Green Home Grant eligibility checker

| Field | Detail |
|-------|--------|
| **Date + Time** | 2026-06-03 |
| **Task** | Create a content-first plan covering all page copy, question options, eligibility rules, and result messages for the service — saved to `docs/plans/2026-06-03-content-plan.md` |
| **What AI Generated** | Full content plan including: start page description text; exact question headings, radio option labels and values, hint text, and error messages for all 5 question pages; check-your-answers row labels and display-label mapping; 5 priority-ordered eligibility rules in plain language; measures-available logic per property type; result page panel titles and body paragraphs for all three outcomes (eligible, partial, ineligible) including sub-cases for renter vs mid-income and income-too-high vs already-fitted; GOV.UK error pattern description; accessibility statement and footer link content; and a content decisions rationale table. |
| **What You Changed + Why** | No changes made to the generated content — this was a planning artefact reviewed before any code was written. Content decisions (e.g. three income bands rather than free-text, all renters routed to partial regardless of income) were accepted as reasonable for a fictional scheme. Grant amounts ("up to £10,000 / £5,000") accepted as appropriately hedged. |

## Prompt 2: [Agent-Jack] Agent work split plan for 4-way parallel development

| Field | Detail |
|-------|--------|
| **Date + Time** | 2026-06-03 |
| **Task** | Define how to split the Green Home Grant build across 4 agents to maximise parallel work and minimise merge conflicts — saved to `docs/plans/2026-06-03-agent-work-split.md` |
| **What AI Generated** | Work split assigning strict file ownership to each agent: Agent 1 (App.jsx + all shared components + Start/Accessibility pages), Agent 2 (question pages 1–3), Agent 3 (questions 4–5 + Check Answers), Agent 4 (eligibility logic + Result page + unit tests). Included an agreed interface contract (formData shape and prop signature), a full file ownership table, conflict risk analysis, and notes for collating all four agents' plans into one implementation plan. |
| **What You Changed + Why** | No changes — reviewed and accepted as a planning artefact. Strict file ownership confirmed as the right strategy; AI_LOG.md is the only unavoidable shared file and is low-risk to merge. |

## Prompt 3: [Agent-Research] Standards research report for Green Home Grant

| Field | Detail |
|-------|--------|
| **Date + Time** | 2026-06-03 |
| **Task** | Research the standards this service must conform to (GOV.UK Design System, WCAG 2.2 AA, GDS Service Standard, PSBAR, content style) and produce `docs/research/research.md` with primary-source links and direction for later requirements / solution planning. Sanity-check the report by spawning subagents. |
| **What AI Generated** | `docs/research/research.md` — ten numbered sections covering: how to read the doc, legal baseline (PSBAR + Equality Act + UK GDPR + PECR), GDS Service Standard with relevance rating per point, WCAG 2.2 AA (POUR, load-bearing AA SCs for forms, new-in-2.2 criteria most likely to bite this service), GOV.UK Design System (patterns, components, pattern-specific rules including question pages, check answers, confirmation, validation, phase banner), content design (style guide and form-structure guidance), accessibility statement structure, cross-browser/mobile expectations, adjacent technical standards (security headers, performance, analytics, inclusive language), testing approach, and 11 directional questions for the next phase. Two appendices: quick-reference link list and explicit out-of-scope items. |
| **What You Changed + Why** | After three sanity-check subagents reviewed the draft, made these factual / structural corrections: (1) relabelled WCAG 3.3.7 Redundant Entry and 3.2.6 Consistent Help from AA to A (they are new in 2.2 but at Level A); (2) reconciled accessibility-statement section count from 7 to the actual 8 in the GOV.UK model; (3) added missing coverage of UK GDPR / PECR / cookies, the "Check if a service is suitable" eligibility-screening pattern (a major omission for an eligibility checker), Service Assessment process, security headers, performance, analytics, inclusive language; (4) added 1.4.4 Resize Text to the load-bearing SC table to match a forward reference in §9; (5) softened overstated claims about the check-answers title and the "Start using a service" replacement history; (6) expanded §10 from 6 to 11 directional items to cover cookie posture, eligibility-test strategy, browser-support floor, Welsh-language scoping, and the phase-banner feedback link target; (7) added Appendix B listing intentional out-of-scope items (AI_LOG, stretch challenges, i18n, Prototype Kit) for traceability. |

## Prompt 4: [Agent-Jack] Full implementation plan for the Green Home Grant eligibility checker

| Field | Detail |
|-------|--------|
| **Date + Time** | 2026-06-03 |
| **Task** | Create a comprehensive implementation plan drawing together content plan, standards research, and frontend-design skill guidance — saved to `docs/plans/2026-06-03-implementation-plan-jack.md` |
| **What AI Generated** | Full implementation plan covering: design philosophy (refined polish within strict GOV.UK constraints); new file list (`progress.css`, `ProgressIndicator.jsx`, eligibility utils); agreed interface contract (formData shape + eligibility function signature); task checklist with checkboxes organised by feature (infrastructure, start page, five question pages, check-answers, eligibility logic, result page, accessibility statement, page transitions); three specific elevation choices (progress indicator, 150ms page-transition CSS animation, inline SVG icons on result panels); per-task GOV.UK pattern requirements (legend wrapping, hint text, error summary link targets, aria-describedby); GOV.UK compliance checklist; test strategy table; definition-of-done criteria. |
| **What You Changed + Why** | Removed per-agent task assignment from the plan structure (user asked to ignore agent-work-spec); reorganised by feature/component instead. Resolved tension between frontend-design skill's bold-aesthetic direction and the GOV.UK compliance rubric by explicitly naming the constraint and limiting elevation to three low-risk additions that are within GOV.UK standards. Added `prefers-reduced-motion` guard on the page-transition animation to preserve accessibility. |

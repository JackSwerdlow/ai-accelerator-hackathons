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

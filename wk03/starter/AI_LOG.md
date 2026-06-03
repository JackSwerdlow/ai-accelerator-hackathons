# AI Assistance Log

Record every instance where you use AI to generate, refactor, or debug code. Four fields per entry: what you asked for, what the AI produced, what you changed, and why you changed it. There is an example provided of how the format for each should look.

## Example: Prompt 1: Eligibility logic for married couple's allowance edge case

| Field | Detail |
|-------|--------|
| **Date + Time** | YYYY-MM-DD HH-MM-SS |
| **Task** | Scaffolded eligibility check for married couple's allowance |
| **What AI Generated** | if/else chain covering 5 scenarios: single owner, joint owner, private renter, housing association renter, and council tenant. Used hardcoded age threshold of 65 for pension-credit eligibility. Did not include civil-partnership status. Error message on ineligible path was generic ("You are not eligible"). |
| **What You Changed + Why** | Removed hardcoded age threshold (was 65, should be state-pension-age variable) -- hardcoded age breaks if policy changes. Added missing civil-partnership case alongside married status -- civil partnership is a legal requirement since 2004. Changed error message from generic to specific ("You are not eligible because your household income exceeds the threshold") -- generic errors do not help users correct their input. |

## Prompt 2:

| Field | Detail |
|-------|--------|
| **Date + Time** | YYYY-MM-DD HH-MM-SS |
| **Task** | |
| **What AI Generated** | |
| **What You Changed + Why** | |

## Prompt 3:
...

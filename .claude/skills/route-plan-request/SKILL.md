---
name: route-plan-request
description: Route HTML planning requests between the exploratory planning skill and the auditable single-file wizard skill. Infer the route when the user's intent is clear; ask one short routing question when it is ambiguous. Use when the user wants an HTML plan, spec, checklist, PRD, analysis, or planning document but has not clearly said whether they want something exploratory or auditable.
argument-hint: Describe the plan you want. If you already know the mode, say whether you want something exploratory or auditable.
user-invocable: true
---

# Route Plan Request

This skill is a thin orchestrator for the two existing HTML planning skills:

- `generate-html-plan` for something **exploratory**
- `generate-interactive-plan` for something **auditable**

Do not build the HTML yourself in this skill. Your job is to decide which leaf skill should handle the request, then pass the user's context through.

## Route automatically when the request is already clear

Route to `generate-html-plan` when the user is clearly asking for something exploratory, such as:

- a brainstorm
- an analysis document
- a tabbed plan viewer
- a richer reference document
- a one-page planning document
- option comparison before committing
- open design decisions

Route to `generate-interactive-plan` when the user is clearly asking for something auditable, such as:

- an auditable plan
- an spec to be shared with stakeholders or colleagues
- a checklist
- a step-by-step decision flow
- a plan that writes answers back into the file
- a plan that can be verified
- a deterministic JSON export
- a markdown-first interactive workflow

## Ask only when the route is ambiguous

If the user has not made the mode clear, ask one short question before routing:

"Do you want something exploratory, or something auditable?"

If useful, expand the options in plain language:

- **Exploratory**: a richer HTML planning document for brainstorming, analysis, and reviewing options.
- **Auditable**: a single-file wizard or checklist that writes choices back into the file and can be verified, shared, and kept over time.

Do not ask this question if the request already strongly implies one route.

## Routing rules

After the user answers:

- If they choose **exploratory**, invoke `generate-html-plan`.
- If they choose **auditable**, invoke `generate-interactive-plan`.

If they ask for both, or they describe a hybrid request, prefer `generate-html-plan` unless they explicitly say the key requirement is that the document must be auditable.

If they specifically want a single long scrolling page with all content visible at once, prefer `generate-html-plan` unless they explicitly prioritise the auditable wizard/checklist behaviour over the one-page layout.

## Pass-through requirements

When handing off to the chosen skill, preserve all relevant user context, including:

- project or refactor name
- the planning subject
- team/no-team information
- desired styling or branding
- output location if already provided
- any constraints about verification, save-back, or review workflow

## Success condition

This skill succeeds when:

- it chooses the correct leaf skill without unnecessary questioning when the request is clear, or
- it asks exactly one short routing question when the request is ambiguous, using the word **auditable** for the single-file wizard/checklist path.

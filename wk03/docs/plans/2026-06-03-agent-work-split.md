# Agent Work Split Plan

**Author:** Agent-Jack  
**Date:** 2026-06-03  
**Status:** Draft — to be collated with plans from other agents into a single implementation plan

---

## Context

Four agents are working in parallel on the Green Home Grant eligibility checker. This document defines how to divide the work to maximise parallel progress and minimise merge conflicts.

All agents are currently in a planning phase. Plans from all four agents will be collated into a single implementation plan before any agent begins writing code.

The content design for the service is defined in `docs/plans/2026-06-03-content-plan.md`.

---

## Core Principle

**Strict file ownership.** If no two agents ever touch the same file, there are zero merge conflicts. The split below assigns every file to exactly one agent.

---

## Agreed Interface Contract

All agents must agree on this before writing any code. The formData shape and prop signature are the shared interface between App-level state (Agent 1) and each question page (Agents 2 and 3).

```js
// App.jsx — formData shape
const [formData, setFormData] = useState({
  propertyType: "",
  ownership: "",
  incomeBand: "",
  insulation: "",
  heating: ""
});

// Every question page receives these two props:
// formData={formData}  setFormData={setFormData}
```

---

## The Split

### Agent 1 — Foundation & Shared Layer

**Files owned exclusively:**
- `src/App.jsx`
- `src/components/GovukHeader.jsx`
- `src/components/GovukButton.jsx`
- `src/components/PhaseBanner.jsx`
- `src/components/GovukFooter.jsx`
- `src/pages/StartPage.jsx`
- `src/pages/AccessibilityStatementPage.jsx`

**Scope:**
- Add `useState` with the agreed `formData` shape to `App.jsx`
- Wire `formData` and `setFormData` as props to every page route
- Mount `PhaseBanner` and `GovukFooter` in `App.jsx` (currently TODO comments)
- Implement `GovukHeader` with "Green Home Grant" as the service name
- Implement `GovukButton` with a `variant="start"` option (renders chevron icon)
- Implement `PhaseBanner` with ALPHA tag and feedback link
- Implement `GovukFooter` with link to `/accessibility-statement`
- Implement `StartPage` — full description text, "Start now" button navigating to `/property-type`
- Implement `AccessibilityStatementPage` — PSBAR-structured content (see content plan §9)

**Early action:** Commit a minimal stub of `GovukButton` as soon as possible so Agents 2 and 3 can import it without errors before the full implementation is ready.

---

### Agent 2 — Questions 1–3

**Files owned exclusively:**
- `src/pages/PropertyTypePage.jsx`
- `src/pages/OwnershipPage.jsx`
- `src/pages/IncomePage.jsx`

**Scope:**
- Implement all three question pages using content from `docs/plans/2026-06-03-content-plan.md` §3
- Each page: radio buttons, GOV.UK error pattern (error summary + inline error), state read/write via props, Back link, Continue button navigating to next route
- Validation: show error if user submits without selecting an option
- Read the agreed `formData` shape — do not invent different field names

**Content reference (from content plan):**
- Question 1: `propertyType` — 5 options (detached, semi-detached, terraced, flat, bungalow)
- Question 2: `ownership` — 4 options (owner, private-renter, housing-association, council)
- Question 3: `incomeBand` — 3 options (low, mid, high)

---

### Agent 3 — Questions 4–5 & Check Answers

**Files owned exclusively:**
- `src/pages/InsulationPage.jsx`
- `src/pages/HeatingPage.jsx`
- `src/pages/CheckAnswersPage.jsx`

**Scope:**
- Implement questions 4 and 5 to the same standard as Agent 2
- Implement `CheckAnswersPage`: GOV.UK summary list, one row per question, "Change" link per row navigating back to that question, "Submit and see result" button navigating to `/result`
- Use the display-label mapping from `docs/plans/2026-06-03-content-plan.md` §4 to render human-readable answers (e.g. `"low"` → `"Under £31,000"`)

**Content reference (from content plan):**
- Question 4: `insulation` — 3 options (none, partial, full)
- Question 5: `heating` — 5 options (gas-boiler, oil-boiler, electric-storage, heat-pump, other)

---

### Agent 4 — Eligibility Logic, Result Page & Tests

**Files owned exclusively:**
- `src/utils/eligibility.js` *(new file)*
- `src/pages/ResultPage.jsx`
- `src/utils/eligibility.test.js` *(new file)*

**Scope:**
- Write `eligibility.js` as a pure function: takes `formData`, returns `{ result, measures }` where `result` is `"eligible"`, `"partial"`, or `"ineligible"` and `measures` is an array of available measure strings
- Implement the 5 priority-ordered rules from `docs/plans/2026-06-03-content-plan.md` §5
- Implement measures logic from §6 of the content plan
- Implement `ResultPage`: read `formData` from props, call eligibility function, render correct GOV.UK panel and body text for each outcome (see content plan §7)
- Write at least 5 unit tests covering the eligibility logic (all ineligible paths, eligible path, partial-renter path, partial-mid-income path, measures logic)
- This agent can work fully independently — no imports from other agents' files except the agreed `formData` shape via props

---

## File Ownership Summary

| File | Agent |
|------|-------|
| `src/App.jsx` | 1 |
| `src/components/GovukHeader.jsx` | 1 |
| `src/components/GovukButton.jsx` | 1 |
| `src/components/PhaseBanner.jsx` | 1 |
| `src/components/GovukFooter.jsx` | 1 |
| `src/pages/StartPage.jsx` | 1 |
| `src/pages/AccessibilityStatementPage.jsx` | 1 |
| `src/pages/PropertyTypePage.jsx` | 2 |
| `src/pages/OwnershipPage.jsx` | 2 |
| `src/pages/IncomePage.jsx` | 2 |
| `src/pages/InsulationPage.jsx` | 3 |
| `src/pages/HeatingPage.jsx` | 3 |
| `src/pages/CheckAnswersPage.jsx` | 3 |
| `src/utils/eligibility.js` *(new)* | 4 |
| `src/pages/ResultPage.jsx` | 4 |
| `src/utils/eligibility.test.js` *(new)* | 4 |
| `src/App.css` | nobody — do not modify |

---

## Conflict Risks & Mitigations

| File | Risk | Mitigation |
|------|------|------------|
| `src/App.jsx` | High if shared | Owned exclusively by Agent 1 — no risk |
| `src/App.css` | Medium if anyone adds styles | Use existing GOV.UK class names only; custom CSS should not be needed |
| `starter/AI_LOG.md` | Low — unavoidable | Each agent appends a clearly-labelled block at the bottom; do not insert mid-file. Conflicts are trivially resolved by accepting both appended blocks. |

---

## Notes for Collation

When the four agents' plans are merged into a single implementation plan:

1. This document defines *who builds what* — the collated plan should preserve these boundaries
2. The interface contract (formData shape + prop names) is the critical shared dependency — the collated plan should call it out prominently at the top
3. Agent 1's early GovukButton stub should be the first task in the collated plan so Agents 2 and 3 are unblocked immediately
4. Agent 4's eligibility function has no dependencies on other agents — it can be the first thing tested end-to-end

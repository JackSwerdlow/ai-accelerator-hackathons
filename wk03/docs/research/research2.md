# Research: Eligibility Service Design

## Objective
Understand how to design a GOV.UK multi-step eligibility service.

## Key Findings
- Finding 1:
- Finding 2:

## Implementation Ideas
- Idea 1:
- Idea 2:

## AI Usage Log
### Prompt
[What you asked Claude]

### Output
[What Claude generated]

### Changes Made
[What you modified and why]
==============================================================================================
Multi-Step Form Design

  Principles
  - One thing per page — single
  decision/input per screen reduces
  cognitive load and error rates
  (GOV.UK service standard).
  - Progressive disclosure — only ask
   what's needed for the current
  branch; skip irrelevant questions.
  - Forward-only by default, but
  always allow back navigation
  without data loss.
  - Save-and-resume for journeys >5
  minutes or requiring lookups.
  - Confirm-before-submit page (Check
   Your Answers) summarising all
  inputs with edit links.

  Recommendations
  - Model the journey as a finite
  state machine; each step is a route
   (/eligibility/property-type,
  /eligibility/tenure, etc.) — never
  modal/wizard-in-place.
  - Persist answers to the URL or
  session storage on each step so
  refresh doesn't wipe progress.
  - Show progress only if steps are
  fixed and >3; otherwise omit
  (GOV.UK research shows progress
  bars often mislead on branching
  journeys).

  GOV.UK Design Patterns

  Use the official building blocks
  - govuk-react or @govuk-react/* if
  you want React-native components,
  or wrap the canonical
  govuk-frontend package (Nunjucks
  templates compiled to HTML/CSS/JS).
  - Standard components: Radios,
  Checkboxes, Input, DateInput,
  ErrorSummary, BackLink, Button,
  SummaryList.

  Patterns to follow
  - Question pages: <h1> is the
  question itself (wrapped in <label>
   or <legend>).
  - Error pattern: ErrorSummary at
  top of page linking to each field;
  field-level error message in red
  below label; page title prefixed
  with "Error:".
  - "Check your answers" page using
  SummaryList before submit.
  - "Result" page that tells the user
   what happens next, not just
  yes/no.
  - Plain English — Flesch reading
  age 9 or below; no jargon.

  Accessibility (WCAG 2.2)

  Key new 2.2 criteria relevant here
  - 2.4.11 Focus Not Obscured (AA) —
  sticky headers/cookie banners must
  not hide focused inputs.
  - 2.5.7 Dragging Movements (AA) —
  avoid drag-only interactions.
  - 2.5.8 Target Size Minimum (AA) —
  interactive targets ≥24×24 CSS px.
  - 3.3.7 Redundant Entry (A) — don't
   ask users to re-enter info they've
   already given in the same journey.
  - 3.3.8 Accessible Authentication 
  (AA) — no cognitive function tests
  (puzzles, memorisation).

  Recommendations

  - Manage focus on route change:
  move focus to the <h1> (or
  ErrorSummary on validation
  this for you.
  - Set document.title per step
  ("Error: …" prefix when invalid).
  - All inputs need a
  programmatically associated label;
  group radios/checkboxes in
  <fieldset> + <legend>.
  - Announce dynamic changes with
  aria-live="polite" regions
  sparingly; prefer full page
  navigation.
  - Test with keyboard only, then
  with NVDA/VoiceOver, then with
  axe-core in CI.
  - Don't autofocus inputs —
  disorients screen reader users.

  State Management in React

  Principle: match the tool to the 
  data's lifetime and scope.

  Data: Current field value
  Lifetime: One step
  Tool: Local useState + uncontrolled

    form library
  ───────────────────────────────────
  ─
  Data: Journey answers
  Lifetime: Whole session
  Tool: URL params + sessionStorage,
    or a single context
  ───────────────────────────────────
  ─
  Data: Server eligibility result
  Lifetime: Until result page
  Tool: TanStack Query or route
  loader
  ───────────────────────────────────
  ─
  Data: User identity
  Lifetime: Cross-session
  Tool: Cookie/session, not React
    state

  Recommendations

  - Use React Router 6.4+ with 
  loaders/actions — colocates data
  with routes and gives you "Check
  Your Answers" for free via parent
  loader access. Or TanStack Router
  for type safety.
  - Use react-hook-form + Zod per
  validation that doubles as the
  eligibility rule definition.
  - Keep journey answers in one 
  reducer/store (Zustand or
  useReducer + Context) — not in 10
  separate states. Persist to
  sessionStorage via middleware so
  refresh survives.
  - Avoid Redux — overkill for a
  linear form.
  - Derive eligibility result; don't
  store it. Compute from answers on
  the result page so it's always 
  consistent.
  - Type the journey state as a
  discriminated union — branches
  become exhaustive at the type
  level.

  Architecture sketch

  /eligibility/start              →
  intro
  /eligibility/[step-id]          →
  one question, react-hook-form + Zod
  /eligibility/check-answers      →
  SummaryList, edit links return to
  step
  /eligibility/result             →
  derived from answers, copy depends
  on rule hit

  Single source of truth: a
  useEligibilityStore (Zustand)
  persisted to sessionStorage,
  validated against the Zod schema on
   hydrate.
   =========================================================================
   ## Key Findings

- One question per page improves usability
- Check answers page required before submission
- Accessibility is mandatory (labels, keyboard navigation)
- Validation should show clear errors

# Citizen-Facing Service Prototype -- Project Lab

## Project Brief

Your team works for a government department that needs to determine whether citizens qualify for a "Green Home Grant" – a fictional scheme offering funding toward home insulation and heat pump installation. Currently, citizens must phone a call centre and wait an average of 35 minutes to find out whether they are eligible. Your job is to build a digital service that replaces that phone call.

The service asks citizens a series of questions (property type, ownership status, household income band, existing insulation, current heating system) and tells them whether they qualify, what they qualify for, and what to do next. The service must follow GOV.UK design patterns, meet WCAG 2.2 AA accessibility requirements, and work on both mobile and desktop browsers.

## Objectives

Build a multi-step eligibility checker for the Green Home Grant scheme that follows GOV.UK design patterns and meets WCAG 2.2 AA accessibility requirements.

## Prerequisites

### Skills (from Weeks 1 and 2)

- Building React components using functional component syntax (W2 Day 1 AM)
- Managing component state with useState (W2 Day 1 AM)
- Handling side effects with useEffect (W2 Day 1 AM)
- Writing JSX with conditional rendering and list iteration (W2 Day 1 AM)
- Applying GOV.UK design patterns for typography, spacing, and form controls (W2 Day 1 PM)
- Implementing WCAG 2.2 AA compliance: semantic HTML, keyboard navigation, ARIA labels (W2 Day 1 PM)
- Using AI to scaffold React applications with routing (W2 Day 2 AM)
- Writing and running tests with Playwright or Vitest (W2 Day 2 PM)
- Code reviewing AI-generated code with an explain-before-you-commit workflow (W1 Day 1 PM)

### Tools and Access

- Node.js 18.x or later
- npm 9.x or later
- Claude CLI installed and authenticated
- A modern browser (Chrome, Firefox, or Edge) with developer tools
- Terminal access

## Setup

Then dependencies before starting:

```bash
npm install
```

Dependencies are not vendored into the repo; `npm install` pulls
them fresh from the package registry. Expect the install to take
30-60 seconds on a fast connection.

## Starter Scaffold

The starter you copied into your working directory contains:

| File / Directory | Purpose |
|-----------------|---------|
| `package.json` | Project dependencies: react, react-dom, react-router-dom, vite |
| `vite.config.js` | Vite configuration for React |
| `index.html` | HTML entry point with GOV.UK-compatible meta tags |
| `src/main.jsx` | React entry point rendering the App component |
| `src/App.jsx` | Router setup with routes for each page |
| `src/App.css` | GOV.UK CSS variables and base styles |
| `src/pages/StartPage.jsx` | Placeholder start page component |
| `src/pages/PropertyTypePage.jsx` | Placeholder question page |
| `src/pages/OwnershipPage.jsx` | Placeholder question page |
| `src/pages/IncomePage.jsx` | Placeholder question page |
| `src/pages/InsulationPage.jsx` | Placeholder question page |
| `src/pages/HeatingPage.jsx` | Placeholder question page |
| `src/pages/CheckAnswersPage.jsx` | Placeholder summary page |
| `src/pages/ResultPage.jsx` | Placeholder result page |
| `src/components/GovukHeader.jsx` | Placeholder header component |
| `src/components/GovukButton.jsx` | Placeholder button component |
| `src/components/PhaseBanner.jsx` | GOV.UK phase banner (alpha/beta tag + feedback link) |
| `src/components/GovukFooter.jsx` | GOV.UK footer with accessibility statement link |
| `src/pages/AccessibilityStatementPage.jsx` | PSBAR-structured accessibility statement stub |

> **Note:** This starter scaffold teaches GOV.UK patterns from first principles. Production services use [govuk-frontend](https://frontend.design-system.service.gov.uk/) or [govuk-react](https://github.com/govuk-react/govuk-react) for pre-built, tested components.

## Acceptance Criteria

- [ ] Start page displays with a title, description, and "Start now" button
- [ ] Clicking "Start now" navigates to the first question
- [ ] There are at least 5 question pages, each asking one question (one-thing-per-page)
- [ ] Each question page has a "Continue" button that navigates to the next question
- [ ] Users can navigate back to previous questions using a "Back" link
- [ ] A "Check your answers" page displays all responses in a summary list
- [ ] Each answer on the summary page has a "Change" link that returns to that question
- [ ] After confirming answers, a result page shows eligibility (eligible / not eligible / partial)
- [ ] All form inputs have associated `<label>` elements
- [ ] All interactive elements are reachable and operable with keyboard only (Tab, Enter, Space)
- [ ] Colour contrast meets 4.5:1 ratio for all text
- [ ] The layout reflows at 320px width without horizontal scrolling
- [ ] Client-side validation shows error messages for empty required fields
- [ ] Error messages follow GOV.UK pattern: error summary at top of page, inline error per field
- [ ] At least 5 unit tests pass for the eligibility logic
- [ ] An `AI_LOG.md` file documents 3+ AI-assisted development instances (open the seeded `AI_LOG.md` in your working directory and complete four fields per entry)

## Minimum Viable Submission

These six items define the floor. Every team must ship all six before pursuing stretch goals or polish.

1. **Multi-page question flow** (Requirement 1–2) – start page through to at least 5 question pages using one-thing-per-page
2. **Check-your-answers summary** (Requirement 3) – summary list with Change links for every answer
3. **Confirmation page** (Requirement 4) – clear eligibility outcome (eligible / not eligible / partial)
4. **GOV.UK Design System components** (Requirement 6) – correct typography, spacing, heading hierarchy using the provided CSS variables
5. **WCAG 2.2 AA compliance** (Requirement 5) – labelled inputs, keyboard navigation, 4.5:1 contrast, visible focus indicators
6. **AI usage log** (Requirement 10) – seeded `AI_LOG.md` with four completed fields per instance, minimum 3 instances

If you ship these six items cleanly, you have met the bar. Build outward from this floor.

## Assessment Rubric

| Criterion | Excellent | Good | Needs Work |
|-----------|-----------|------|------------|
| Functionality | All 5+ questions work, eligibility logic handles all paths, check-answers page complete | Core question flow works, eligibility logic covers main paths | Incomplete flow or broken navigation |
| Code quality | Components are small and focused, state management is clear, no duplicated logic | Reasonable structure with minor duplication | Large monolithic components, tangled state |
| AI effectiveness | `AI_LOG.md` shows 3+ instances with clear before/after, critical review of AI output | `AI_LOG.md` present with some detail | `AI_LOG.md` missing or superficial |
| Accessibility | Passes manual keyboard test, all inputs labelled, error summary present, 4.5:1 contrast verified | Most inputs labelled, partial keyboard support | Significant accessibility gaps |
| GOV.UK visual compliance | Correct typography scale, spacing, start page pattern, confirmation pattern | Recognisably GOV.UK-styled with minor deviations | Generic styling, not recognisably GOV.UK |
| Service-Standard conformance | Accessibility statement + phase banner + footer + cookie notice | Accessibility statement + one other signal | None of the discoverable signals present |

## Day 1 Target

By end of Day 1, you should have:

- [ ] Start page rendering and navigating to the first question
- [ ] All 5+ question pages rendering with navigation (Continue / Back)
- [ ] Form state persisted across pages (answers not lost when navigating)
- [ ] Eligibility logic function written (even if not all edge cases are covered)
- [ ] At least one complete path from start to result page working

## Teardown

1. Stop the Vite dev server (Ctrl+C in the terminal)
2. No cloud resources or containers to clean up

## Hints

<details>
<summary>When teams get stuck</summary>

| Problem | Response |
|---------|----------|
| Team cannot agree on architecture | Start with the GOV.UK start page and build one question at a time. Ship a working page before debating the overall design. The starter scaffold already has the routes — follow them. |
| Form state is lost between pages | Lift state into the App component. All form data lives in one `useState` object at the top level, passed down via props. See the architecture hint below. |
| Team is spending too long on styling | The starter CSS already provides GOV.UK variables and class names. Use `govuk-heading-xl`, `govuk-body`, `govuk-button`, etc. Custom CSS is almost never needed for this brief. |
| Eligibility logic is tangled into components | Extract it into a pure function in its own file (`src/utils/eligibility.js`). The function takes the form data object and returns a result string. This also makes it testable without rendering any components. |
| Team has finished early and wants to add features | Prioritise stretch goals in this order: save-and-return with localStorage, a second eligibility pathway, Playwright end-to-end tests. Discourage cosmetic additions that do not demonstrate new capability. |

</details>

<details>
<summary>Architecture suggestion</summary>

Hold all form answers in a single state object at the App level. Pass the state and a setter function down to each page via props or React context. Each page reads its relevant field and updates it on "Continue". This avoids the need for a state management library.

```
formData = {
  propertyType: "",
  ownership: "",
  incomeBand: "",
  insulation: "",
  heating: ""
}
```

The eligibility function takes this object and returns a result string. Keep it as a pure function in its own file so you can test it independently.

</details>

<details>
<summary>If you are stuck on navigation between pages</summary>

Use react-router-dom's `useNavigate` hook. Each page's "Continue" handler saves the answer to state and then calls `navigate("/next-page-path")`. The "Back" link uses `navigate(-1)` or an explicit path to the previous question.

</details>

<details>
<summary>If GOV.UK styling looks wrong</summary>

The starter CSS uses CSS custom properties matching GOV.UK values. Check that your components use the correct class names: `govuk-heading-xl`, `govuk-body`, `govuk-button`, `govuk-form-group`, `govuk-label`, `govuk-input`, `govuk-radios`. The styles for these classes are defined in `src/App.css`.

</details>

## Stretch Goals

- Add a "Save and return" feature using `localStorage` so users can resume a partially completed form
- Add a second eligibility pathway (e.g., tenant vs. owner routes with different questions)
- Add end-to-end tests with Playwright covering the full user journey
- Generate an accessible PDF summary of the eligibility result

### Stretch challenge: Semantic intent matching

A free-text "what do you need help with?" entry point that maps natural-language input to the right service intent — e.g., "I need help with my boiler" maps to a "heating-system support" entry in the service catalogue. Browser-local, no API key, no cost. Foreshadows the Week 5 RAG module.

1. Install `@xenova/transformers` in your existing React app
2. Encode the service-catalogue titles + descriptions once at startup (sentence-transformers MiniLM is a reasonable default)
3. On user input, encode the query and find the top-3 most cosine-similar service entries
4. Display the matched services with a similarity-score badge
5. Reflect in `AI_LOG.md`: where did the AI help (model selection, similarity-threshold tuning)? Where did it not (vector-DB choice — none needed; this is in-memory)?

## Resources

- [GOV.UK Design System](https://design-system.service.gov.uk/) – components and patterns
- [GOV.UK Design System: Question pages](https://design-system.service.gov.uk/patterns/question-pages/) – one-thing-per-page pattern
- [GOV.UK Design System: Check answers](https://design-system.service.gov.uk/patterns/check-answers/)
- [GOV.UK Design System: Confirmation pages](https://design-system.service.gov.uk/patterns/confirmation-pages/)
- [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/?currentsidebar=%23col_overview&levels=aaa) – filter to Level AA
- [Vite documentation](https://vitejs.dev/)
- [React Router v6 documentation](https://reactrouter.com/en/main)
- Week 1 and Week 2 module slides (your prerequisite content)

> **Teaching scaffold vs production scaffold.** The starter scaffold uses plain CSS variables and React components to teach GOV.UK patterns from first principles. Production government services use [govuk-frontend](https://frontend.design-system.service.gov.uk/) (the official npm package with Nunjucks/HTML components) or [govuk-react](https://github.com/govuk-react/govuk-react) (a community React binding). Both ship pre-built, tested components that handle accessibility, responsive behaviour, and print styles. The teaching scaffold omits these to ensure you understand the underlying markup and WCAG requirements rather than relying on a library to handle them.

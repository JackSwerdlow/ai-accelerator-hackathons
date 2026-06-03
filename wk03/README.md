# Citizen-Facing Service Prototype -- Project Lab

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

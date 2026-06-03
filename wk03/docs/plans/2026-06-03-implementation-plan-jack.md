# Green Home Grant — Implementation Plan

**Author:** Agent-Jack  
**Date:** 2026-06-03  
**Status:** Ready for execution

> **For agents executing this plan:** Use `superpowers:executing-plans` or `superpowers:subagent-driven-development` to work through tasks. Mark each checkbox as it completes.

**References:**
- Content (copy, questions, rules, outcomes): `docs/plans/2026-06-03-content-plan.md`
- Standards research: `docs/research.md`
- Interface contract: see §3 below

---

## 1. Design Philosophy

This is a citizen-facing government service. The rubric rewards *recognisably GOV.UK-styled* output. The goal is not to bend the design system — it is to **execute it with precision and care that the starter scaffold does not**.

The starter gives us CSS variables and class names. A polished execution means:
- Every component renders the GOV.UK pattern faithfully (no improvised structural HTML)
- Visual weight and spacing match the GOV.UK examples exactly
- No missing details: back link before `<h1>`, hint text below legend not label, error summary before heading, panel only on result page
- Three specific **elevation choices** that stay within GOV.UK standards:
  1. **Progress indicator** — "Step X of 5" above each question heading (GOV.UK-sanctioned, not in the starter)
  2. **Page transitions** — 150 ms CSS fade + 8 px upward translate on route change (non-jarring, motion-safe-guarded)
  3. **Result page icons** — inline SVG glyph (tick / info / cross) inside the panel body per outcome

Everything else is GOV.UK by the book. No custom fonts, no palette deviations, no structural surprises.

---

## 2. Extend `App.css` or add a sibling?

The work-split plan marked `App.css` as "do not modify." That made sense when it was a frozen teaching scaffold. For this plan, we need styles for:
- The progress indicator
- Page-transition wrapper
- SVG icon sizing in the panel

**Decision:** Add a new file `src/progress.css` for the progress indicator and transition styles, imported in `App.jsx`. Do not modify `App.css`. This preserves the teaching scaffold for inspection while keeping new styles in a named place.

---

## 3. Agreed Interface Contract

All components must use exactly this formData shape — do not invent new field names.

```js
// App.jsx
const [formData, setFormData] = useState({
  propertyType: "",
  ownership: "",
  incomeBand: "",
  insulation: "",
  heating: ""
});

// Every question page and result page receives:
// formData={formData}  setFormData={setFormData}
```

The eligibility function signature:

```js
// src/utils/eligibility.js
function checkEligibility(formData)
// Returns: { result: "eligible" | "partial" | "ineligible", measures: string[] }
```

---

## 4. New File to Create

In addition to completing the existing stubs, one new directory and two new files are needed:

| New path | Purpose |
|----------|---------|
| `src/utils/eligibility.js` | Pure eligibility function |
| `src/utils/eligibility.test.js` | Unit tests (Vitest) |
| `src/progress.css` | Progress indicator + transition styles |
| `src/components/ProgressIndicator.jsx` | "Step X of 5" component |

---

## 5. Task Checklist

Tasks are grouped by concern, not by agent, to allow flexible parallel assignment.

### 5.1 Shared Infrastructure

- [ ] **App.jsx — state + layout wiring**
  - Add `useState` with the interface-contract `formData` shape
  - Pass `formData` and `setFormData` as props to every `<Route>` element
  - Mount `<PhaseBanner phase="alpha" feedbackHref="#" />` between header and width-container
  - Mount `<GovukFooter />` after `</main>`
  - Import `./progress.css`

- [ ] **`src/progress.css` — transitions and progress indicator styles**
  - `.page-transition-enter { opacity: 0; transform: translateY(8px); }`
  - `.page-transition-enter-active { opacity: 1; transform: translateY(0); transition: opacity 150ms ease, transform 150ms ease; }`
  - `@media (prefers-reduced-motion: reduce) { .page-transition-enter-active { transition: none; } }`
  - `.govuk-step-indicator { font-size: 16px; color: var(--govuk-dark-grey); margin-bottom: var(--govuk-spacing-2); }`

- [ ] **`GovukHeader.jsx`** — render the full GOV.UK header:
  ```jsx
  <header className="govuk-header" role="banner">
    <div className="govuk-header__container govuk-width-container">
      <div className="govuk-header__logo">
        <a href="/" className="govuk-header__link govuk-header__link--homepage">GOV.UK</a>
      </div>
      <div className="govuk-header__content">
        <a href="/" className="govuk-header__link govuk-header__service-name">
          Green Home Grant
        </a>
      </div>
    </div>
  </header>
  ```

- [ ] **`GovukButton.jsx`** — accept `variant`, `onClick`, `children`, `type` props:
  - Default variant: renders `<button className="govuk-button">`
  - `variant="start"`: adds class `govuk-button--start`, renders chevron SVG after children:
    ```jsx
    <svg className="govuk-button__start-icon" aria-hidden="true" ...>
      <path d="M0 0l9 5-9 5z" />
    </svg>
    ```

- [ ] **`PhaseBanner.jsx`** — render phase tag + feedback text:
  ```jsx
  <div className="govuk-phase-banner">
    <p className="govuk-phase-banner__content">
      <strong className="govuk-tag govuk-phase-banner__content__tag">alpha</strong>
      <span className="govuk-phase-banner__text">
        This is a new service – your <a href={feedbackHref}>feedback</a> will help us to improve it.
      </span>
    </p>
  </div>
  ```
  CSS: use App.css's existing variable set; add `.govuk-phase-banner` rules inline in the component via a `<style>` tag or note them in `progress.css`.

- [ ] **`GovukFooter.jsx`** — render footer with accessibility statement link and cookies link (see content plan §10)

- [ ] **`ProgressIndicator.jsx`** — accept `current` and `total` props:
  ```jsx
  <p className="govuk-step-indicator" aria-label={`Step ${current} of ${total}`}>
    Step {current} of {total}
  </p>
  ```

---

### 5.2 Start Page

- [ ] **`StartPage.jsx`** — full implementation per content plan §2:
  - `<h1 className="govuk-heading-xl">Check if you can get a Green Home Grant</h1>`
  - Three `<p className="govuk-body">` paragraphs from content plan
  - Bullet list of what users need to know (`<ul className="govuk-list govuk-list--bullet">`)
  - `<GovukButton variant="start" onClick={() => navigate('/property-type')}>Start now</GovukButton>`
  - No back link, no progress indicator on start page

---

### 5.3 Question Pages (all five follow the same pattern)

Each question page must:
1. Render `<a className="govuk-back-link" href={prevRoute}>Back</a>` above the fieldset
2. Render `<ProgressIndicator current={n} total={5} />` below the back link
3. If validation error: render error summary (`<div className="govuk-error-summary">`) before the heading
4. Wrap radios in a `<fieldset className="govuk-fieldset">` with a `<legend>` containing the heading
5. Show inline error above the radio group when submitted empty
6. On Continue: validate → update `formData` → navigate to next route

**Hover enhancement:** Each `.govuk-radios__item` gets a subtle left-border accent on hover:
```css
/* In progress.css */
.govuk-radios__item:hover {
  background-color: var(--govuk-light-grey);
  border-left: 4px solid var(--govuk-blue);
  padding-left: 8px;
}
```

- [ ] **`PropertyTypePage.jsx`** — Question 1 (`/property-type`)
  - Step 1 of 5
  - 5 radio options from content plan §3-Q1
  - Back: `/` | Continue: `/ownership`

- [ ] **`OwnershipPage.jsx`** — Question 2 (`/ownership`)
  - Step 2 of 5
  - Hint text below fieldset legend: "If you own your home with a mortgage, select 'I own my home'."
  - 4 radio options from content plan §3-Q2
  - Back: `/property-type` | Continue: `/income`

- [ ] **`IncomePage.jsx`** — Question 3 (`/income`)
  - Step 3 of 5
  - Hint text: "Include the income of all adults living in your home, before tax and other deductions."
  - 3 radio options from content plan §3-Q3
  - Back: `/ownership` | Continue: `/insulation`

- [ ] **`InsulationPage.jsx`** — Question 4 (`/insulation`)
  - Step 4 of 5
  - Hint text: "If you are not sure, check your Energy Performance Certificate (EPC)..."
  - 3 radio options from content plan §3-Q4
  - Back: `/income` | Continue: `/heating`

- [ ] **`HeatingPage.jsx`** — Question 5 (`/heating`)
  - Step 5 of 5
  - Hint text: "Select the system that heats most of your home."
  - 5 radio options from content plan §3-Q5
  - Back: `/insulation` | Continue: `/check-answers`

---

### 5.4 Check Your Answers Page

- [ ] **`CheckAnswersPage.jsx`** (`/check-answers`) — per content plan §4:
  - `<h1 className="govuk-heading-l">Check your answers</h1>`
  - `<p className="govuk-body">Check your answers before you find out if you are eligible.</p>`
  - GOV.UK summary list (`<dl className="govuk-summary-list">`) with 5 rows:
    - Property type | Ownership status | Annual household income | Current insulation | Current heating system
  - Each row: `<dd className="govuk-summary-list__actions"><a href={changeRoute}>Change</a></dd>`
  - Display labels: use the mapping table from content plan §4 to convert stored values to human-readable strings (e.g. `"low"` → `"Under £31,000"`)
  - `<GovukButton onClick={() => navigate('/result')}>Submit and see result</GovukButton>`
  - No progress indicator on this page
  - Back link: `/heating`

---

### 5.5 Eligibility Logic

- [ ] **`src/utils/eligibility.js`** — pure function per content plan §5 and §6:
  ```js
  export function checkEligibility(formData) {
    // Rules evaluated in priority order — first match wins
    // Rule 1: income high → ineligible
    // Rule 2: full insulation AND heat pump → ineligible
    // Rule 3: any renter → partial
    // Rule 4: owner + mid income → partial
    // Rule 5: owner + low income → eligible
    // Default → ineligible
    //
    // Measures (independent of result):
    // - "Loft insulation" if insulation !== "full" AND propertyType !== "flat"
    // - "Internal wall insulation" if insulation !== "full"
    // - "Air source heat pump installation" if heating !== "heat-pump"
    return { result, measures };
  }
  ```
  Export `checkEligibility` as a named export (not default) — simplifies test imports.

- [ ] **`src/utils/eligibility.test.js`** — minimum 5 tests using Vitest:
  - Rule 1: high income → ineligible
  - Rule 2: full insulation + heat pump → ineligible
  - Rule 3: private renter → partial (regardless of income)
  - Rule 4: owner + mid income → partial
  - Rule 5: owner + low income → eligible
  - Bonus: housing-association renter → partial
  - Bonus: measures array omits loft insulation for flats
  - Bonus: measures array includes all three measures for low-income owner with no insulation and gas boiler

---

### 5.6 Result Page

- [ ] **`ResultPage.jsx`** (`/result`) — per content plan §7:
  - Call `checkEligibility(formData)` at render time
  - Render GOV.UK panel with outcome-specific class and icon:

  **ELIGIBLE:**
  ```jsx
  <div className="govuk-panel govuk-panel--confirmation">
    <h1 className="govuk-panel__title">You may be eligible for a Green Home Grant</h1>
    <div className="govuk-panel__body">
      {/* Tick SVG icon */}
      <svg aria-hidden="true" width="40" height="40" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="20" fill="white" fillOpacity="0.2"/>
        <path d="M10 20l7 7 13-13" stroke="white" strokeWidth="3" fill="none"/>
      </svg>
      <p>You may qualify for a grant of up to £10,000</p>
    </div>
  </div>
  ```

  **PARTIAL:**
  ```jsx
  <div className="govuk-panel govuk-panel--confirmation" style={{ background: 'var(--govuk-dark-grey)' }}>
    <h1 className="govuk-panel__title">You may be partially eligible for a Green Home Grant</h1>
    <div className="govuk-panel__body">
      {/* Info SVG icon */}
      <svg aria-hidden="true" width="40" height="40" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="20" fill="white" fillOpacity="0.2"/>
        <text x="20" y="27" textAnchor="middle" fill="white" fontSize="22" fontWeight="bold">i</text>
      </svg>
    </div>
  </div>
  ```

  **INELIGIBLE:**
  ```jsx
  <div className="govuk-panel govuk-panel--not-eligible">
    <h1 className="govuk-panel__title">You are not eligible for a Green Home Grant</h1>
    <div className="govuk-panel__body">
      {/* Cross SVG icon */}
      <svg aria-hidden="true" width="40" height="40" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="20" fill="white" fillOpacity="0.2"/>
        <path d="M13 13l14 14M27 13l-14 14" stroke="white" strokeWidth="3"/>
      </svg>
    </div>
  </div>
  ```

  - Measures bullet list (when result is eligible or partial + owner): `<ul className="govuk-list govuk-list--bullet">`
  - Body paragraphs and next-steps section per content plan §7 — use `result` and `formData.ownership` to pick the right variant
  - "Find an approved installer" link (`href="#"`)
  - No back link, no progress indicator
  - If `formData` has empty fields (direct URL access): redirect to `/` using `useNavigate`

---

### 5.7 Accessibility Statement Page

- [ ] **`AccessibilityStatementPage.jsx`** (`/accessibility-statement`) — per content plan §9:
  - `<h1 className="govuk-heading-l">Accessibility statement for Green Home Grant eligibility checker</h1>`
  - PSBAR-structured body using content plan §9 values
  - Contact email rendered as a `mailto:` link

---

### 5.8 Page Transitions (enhancement)

- [ ] Wrap the `<Routes>` output in a transition container. Since react-router-dom v6 does not natively expose an enter/exit hook, the simplest approach is a CSS animation on `<main>`:
  ```css
  /* progress.css */
  @keyframes page-enter {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .govuk-main-wrapper {
    animation: page-enter 150ms ease forwards;
  }
  @media (prefers-reduced-motion: reduce) {
    .govuk-main-wrapper { animation: none; }
  }
  ```
  This triggers on every route change because React replaces the component tree, re-mounting `<main>`. No library required. Add the `animation` rule to `progress.css`, not `App.css`.

---

## 6. GOV.UK Compliance Checklist

Run through this before calling any task "done":

**Structure**
- [ ] `<h1>` is the first heading on every page and matches the `<title>`
- [ ] Error pages prefix `<title>` with `"Error: "`
- [ ] `<legend>` (not `<label>`) wraps the question heading on radio pages
- [ ] Hint text uses `<div id="…-hint" className="govuk-hint">` and is referenced by `aria-describedby`
- [ ] Error messages use `<p id="…-error" className="govuk-error-message">` with a `<span className="govuk-visually-hidden">Error:</span>` prefix
- [ ] Error summary links (`<a href="#fieldId">`) point to the first errored field

**Keyboard / focus**
- [ ] Tab order follows visual reading order
- [ ] All interactive elements show the GOV.UK yellow focus ring (`:focus` outline: 3px solid #ffdd00)
- [ ] Back link is the first focusable element after the skip link

**Responsive**
- [ ] Layout reflows at 320 px with no horizontal scroll
- [ ] Radio label text wraps without overflow

**Motion**
- [ ] Page transition animation is disabled under `prefers-reduced-motion: reduce`
- [ ] No other animations fire at startup

---

## 7. Test Strategy

| Layer | Tool | Target |
|-------|------|--------|
| Eligibility unit tests | Vitest | ≥ 5 tests in `eligibility.test.js`; all rules + measures cases |
| Component render smoke | Vitest + React Testing Library (optional) | StartPage renders with correct heading |
| End-to-end happy path | Playwright (stretch) | Full flow: start → result (eligible) |

Run tests with:
```bash
cd wk03/starter
npm test
```

---

## 8. Definition of Done

The build is complete when all of the following are true:

- [ ] All 5 question pages navigate in sequence, with state persisted across pages
- [ ] Validation error pattern (summary + inline) fires on every question page when submitted empty
- [ ] Check-your-answers page shows all 5 answers with human-readable labels and Change links
- [ ] Result page renders the correct outcome for all three paths (eligible, partial, ineligible)
- [ ] Measures list is correct for at least one eligible test case
- [ ] GOV.UK compliance checklist above is fully ticked
- [ ] `npm test` passes all eligibility tests (≥ 5)
- [ ] `AI_LOG.md` has ≥ 3 entries with all four required fields
- [ ] Phase banner, footer with accessibility statement link, and accessibility statement page are present
- [ ] No TypeScript / lint errors (run `npm run build` — should complete without errors)

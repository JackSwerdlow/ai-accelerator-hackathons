# Green Home Grant Eligibility Checker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Do not change any decision in §3 or §4 without flagging it back to the user.**

**Goal:** Build a React + Vite multi-step eligibility checker for the (fictional) Green Home Grant scheme that follows GOV.UK design patterns and meets WCAG 2.2 AA, replacing the placeholder starter scaffold in `wk03/starter/` with a working service.

**Architecture:** Single-page React app, client-side routing via `react-router-dom` v6, single React Context for answer state, generic `<QuestionPage>` component for the five question screens, pure `eligibility()` function for rules, Vitest + React Testing Library for tests. Content is fully specified — do not invent copy or rules.

**Tech Stack:** React 18.2, react-router-dom 6.20, Vite 5, Vitest + @testing-library/react (to be added), GOV.UK CSS variables (the teaching scaffold in `App.css` — no `govuk-frontend` npm package).

---

## 1. Goal and Scope

Build a five-question eligibility checker that opens with a GOV.UK start page, walks the user through five one-thing-per-page questions (property type, ownership, income band, insulation, heating), summarises their answers on a check-answers page, and renders one of three outcomes (eligible / partial / ineligible) with the right next steps. Reachable from the footer: an accessibility statement page. The service must meet the README acceptance criteria, the WCAG 2.2 AA criteria enumerated in `docs/research/research.md` §4, and the GOV.UK Design System patterns enumerated in `docs/research/research.md` §5. All copy, options, rules, and result variants are fixed by `docs/plans/2026-06-03-content-plan.md`.

## 2. References

| Source | Used for |
|---|---|
| `wk03/docs/plans/2026-06-03-content-plan.md` | Authoritative copy, question options, eligibility rules (§5), measures logic (§6), result-page variants (§7), accessibility-statement fields (§9), footer links (§10) |
| `wk03/docs/research/research.md` | Standards baseline: PSBAR §2.1, WCAG 2.2 SC list §4.2–§4.3, GOV.UK Design System patterns §5, accessibility statement structure §7 |
| `wk03/docs/research/research2.md` | Reinforces focus-management discipline; supports "Step X of 5" on this linear fixed-length journey; flags `sessionStorage` persistence as a viable stretch |
| `wk03/docs/plans/2026-06-03-implementation-plan-jack.md` | Source for the "Step X of 5" indicator, motion-safe page transition |
| `wk03/docs/plans/2026-06-03-implementation-plan-Agent-SK.md` | Source for FormContext, generic QuestionPage, `router.jsx` split, reason-coded eligibility return, `?from=check-answers` flow, contextual-help tiers |
| `wk03/starter/` | Scaffold to fill in (do not delete files; modify in place) |
| `wk03/CLAUDE.md`, repo-root `CLAUDE.md`, `/home/lab-admin/Documents/CLAUDE.md` | Workflow rules: agent identity in commits, `AI_LOG.md` entry per task, `git pull --rebase` discipline, no `localhost` (use `http://<hostname>:<PORT>`) |

## 3. Architecture Decisions

| # | Decision | Rationale | Source |
|---|---|---|---|
| AD1 | Single `FormContext` at `App.jsx` level, accessed via `useFormContext()` hook | Avoids prop drilling across 9 routes; single source of truth; cheaper to add a `?from=check-answers` consumer | SK plan §2 |
| AD2 | One generic `<QuestionPage>` component; the five question pages are thin wrappers passing props | Five near-identical pages would drift; one component keeps the GOV.UK pattern identical everywhere | SK plan §3.4 |
| AD3 | Routes extracted to `src/router.jsx` (single `<AppRoutes />` export) | `App.jsx` stays focused on chrome + providers; route table is grep-able | SK plan §3a.3 |
| AD4 | `eligibility(answers)` returns `{ outcome, reason, measures }` | Result page needs the reason to pick the right copy variant per content plan §7; computing reason at the source is cheaper than re-deriving | SK plan §3.3 |
| AD5 | `src/displayLabels.js` exports `labelFor(field, value)` and `measuresFor(answers)`, consumed by CheckAnswers and Result pages | One mapping table per content plan §4 + §6, used twice — share it | SK plan §6.4 |
| AD6 | Change-link flow uses `?from=check-answers` query string; `<QuestionPage>` detects it and overrides its `onContinueNavigateTo` | Standard react-router pattern, satisfies WCAG 3.3.7 (Redundant Entry) | SK plan §3.4 |
| AD7 | Skip-to-main-content link as the first focusable element | WCAG 2.4.1 | SK plan §A4 |
| AD8 | On every route change, focus moves to `<main id="main-content">` (made focusable with `tabIndex={-1}`). On validation error, focus moves to the error summary | Live GOV.UK services focus the `<main>` wrapper on SPA navigation rather than the `<h1>` — focusing an H1 inside a `<legend>` causes NVDA/JAWS to double-announce, and `<main>` gives screen readers a clean landmark to enter the new page from. Skip-link, `document.title`, and error-summary focus remain as additional signals | SK plan §3.4 (error focus) + best-practice from live services |
| AD9 | `document.title` set per page via `useEffect`, prefixed with `Error: ` when an error is visible | WCAG 2.4.2 | SK plan §6.3 |
| AD10 | CheckAnswers redirects to the first unanswered question if any answer is empty; Result redirects to `/` if any answer is empty | Stops a deep-linked user from seeing a half-result | SK plan §C4, Jack plan §5.6 |
| AD11 | Vitest + @testing-library/react + jsdom — added to the existing scaffold | The starter has no test config; we add the minimum that runs locally and in CI | SK plan §D1 |
| AD12 | Keep the "Step X of 5" indicator above each question's H1 (Jack plan elevation) | This journey is linear and fixed at 5 steps — the case research2 explicitly allows ("Show progress only if steps are fixed and >3") | Jack plan §1, research2 |
| AD13 | Keep a motion-safe 150 ms page-enter CSS transition (Jack plan elevation) | Adds polish without leaving the Design System; gated by `prefers-reduced-motion` | Jack plan §1, §5.8 |
| AD14 | Add a `<details>` "Help with this question" block on Income, Insulation, Heating | Tier-2 of SK's contextual-help model; keyboard- and SR-accessible; safer than tooltips | SK plan §3a.8 |
| AD15 | No new state library (Redux/Zustand/Recoil/jotai); no react-hook-form; no Zod; no TanStack Query/Router | Service scope is five radio questions — context is enough; the teaching scaffold mandates hand-written components | SK plan §3a.1 |
| AD16 | No SVG icons inside the GOV.UK result panel, no radio-hover left-border accent | Both are deviations from the Design System — GOV.UK fidelity wins ties | (See §8) |
| AD17 | Per-agent lane assignments and per-agent change-logs are explicitly out of scope for this plan | The work split is handled in a separate step after this plan is approved | User direction |

## 4. Shared Contracts

These are the API surfaces every file must agree on. Once `src/contexts/FormContext.jsx` is committed, the contract is real.

### 4.1 `Answers` shape

```js
// Authoritative shape — every page reads/writes via this exact set of keys.
const INITIAL_ANSWERS = {
  propertyType: "", // "" | "detached" | "semi-detached" | "terraced" | "flat" | "bungalow"
  ownership:    "", // "" | "owner" | "private-renter" | "housing-association" | "council"
  incomeBand:   "", // "" | "low" | "mid" | "high"
  insulation:   "", // "" | "none" | "partial" | "full"
  heating:      "", // "" | "gas-boiler" | "oil-boiler" | "electric-storage" | "heat-pump" | "other"
};
```

Empty string means "not yet answered". Pages treat `""` as "no preselection".

### 4.2 `useFormContext()` hook

```js
// Export from: src/contexts/FormContext.jsx
const { answers, setAnswer, resetAnswers } = useFormContext();

// answers       — the object in §4.1
// setAnswer(field, value)  — updates one field; field must be a key of answers
// resetAnswers()           — clears all fields back to ""
// useFormContext() throws if called outside <FormProvider>
```

### 4.3 `eligibility(answers)` function

```js
// Export from: src/eligibility.js — pure function, no side effects, no I/O.
import { eligibility } from "./eligibility";

const { outcome, reason, measures } = eligibility(answers);
// outcome:  "eligible" | "partial" | "ineligible"
// reason:   reason code (see table below)
// measures: string[] — display labels (e.g. "Loft insulation")
```

Rules per content plan §5, evaluated in priority order — first match wins:

| Priority | Rule | `outcome` | `reason` |
|---|---|---|---|
| 1 | `incomeBand === "high"` | `ineligible` | `"income-too-high"` |
| 2 | `insulation === "full"` AND `heating === "heat-pump"` | `ineligible` | `"no-measures-needed"` |
| 3 | `ownership` in `{private-renter, housing-association, council}` | `partial` | `"renter"` |
| 4 | `ownership === "owner"` AND `incomeBand === "mid"` | `partial` | `"owner-mid-income"` |
| 5 | `ownership === "owner"` AND `incomeBand === "low"` | `eligible` | `"owner-low-income"` |
| — | Default (no rule matched, or any answer empty) | `ineligible` | `"default"` |

Measures (per content plan §6) — computed independently of outcome:

| Condition | Measure label appended |
|---|---|
| `insulation !== "full"` AND `propertyType !== "flat"` | `"Loft insulation"` |
| `insulation !== "full"` | `"Internal wall insulation"` |
| `heating !== "heat-pump"` | `"Air source heat pump installation"` |

`eligibility({})` and `eligibility({ propertyType: "boat" })` must return `{ outcome: "ineligible", reason: "default", measures: [...] }` without throwing.

### 4.4 `<QuestionPage>` component

```jsx
// Export from: src/components/QuestionPage.jsx
<QuestionPage
  pageTitle="What type of property do you live in?"
  fieldName="propertyType"
  step={1}
  totalSteps={5}
  options={[
    { value: "detached",      label: "Detached house" },
    { value: "semi-detached", label: "Semi-detached house" },
    // ...
  ]}
  hint="Optional plain-text hint, shown below the legend"   // optional
  helpDetails={{                                             // optional Tier-2 help
    summaryText: "Help with annual household income",
    bodyText: "Include earnings from employment, self-employment, …",
  }}
  errorMessage="Select the type of property you live in"
  backHref="/"
  onContinueNavigateTo="/ownership"
/>
```

Behaviour the component owns (so the five pages get all of this for free):

1. Reads `answers[fieldName]` from context to pre-select on mount.
2. Updates `answers[fieldName]` via `setAnswer` on radio change.
3. Renders the GOV.UK back link above main content.
4. Renders the GOV.UK fieldset + legend-as-H1 pattern (see §6.1).
5. Renders `<ProgressIndicator current={step} total={totalSteps} />` between the back link and the H1 (above the error summary if one is shown). See §6.9 for placement and class.
6. On Continue with no selection: sets local error state, renders the error pattern (§6.2), moves keyboard focus to the error summary (`tabIndex="-1"` + `ref.focus()`).
7. On Continue with a selection: navigates to `onContinueNavigateTo`, OR to `/check-answers` if the URL contains `?from=check-answers`.
8. Maintains `document.title` per §6.3 (`"<pageTitle> - Green Home Grant - GOV.UK"`, prefixed with `Error: ` while an error is visible).

### 4.5 Routes

Defined in `src/router.jsx` as `<AppRoutes />`. Mounted by `App.jsx` inside the existing `<BrowserRouter>` already established in `src/main.jsx`.

| Path | Page component |
|---|---|
| `/` | `StartPage` |
| `/property-type` | `PropertyTypePage` |
| `/ownership` | `OwnershipPage` |
| `/income` | `IncomePage` |
| `/insulation` | `InsulationPage` |
| `/heating` | `HeatingPage` |
| `/check-answers` | `CheckAnswersPage` |
| `/result` | `ResultPage` |
| `/accessibility-statement` | `AccessibilityStatementPage` |

## 5. Coding Standards

| Rule | Notes |
|---|---|
| **State management** | Form answers live only in `FormContext` (§4.1). Local `useState` is fine for transient UI state (error flags, etc.). No state libraries. |
| **Derive, don't store** | `eligibility(answers)`, measures, display labels are all computed at render time. Never cache the outcome. |
| **Rules of Hooks** | Top-level only, never inside conditionals/loops/early-returns. Effect dep arrays must be complete; no `eslint-disable` of `react-hooks/exhaustive-deps`. |
| **Allowed hooks** | `useState`, `useEffect`, `useRef`, `useContext`, plus router hooks `useNavigate`, `useLocation`, `useSearchParams`, `useParams`. `useMemo`/`useCallback` only with a measured reason. |
| **Custom hooks** | Live in `src/hooks/`, named `useXxx.js`, exported function `useXxx`. |
| **Focus discipline** | On every route change, focus moves to `<main id="main-content">` (which carries `tabIndex={-1}` so it can receive programmatic focus). On validation error, focus moves to the error summary (`tabIndex={-1}` + `ref.focus()` on mount). The skip link is the entry point on every page. **Do not auto-focus inputs, legends, or H1s** — auto-focusing an H1 inside a `<legend>` causes screen readers to double-announce. |
| **Document title** | Every page sets `document.title` via `useEffect` to `"<pageTitle> - Green Home Grant - GOV.UK"`, prefixed `Error: ` when an error is visible. |
| **Naming** | Components: `PascalCase`. Non-component files: `camelCase.js`. Vars/funcs/hooks: `camelCase`. Constants: `UPPER_SNAKE_CASE`. Booleans: `is…`/`has…`/`can…`. Event handlers: `handleX` (own), `onX` (prop). |
| **British vs American spelling** | Content uses British English (`colour`, `behaviour`); code uses the standard-library spelling (`color`, `behavior`). Don't mix in one file. |
| **Comments / JSDoc** | Comment for **why**, not what. New file: 1–3 line header. Every exported function/component: a JSDoc block with brief description, `@param`, `@returns`. No commented-out code in commits. |
| **`console.*`** | No `console.log` in committed code. `console.warn`/`console.error` only with a one-line comment naming the condition. |
| **Lines / structure** | Lines under ~100 chars where reasonable. Early returns over deep ternaries. Pure functions where possible. |

## 6. Reference Patterns

Copy-paste templates. The plan considers these the canonical implementation — do not improvise alternatives.

### 6.1 Question page HTML pattern (used by `<QuestionPage>`)

DOM order matters: legend (H1) → hint → inline error → radios (per GOV.UK question-pages pattern). The optional `<details>` "Help with this question" block is **outside** the `<fieldset>` (it is supplementary content, not part of the field), positioned between the fieldset and the Continue button.

**Back link must use react-router `<Link>`, not a plain `<a>`.** A plain anchor would trigger a full-page reload, wiping `FormContext` state. Import: `import { Link } from "react-router-dom";`

```jsx
<Link to={backHref} className="govuk-back-link">Back</Link>

<ProgressIndicator current={step} total={totalSteps} />

{hasError && <ErrorSummary firstFieldId={`${fieldName}-1`} message={errorMessage} />}

<div className={`govuk-form-group${hasError ? ' govuk-form-group--error' : ''}`}>
  <fieldset className="govuk-fieldset" aria-describedby={describedBy}>
    <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
      <h1 className="govuk-fieldset__heading">{pageTitle}</h1>
    </legend>

    {hint && (
      <div id={`${fieldName}-hint`} className="govuk-hint">{hint}</div>
    )}

    {hasError && (
      <p id={`${fieldName}-error`} className="govuk-error-message">
        <span className="govuk-visually-hidden">Error:</span> {errorMessage}
      </p>
    )}

    <div className="govuk-radios">
      {options.map((opt, i) => (
        <div className="govuk-radios__item" key={opt.value}>
          <input
            className="govuk-radios__input"
            id={`${fieldName}-${i + 1}`}
            name={fieldName}
            type="radio"
            value={opt.value}
            checked={answers[fieldName] === opt.value}
            onChange={() => setAnswer(fieldName, opt.value)}
          />
          <label className="govuk-radios__label" htmlFor={`${fieldName}-${i + 1}`}>
            {opt.label}
          </label>
        </div>
      ))}
    </div>
  </fieldset>
</div>

{helpDetails && (
  <details className="govuk-details">
    <summary className="govuk-details__summary">
      <span className="govuk-details__summary-text">{helpDetails.summaryText}</span>
    </summary>
    <div className="govuk-details__text">{helpDetails.bodyText}</div>
  </details>
)}

<GovukButton onClick={handleContinue}>Continue</GovukButton>
```

`describedBy` is the space-separated list of present id refs (`${fieldName}-hint`, `${fieldName}-error`), or omitted entirely if neither is present.

### 6.2 ErrorSummary component

```jsx
// src/components/ErrorSummary.jsx
import { useEffect, useRef } from "react";

/**
 * GOV.UK error summary. Focuses itself on mount so the keyboard user
 * lands at the top of the page and screen readers announce the heading
 * + error link. Uses focus rather than role="alert" — focusing a live
 * region can cause double-announcement in NVDA/JAWS, and the canonical
 * govuk-frontend pattern focuses the container instead.
 */
export default function ErrorSummary({ firstFieldId, message }) {
  const ref = useRef(null);
  useEffect(() => { ref.current?.focus(); }, []);
  return (
    <div
      ref={ref}
      className="govuk-error-summary"
      tabIndex={-1}
      aria-labelledby="error-summary-title"
    >
      <h2 id="error-summary-title" className="govuk-error-summary__title">
        There is a problem
      </h2>
      <div className="govuk-error-summary__body">
        <ul className="govuk-error-summary__list">
          <li><a href={`#${firstFieldId}`}>{message}</a></li>
        </ul>
      </div>
    </div>
  );
}
```

### 6.3 Document title `useEffect`

```jsx
useEffect(() => {
  const base = `${pageTitle} - Green Home Grant - GOV.UK`;
  document.title = hasError ? `Error: ${base}` : base;
}, [pageTitle, hasError]);
```

### 6.4 Focus the `<main>` element on route change

Wire this in `App.jsx`. Three rules:

- `<main>` carries `id="main-content"` (skip-link target) and `tabIndex={-1}` (so it can receive programmatic focus without being a tab stop).
- On every route change, focus moves to `<main>`.
- This is the only auto-focus on route change — do **not** add a parallel focus call on the H1, the legend, or any input.

```jsx
// Inside App.jsx
import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

function App() {
  const mainRef = useRef(null);
  const { pathname } = useLocation();
  useEffect(() => { mainRef.current?.focus(); }, [pathname]);

  return (
    <>
      <SkipLink />
      <GovukHeader />
      <PhaseBanner phase="alpha" feedbackHref="#" />
      <div className="govuk-width-container">
        <main
          id="main-content"
          className="govuk-main-wrapper"
          role="main"
          ref={mainRef}
          tabIndex={-1}
        >
          <AppRoutes />
        </main>
      </div>
      <GovukFooter />
    </>
  );
}
```

Why this works for GOV.UK accessibility:
- Screen readers announce the new page title (set via §6.3) followed by the main-landmark, then read forward into the new content.
- Keyboard users see the focus ring move out of any stale focused element to a neutral, predictable position.
- No double-announcement risk from the legend-nested H1 in question pages (§6.1).
- The error summary still wins focus when validation fails because it mounts after the route-change focus has already settled and explicitly calls `ref.focus()`.

### 6.5 Check-answers summary list

```jsx
<dl className="govuk-summary-list">
  <div className="govuk-summary-list__row">
    <dt className="govuk-summary-list__key">Property type</dt>
    <dd className="govuk-summary-list__value">
      {labelFor("propertyType", answers.propertyType)}
    </dd>
    <dd className="govuk-summary-list__actions">
      <Link className="govuk-link" to="/property-type?from=check-answers">
        Change<span className="govuk-visually-hidden"> property type</span>
      </Link>
    </dd>
  </div>
  {/* repeat for ownership, incomeBand, insulation, heating per content plan §4 */}
</dl>
```

### 6.6 Result-page panel (no icons — see §8)

```jsx
<div className={`govuk-panel ${outcome === "ineligible" ? "govuk-panel--not-eligible" : "govuk-panel--confirmation"}`}>
  <h1 className="govuk-panel__title">{panelTitle}</h1>
  {panelBody && <div className="govuk-panel__body">{panelBody}</div>}
</div>
```

**Class note.** `govuk-panel--confirmation` is the canonical Design System modifier; it's used for eligible AND partial outcomes (both are "confirmation of receipt"-style screens with positive framing). `govuk-panel--not-eligible` is a **teaching-scaffold extension** introduced by the starter `App.css` to render the not-eligible variant in dark grey — it is not in the official Design System. It is kept because the scaffold already defines it; future work that ports to `govuk-frontend` would replace it.

Panel titles and bodies per content plan §7 — branch on `(outcome, reason)`:

| `(outcome, reason)` | Panel title | Panel body |
|---|---|---|
| `("eligible", "owner-low-income")` | "You may be eligible for a Green Home Grant" | "You may qualify for a grant of up to £10,000" |
| `("partial", "renter")` | "You may be partially eligible for a Green Home Grant" | *(empty — detail below)* |
| `("partial", "owner-mid-income")` | "You may be partially eligible for a Green Home Grant" | *(empty — detail below)* |
| `("ineligible", *)` | "You are not eligible for a Green Home Grant" | *(empty — detail below)* |

### 6.7 `<details>` help block

```jsx
<details className="govuk-details">
  <summary className="govuk-details__summary">
    <span className="govuk-details__summary-text">Help with annual household income</span>
  </summary>
  <div className="govuk-details__text">
    Include earnings from employment, self-employment, pensions, rental
    income, and benefits. Do not include one-off payments like
    inheritance or lottery winnings.
  </div>
</details>
```

### 6.8 Skip link

```jsx
// src/components/SkipLink.jsx
export default function SkipLink() {
  return (
    <a href="#main-content" className="govuk-skip-link">
      Skip to main content
    </a>
  );
}
```

Mounted as the first element inside `<App>`. `App.jsx`'s `<main>` element gets `id="main-content"`.

CSS rule (added to `App.css`):

```css
.govuk-skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  padding: var(--govuk-spacing-2) var(--govuk-spacing-3);
  background: var(--govuk-yellow);
  color: var(--govuk-black);
  text-decoration: underline;
  font-weight: 700;
}
.govuk-skip-link:focus {
  left: 0;
  outline: 3px solid var(--govuk-focus-colour);
}
```

### 6.9 Progress indicator

This is a **custom component**, not a GOV.UK Design System pattern. The class is prefixed `app-` to make that explicit — do not name it `govuk-step-indicator`. The plain-text "Step X of 5" pattern is permitted by GOV.UK research for linear fixed-length journeys (research2 — "fixed and >3").

The indicator sits **between the back link and the H1** on every question page (not above the back link, not below the H1).

```jsx
// src/components/ProgressIndicator.jsx
export default function ProgressIndicator({ current, total }) {
  return (
    <p className="app-step-indicator" aria-label={`Step ${current} of ${total}`}>
      Step {current} of {total}
    </p>
  );
}
```

CSS rule (added to `App.css`):

```css
.app-step-indicator {
  font-size: 16px;
  color: var(--govuk-dark-grey);
  margin-top: 0;
  margin-bottom: var(--govuk-spacing-2);
}
```

## 7. Files to Create / Modify

(Flat list — no ownership assigned. Lane assignment happens in a separate step after this plan is accepted.)

**Modify (existing scaffold stubs):**

- `wk03/starter/src/App.jsx` — wrap content in `<FormProvider>`; mount `<SkipLink />`, `<GovukHeader />`, `<PhaseBanner phase="alpha" feedbackHref="#" />`, `<AppRoutes />`, `<GovukFooter />`; add `id="main-content"`, `tabIndex={-1}`, and a `ref` to `<main>`; add the `useLocation` + `useEffect` focus-on-route-change pattern per §6.4.
- `wk03/starter/src/App.css` — extend with classes listed in §8.3 (phase banner, footer, hint, summary-list-actions visually-hidden, fieldset legend large, skip-link, step indicator, details, page-enter animation).
- `wk03/starter/src/components/GovukHeader.jsx` — render "GOV.UK" wordmark + "Green Home Grant" service-name link to `/`.
- `wk03/starter/src/components/GovukButton.jsx` — accept `variant`, `onClick`, `type`, `children`; `variant="start"` adds `.govuk-button--start` and a chevron SVG.
- `wk03/starter/src/components/PhaseBanner.jsx` — render alpha tag + feedback link, copy per content plan §1.
- `wk03/starter/src/components/GovukFooter.jsx` — render accessibility-statement link and cookies link per content plan §10.
- `wk03/starter/src/pages/StartPage.jsx` — implement per content plan §2.
- `wk03/starter/src/pages/PropertyTypePage.jsx` — thin `<QuestionPage>` wrapper, content plan §3 Q1.
- `wk03/starter/src/pages/OwnershipPage.jsx` — content plan §3 Q2.
- `wk03/starter/src/pages/IncomePage.jsx` — content plan §3 Q3 (+ `helpDetails`).
- `wk03/starter/src/pages/InsulationPage.jsx` — content plan §3 Q4 (+ `helpDetails`).
- `wk03/starter/src/pages/HeatingPage.jsx` — content plan §3 Q5 (+ `helpDetails`).
- `wk03/starter/src/pages/CheckAnswersPage.jsx` — implement per content plan §4. Guards: redirect to first unanswered question if any answer is empty.
- `wk03/starter/src/pages/ResultPage.jsx` — implement per content plan §7. Guards: redirect to `/` if any answer is empty. No back link.
- `wk03/starter/src/pages/AccessibilityStatementPage.jsx` — implement per content plan §9.
- `wk03/starter/package.json` — add the test dev-deps and scripts in §12.1.
- `wk03/starter/vite.config.js` — add Vitest `test` block per §12.1.

**Create:**

- `wk03/starter/src/contexts/FormContext.jsx` — `FormProvider`, `useFormContext`; initial state per §4.1.
- `wk03/starter/src/router.jsx` — `<AppRoutes />` route table per §4.5.
- `wk03/starter/src/components/SkipLink.jsx` — §6.8.
- `wk03/starter/src/components/ProgressIndicator.jsx` — §6.9.
- `wk03/starter/src/components/QuestionPage.jsx` — §4.4 + §6.1.
- `wk03/starter/src/components/ErrorSummary.jsx` — §6.2.
- `wk03/starter/src/components/Panel.jsx` — wraps §6.6.
- `wk03/starter/src/components/SummaryList.jsx` — wraps §6.5 with a `rows` prop (`{ key, value, changeHref, changeHiddenText }[]`).
- `wk03/starter/src/displayLabels.js` — `labelFor(field, value)` and `measuresFor(answers)` per content plan §4 + §6.
- `wk03/starter/src/eligibility.js` — pure `eligibility(answers)` per §4.3.
- `wk03/starter/src/__tests__/eligibility.test.js` — §12.2.
- `wk03/starter/src/__tests__/QuestionPage.test.jsx` — §12.3.
- `wk03/starter/src/__tests__/setup.js` — §12.1.

**Do not touch:** `wk03/starter/index.html`, `wk03/starter/src/main.jsx` (BrowserRouter is already there — that is the correct wrapper), `wk03/starter/AI_LOG.md` content beyond appending entries.

## 8. GOV.UK Styling Discipline

GOV.UK fidelity is the load-bearing requirement of this brief. If a polish idea conflicts with the Design System, the polish goes. Every page and every component must look and behave like the equivalent in `https://design-system.service.gov.uk/` even though we are hand-writing the markup.

**Permitted deviations are enumerated in §9 (polish enhancements) and nowhere else.** The three permitted deviations are: the `app-step-indicator` custom component, the motion-safe 150 ms page-enter animation, and `<details>` "Help with this question" blocks. The teaching-scaffold `govuk-panel--not-eligible` modifier (already in `App.css`) is permitted as a pre-existing scaffold extension — see §6.6. Any other deviation from the Design System needs sign-off in `AI_LOG.md` before it ships.

### 8.1 What is ENFORCED

| Layer | Rule |
|---|---|
| **Typography** | Use only `govuk-heading-xl`, `govuk-heading-l`, `govuk-heading-m`, `govuk-body`, `govuk-body-l`, `govuk-list`, `govuk-list--bullet`. No new heading sizes. No new font families. Body font is the existing stack in `App.css` (`"GDS Transport", arial, sans-serif`). |
| **Colour palette** | Use only the CSS variables already defined in `App.css` (`--govuk-blue`, `--govuk-black`, `--govuk-white`, `--govuk-green`, `--govuk-red`, `--govuk-yellow`, `--govuk-light-grey`, `--govuk-mid-grey`, `--govuk-dark-grey`). Do not introduce new colour values. |
| **Spacing** | Use only `var(--govuk-spacing-1..6, 8, 9)` already defined in `App.css`. No magic-number margins or padding. |
| **Focus ring** | Yellow (`var(--govuk-yellow)`) 3 px solid outline on every focusable element. The existing `:focus` rules in `App.css` are correct — extend the same pattern to new components. |
| **Page structure** | `<header>` (GOV.UK) → `<div class="govuk-phase-banner">` → `<div class="govuk-width-container">` → `<main id="main-content" class="govuk-main-wrapper" role="main">` → page → `<footer>` (GOV.UK). The skip link is the first focusable element. |
| **Question pages** | Back link → progress indicator → (error summary if error) → `<fieldset>` with `<legend class="govuk-fieldset__legend--l">` wrapping `<h1 class="govuk-fieldset__heading">` → hint (if any) → details (if any) → inline error (if error) → radios → Continue button. Pattern is §6.1 verbatim. |
| **Radios** | Native `<input type="radio">` inside `.govuk-radios__item`, each with an explicit `<label htmlFor=…>`. No custom radio components. Tap target ≥ 40 px (already set in `App.css`). |
| **Error pattern** | Error summary at top with heading "There is a problem" (`role="alert"`, `tabIndex=-1`, auto-focused). Inline error above input, prefixed `<span class="govuk-visually-hidden">Error:</span>`. `<title>` gains "Error: " prefix. Error-summary link href is `#<firstFieldId>` and clicking it focuses the first errored field. Exact pattern per content plan §8 and research §5.3. |
| **Check answers** | `<dl class="govuk-summary-list">` markup per §6.5. Every "Change" link has visually-hidden text naming the field ("Change *property type*"). Submit button reads "Submit and see result" (content plan §4). |
| **Result panel** | `<div class="govuk-panel govuk-panel--confirmation">` for eligible/partial; `<div class="govuk-panel govuk-panel--not-eligible">` for ineligible. **No interactive elements (buttons/links) inside the panel** — research §5.3 notes the contrast ratio fails for them. Body paragraphs and "What to do next" sit outside the panel. |
| **Phase banner** | Exact wording from content plan §1: "This is a new service – your *feedback* will help us to improve it." Tag text "alpha". **Dash character is the en dash (`–`, U+2013)** as written in content plan §1; do not normalise to em dash or hyphen-minus. |
| **Footer** | Accessibility statement link to `/accessibility-statement`. Cookies link to `#`. Both per content plan §10. |
| **Accessibility statement** | All eight sections from research §7, populated with the values in content plan §9. |
| **Plain English** | All visible copy is from the content plan. Do not paraphrase. Sentence case for headings. Currency as "£10,000" (no `.00`). Use "and" not "&". |

### 8.2 What is FORBIDDEN

| Pattern | Why it's out |
|---|---|
| Inline SVG icons inside the result panel | Not part of the Design System panel pattern; risks WCAG 1.4.3 contrast failure on the icon stroke (white-on-green or white-on-grey is borderline). Drop them. |
| Decorative SVGs without `focusable="false"` and `aria-hidden="true"` | The start-button chevron is the one allowed decorative SVG (it ships with the Design System start-button pattern). It MUST carry both `aria-hidden="true"` and `focusable="false"` to be invisible to assistive tech and to keyboard focus. |
| Radio-hover left-border accent | Not part of the Design System radios pattern; introduces a state the Design System does not specify, which can confuse keyboard users tracking focus. Drop it. |
| Hover-only tooltips, `title="…"` attribute tooltips | Fail on touch, hide from screen readers, break keyboard nav. Research §5.3 + SK plan §3a.8 forbid them. Use `<details>` (§6.7) instead. |
| Custom fonts (web-fonts beyond the existing GDS Transport / Arial fallback) | Adds load + risks rendering differences. |
| Custom palette colours, custom heading sizes, custom spacing values | The CSS-variable set is the design system — extend it only with values that match the official GOV.UK token set. |
| Sticky headers, sticky footers, sticky banners | Risk WCAG 2.4.11 (Focus Not Obscured — Minimum) failures. |
| React-router `<Link>` for the skip link | The skip link is a same-page anchor (`#main-content`), not a route change — use a plain `<a>`. |
| Decorative animations beyond the §9 page-enter | Anything else is out of scope. |

### 8.3 New `App.css` classes to add

The starter `App.css` already covers most of what is needed (typography, buttons, radios, error summary, summary list, panel). The following classes are referenced by this plan and must be added:

| Class | Purpose |
|---|---|
| `.govuk-back-link` | Back link styling (small font, left chevron via `::before`). |
| `.govuk-fieldset` | Reset border/padding. |
| `.govuk-fieldset__legend--l` | 36 px heading-size legend wrapper. |
| `.govuk-fieldset__heading` | `margin: 0; font: inherit;` so the H1 inside the legend inherits the legend's size. |
| `.govuk-hint` | `color: var(--govuk-dark-grey); margin-bottom: var(--govuk-spacing-3);`. |
| `.govuk-visually-hidden` | Standard visually-hidden utility (`clip: rect(0 0 0 0)` recipe). |
| `.govuk-phase-banner`, `.govuk-phase-banner__content`, `.govuk-phase-banner__content__tag`, `.govuk-tag` | Phase banner styling, black-on-blue tag. |
| `.govuk-footer`, `.govuk-footer__meta`, `.govuk-footer__inline-list`, `.govuk-footer__link` | Footer styling. |
| `.govuk-skip-link` | §6.8. |
| `.app-step-indicator` | §6.9 (custom, not GOV.UK). |
| `.govuk-details`, `.govuk-details__summary`, `.govuk-details__summary-text`, `.govuk-details__text` | Tier-2 contextual help (SK plan §3a.8). |
| `.govuk-link` | Plain link styling, matches default `a`. |
| `.govuk-button--start` | (Existing in `App.css`.) Verify it still works with the chevron SVG. |
| `.govuk-summary-list__actions a` | Right-aligned change link styling (existing `.govuk-summary-list__actions` covers layout). |
| `.govuk-error-summary__body` | No-op layout wrapper referenced by §6.2 markup; add an empty rule or minimal layout spacing so the selector exists. |
| Page-enter animation | §9. |

## 9. Polish Enhancements (Within GOV.UK Standards)

These three additions stay inside the Design System and are part of the plan, not stretch:

1. **"Step X of 5" progress indicator** above each question H1. Component §6.9. Permitted because the journey is linear and fixed at 5 steps (research2 explicitly allows progress only when steps are "fixed and >3").
2. **Motion-safe 150 ms page-enter transition.** Add to `App.css`:

   ```css
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

   This fires on every route change because React replaces the page subtree, re-mounting `<main>`. No library required.
3. **`<details>` "Help with this question" blocks** on Income, Insulation, Heating. Pattern §6.7. Wording is at the implementer's discretion but must follow content plan voice (plain English, second person, no jargon). Suggested topics: what counts as household income; how to read your EPC; what "Other" means on the heating page.

## 10. Stretch / Optional

**Not built by default.** If pursued, this is the recommended approach.

**`sessionStorage` persistence of `answers`** — so a browser refresh during the journey doesn't wipe progress. Sketch:

```jsx
// src/contexts/FormContext.jsx (modified)
import { createContext, useContext, useEffect, useState } from "react";

const STORAGE_KEY = "ghg.answers.v1";
const INITIAL_ANSWERS = { propertyType: "", ownership: "", incomeBand: "", insulation: "", heating: "" };

const FormContext = createContext(null);

export function FormProvider({ children }) {
  const [answers, setAnswers] = useState(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      return raw ? { ...INITIAL_ANSWERS, ...JSON.parse(raw) } : INITIAL_ANSWERS;
    } catch { return INITIAL_ANSWERS; }
  });
  useEffect(() => {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(answers)); } catch { /* quota / private mode */ }
  }, [answers]);
  const setAnswer = (field, value) => setAnswers((prev) => ({ ...prev, [field]: value }));
  const resetAnswers = () => { sessionStorage.removeItem(STORAGE_KEY); setAnswers(INITIAL_ANSWERS); };
  return <FormContext.Provider value={{ answers, setAnswer, resetAnswers }}>{children}</FormContext.Provider>;
}

export function useFormContext() {
  const ctx = useContext(FormContext);
  if (!ctx) throw new Error("useFormContext must be used inside <FormProvider>");
  return ctx;
}
```

If implemented, add one note to the accessibility statement (the service uses `sessionStorage`, no cookies) and update the cookies-link target to point to a brief notice.

Other stretches the README lists (`localStorage` save-and-return, second eligibility pathway, Playwright E2E, accessible PDF, semantic-intent stretch) are out of scope unless explicitly added later.

## 11. WCAG 2.2 AA Compliance Checklist

Grouped by POUR. Cite SC numbers when filing test reports. Source: `docs/research/research.md` §4.

**Perceivable**
- [ ] **1.1.1 Non-text content** — the start-button chevron SVG carries `aria-hidden="true"` and `focusable="false"`. No informational images in scope.
- [ ] **1.3.1 Info and Relationships** — `<fieldset>`/`<legend>` for radio groups; `<label htmlFor>` for every radio; `<dl>/<dt>/<dd>` on check-answers.
- [ ] **1.3.5 Identify input purpose (AA)** — N/A (no autocomplete-eligible inputs: this service collects no name, address, email, or payment details).
- [ ] **1.4.3 Contrast** — verify with axe; existing palette in `App.css` is GOV.UK-compliant (black/white, blue/white, green/white, red/white). Don't introduce new combinations.
- [ ] **1.4.4 Resize text** — layouts survive 200 % text scale (browser zoom).
- [ ] **1.4.5 Images of Text (AA)** — N/A (no images of text used; all headings are real text).
- [ ] **1.4.10 Reflow** — 320 × 568 viewport, no horizontal scroll on any route.
- [ ] **1.4.11 Non-text contrast** — focus ring (`var(--govuk-yellow)` on `var(--govuk-black)`), form borders, panel chrome.
- [ ] **1.4.12 Text spacing** — layouts survive user-applied line-height / letter-spacing.

**Operable**
- [ ] **2.1.1 Keyboard** — every control reachable / operable with keyboard only (Tab, Shift+Tab, Enter, Space).
- [ ] **2.4.1 Bypass blocks** — skip link is the first focusable element on every page.
- [ ] **2.4.2 Page titled** — `document.title` set on every page in the exact format `"<pageTitle> - Green Home Grant - GOV.UK"` (with `Error: ` prefix when an error is visible). §6.3.
- [ ] **2.4.3 Focus order** — Tab order matches visual: SkipLink → Header → PhaseBanner → BackLink → Form → Continue → Footer.
- [ ] **2.4.4 Link Purpose (In Context)** — every "Change" link in the summary list includes visually-hidden text naming the field ("Change *property type*"). The "Find an approved installer" link's purpose is clear from surrounding body copy.
- [ ] **2.4.7 Focus visible** — yellow focus ring on every focusable element.
- [ ] **2.4.11 Focus Not Obscured (Minimum) (new in 2.2)** — no sticky headers/footers/banners that could hide the focused element.
- [ ] **2.5.3 Label in Name** — the visible button text ("Continue", "Start now", "Submit and see result") is the accessible name; no `aria-label` overrides on buttons.
- [ ] **2.5.7 Dragging Movements (AA, new in 2.2)** — N/A (no drag interactions).
- [ ] **2.5.8 Target Size (Minimum) (new in 2.2)** — every tap target ≥ 24 × 24 CSS px. Radios are 40 × 40; Change links and Back link must be ≥ 24 px tall (achieve by line-height / padding, not by shrinking text).

**Understandable**
- [ ] **3.2.6 Consistent Help (new in 2.2)** — phase-banner feedback link appears in the same place on every page.
- [ ] **3.3.1 Error identification** — inline error names which field, what's wrong. Error summary lists each errored field.
- [ ] **3.3.2 Labels or instructions** — every input has a `<label>` (or `<legend>` for radio groups).
- [ ] **3.3.3 Error suggestion** — error messages tell the user what to do ("Select your ownership status").
- [ ] **3.3.7 Redundant Entry (new in 2.2)** — Change-link flow preserves prior answer (read from context, `?from=check-answers` returns the user to check-answers without re-asking later questions).
- [ ] **3.3.8 Accessible Authentication (Minimum) (AA, new in 2.2)** — N/A (no authentication in this service).

**Robust**
- [ ] **4.1.2 Name, role, value** — native HTML elements; no custom ARIA roles for radios / buttons.
- [ ] **4.1.3 Status messages** — the error summary's focus-on-mount + `<h2>` title surface the validation problem; no `aria-live` regions needed (research2 advises minimising them).

## 12. Test Strategy

### 12.1 Test infrastructure setup

**Modify `wk03/starter/package.json`:**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:run": "vitest run"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "@vitejs/plugin-react": "^4.2.0",
    "jsdom": "^25.0.0",
    "vite": "^5.0.0",
    "vitest": "^2.1.0"
  }
}
```

**Modify `wk03/starter/vite.config.js`** — add the triple-slash reference and the `test` block. The existing `defineConfig` from `vite` continues to work; Vitest reads this file as its config too.

```js
/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import os from 'node:os';

const PORT = Number(process.env.VITE_PORT) || 5002;
const HOSTNAME = process.env.VITE_PUBLIC_HOSTNAME || os.hostname();

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: PORT,
    strictPort: true,
    hmr: { protocol: 'wss', host: HOSTNAME, clientPort: 443 },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.js'],
    css: false,
  },
});
```

**Create `wk03/starter/src/__tests__/setup.js`:**

```js
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => { cleanup(); });
```

Then `npm install` once; `npm run test:run` should exit 0 ("no test files found" is OK before any test exists).

### 12.2 Eligibility test matrix (≥ 8 tests, one per rule branch + measures)

File: `wk03/starter/src/__tests__/eligibility.test.js`.

| # | Scenario | Expected `outcome` | Expected `reason` |
|---|---|---|---|
| 1 | `incomeBand: "high"` overrides all other answers | `ineligible` | `income-too-high` |
| 2 | Full insulation + heat pump | `ineligible` | `no-measures-needed` |
| 3 | `ownership: "private-renter"` | `partial` | `renter` |
| 4 | `ownership: "housing-association"` | `partial` | `renter` |
| 5 | `ownership: "council"` | `partial` | `renter` |
| 6 | `ownership: "owner"` + `incomeBand: "mid"` | `partial` | `owner-mid-income` |
| 7 | `ownership: "owner"` + `incomeBand: "low"` | `eligible` | `owner-low-income` |
| 8 | No rule matched (empty/unknown) | `ineligible` | `default` |

Plus measures checks (count toward the ≥ 8 minimum):

| # | Scenario | Expected `measures` includes / excludes |
|---|---|---|
| 9 | `propertyType: "flat"`, partial insulation | excludes "Loft insulation"; includes "Internal wall insulation" |
| 10 | `insulation: "full"` | excludes both insulation measures |
| 11 | `heating: "heat-pump"` | excludes "Air source heat pump installation" |

Plus robustness checks:

| # | Scenario | Expected |
|---|---|---|
| 12 | `eligibility({})` | does not throw; returns `{ outcome: "ineligible", reason: "default", measures: [...] }` |
| 13 | `eligibility({ propertyType: "boat" })` | does not throw; returns `ineligible` / `default` |

### 12.3 QuestionPage component test matrix (≥ 4 tests)

File: `wk03/starter/src/__tests__/QuestionPage.test.jsx`. Wrap renders in `<MemoryRouter>` + `<FormProvider>`.

```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { FormProvider } from '../contexts/FormContext';
import QuestionPage from '../components/QuestionPage';

function renderWithProviders(ui, { initialEntries = ['/property-type'] } = {}) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <FormProvider>{ui}</FormProvider>
    </MemoryRouter>
  );
}
```

| # | Test |
|---|---|
| 1 | Renders all radio options provided in `options` prop |
| 2 | Clicking Continue with no selection shows the error summary AND the inline error |
| 3 | After error appears, the error summary is the focused element (`document.activeElement`) |
| 4 | When `answers[fieldName]` is non-empty, the matching radio is pre-checked |
| 5 (bonus) | When URL is `/property-type?from=check-answers`, Continue navigates to `/check-answers` rather than the next question |

### 12.4 Manual test plan (run before declaring done)

- [ ] Tab through a fresh page: SkipLink is first; activating it jumps focus to `<main>`.
- [ ] Three happy paths: owner+low → eligible; private-renter+any non-high → partial; high income → ineligible.
- [ ] Two edge paths: owner+full insulation+heat pump → ineligible (no-measures-needed); owner+mid → partial (owner-mid-income).
- [ ] Change-link round trip: click Change on a row, change the answer, Continue returns to check-answers — does not loop through subsequent questions.
- [ ] Reflow at 320 × 568 viewport on every route — no horizontal scroll.
- [ ] At 200 % browser zoom, no content lost.
- [ ] `prefers-reduced-motion: reduce` disables the page-enter animation (verify in DevTools rendering tab).
- [ ] Lighthouse / axe-devtools pass on Start, every question page, CheckAnswers, all three Result variants, and AccessibilityStatement.

## 13. Definition of Done

Mapped to the README acceptance criteria (`wk03/README.md`).

- [ ] **Start page** with title, description, "Start now" button. (README criterion 1)
- [ ] **Start now navigates to the first question.** (README criterion 2)
- [ ] **5 question pages**, one-thing-per-page. (README criterion 3)
- [ ] **Each question has a Continue button** navigating to the next. (README criterion 4)
- [ ] **Back link** on every question page. (README criterion 5)
- [ ] **Check-your-answers page** with a summary list of all responses. (README criterion 6)
- [ ] **Each summary row has a Change link** that returns to that question; the change flow returns the user to check-answers. (README criterion 7)
- [ ] **Result page** showing eligible / not eligible / partial. (README criterion 8)
- [ ] **All form inputs have `<label>`** (or `<legend>` for radios). (README criterion 9)
- [ ] **Keyboard reachable / operable.** (README criterion 10)
- [ ] **Contrast ≥ 4.5:1** for all text. (README criterion 11)
- [ ] **320 px reflow** without horizontal scrolling. (README criterion 12)
- [ ] **Client-side validation** shows errors on empty required fields. (README criterion 13)
- [ ] **Error pattern** follows GOV.UK: summary at top + inline. (README criterion 14)
- [ ] **≥ 5 eligibility unit tests pass** (we ship ≥ 8 + measures + edges = 13). (README criterion 15)
- [ ] **`AI_LOG.md` has ≥ 3 entries**, each with the four required fields. (README criterion 16)

Plus this plan's additions (each is objectively verifiable):

- [ ] **Phase banner matches §8.1 and content plan §1** — exact wording, alpha tag, present on every route.
- [ ] **Footer** has an "Accessibility statement" link to `/accessibility-statement` and a "Cookies" link, per content plan §10.
- [ ] **Accessibility-statement page** renders all eight PSBAR sections enumerated in `docs/research/research.md` §7, populated with the values in content plan §9. (Mere presence of the page is not enough.)
- [ ] Skip link is the first focusable element on every page; activating it moves focus to `<main id="main-content">`.
- [ ] **Focus discipline:** `<main id="main-content" tabIndex={-1}>` receives focus on every route change (§6.4). Error summary auto-focuses on validation. No auto-focus on H1, legend, or input.
- [ ] **`document.title`** updates on every route in the exact format `"<pageTitle> - Green Home Grant - GOV.UK"`, with `Error: ` prefix when an error is visible. Verified by inspecting the browser tab on each route.
- [ ] CheckAnswers redirects to the first unanswered question if any answer is empty; Result redirects to `/` if any answer is empty.
- [ ] `npm run test:run` exits 0; all eligibility + QuestionPage tests pass.
- [ ] `npm run build` exits 0; no console errors or warnings on any route in dev.
- [ ] **`<details>` help blocks** present on `/income`, `/insulation`, `/heating`. Copy follows content-plan voice (plain English, second person, no jargon) — no lorem ipsum.
- [ ] **Step indicator** present on every question page, sits between the back link and the H1, with `aria-label="Step X of 5"` and visible text "Step X of 5".
- [ ] Page-enter animation runs only when `prefers-reduced-motion` is not "reduce".
- [ ] **No `localhost` URLs** referenced in any committed file — per repo CLAUDE.md the dev server must be reached via `http://<hostname>:<PORT>`.

## 14. Explicit Non-Goals

So future agents do not re-propose these:

- **State libraries** — Redux, Zustand, Recoil, jotai, MobX. Single `FormContext` is enough.
- **Form libraries** — react-hook-form. Five radio fields don't justify it.
- **Schema libraries** — Zod, Yup. Validation is "is this field non-empty?" — one `if` statement per page.
- **Data-fetching libraries** — TanStack Query. No remote data.
- **Router upgrades** — TanStack Router, React Router 7+, React Router 6.4+ data routers / loaders. The brief specifies plain client-side routing; the starter is already on `react-router-dom@6.20`.
- **TypeScript** — project is plain JavaScript; do not introduce TS or discriminated-union typing now.
- **`govuk-frontend` npm package, `govuk-react`** — the teaching scaffold is intentional; introducing the npm package defeats the brief.
- **SVG icons inside the result panel** — see §8.2.
- **Radio-hover left-border accent** — see §8.2.
- **Hover-only / `title`-attribute tooltips** — see §8.2.
- **Per-agent change-log files (`docs/agents/Agent-<id>-changes.md`)** — out of scope for this plan; if needed, raise separately.
- **Lane assignments to agents** — out of scope; a separate step splits this plan across the four agents.
- **`localStorage` save-and-return** — README lists it as stretch only; `sessionStorage` is the recommended persistence layer if any is added (§10).
- **Analytics (GA / GA4)** — none. Avoiding PECR cookie-banner obligation (research §2.4).
- **A second eligibility pathway, Playwright E2E, PDF export, semantic-intent stretch** — out of scope (README stretch only).

## 15. Open Questions

Surface to the user before declaring done if they become blockers.

1. **Phase-banner feedback link target.** Content plan §1 uses `#` as placeholder. Decide: real survey URL, mailto, GitHub issue, or accept `#` for the prototype? (Research §10 Q11.)
2. **"Start again" link on Result page.** Not required by the brief or content plan. Add as a single link below "What to do next"? If yes, it would call `resetAnswers()` and `navigate('/')`. Default: do not add unless the user asks.
3. **Welsh-language requirement.** A fictional UK scheme — exempt from the Welsh Language (Wales) Measure 2011 if the body is UK-wide; not exempt if devolved. Default: English only. (Research §10 Q10.)
4. **Cookie posture.** Default: set no non-essential cookies; the cookies link points to a stub statement that says so. If `sessionStorage` is added (§10), update the statement to mention it (sessionStorage is not a cookie under PECR, but transparency is good practice).
5. **Where to host the running dev server.** Per the lab CLAUDE.md, use `http://<hostname>:<PORT>` not `http://localhost:5002` — `vite.config.js` already binds to `0.0.0.0`. Confirm the lab `VITE_PUBLIC_HOSTNAME` is set if HMR misbehaves.

---

## 16. Stretch — Semantic Intent Matcher

> **Status:** This section opts the project back into the "semantic-intent stretch" item that §14 lists as out of scope. Execute only after the core eligibility service is complete and merged. Each task below is a single commit, scoped to be picked up by an LLM agent without further context.

### 16.1 Goal

Add a free-text "What do you need help with?" entry point at `/help` where the user types a natural-language description ("I need help with my boiler") and the page surfaces the top-3 most relevant entries from a small service catalogue, ranked by cosine similarity over on-device sentence embeddings.

**Constraints (from README line 188):**

- Runs entirely in the browser. No remote inference API.
- No API key, no server, no per-query cost.
- Embeddings are computed on first visit and cached locally for subsequent ones.
- Foreshadows Week 5 RAG — keep the architecture readable, not magic.

### 16.2 References

| Source | What it provides |
|--------|------------------|
| README.md §"Stretch challenge: Semantic intent matching" (line 188+) | Original brief and recommended stack (`@xenova/transformers`, MiniLM, top-3 cosine). |
| [Transformers.js docs](https://huggingface.co/docs/transformers.js) | Runtime — pipeline API, `feature-extraction` task, ONNX models. |
| [Sentence-Transformers MiniLM-L6-v2 model card](https://huggingface.co/Xenova/all-MiniLM-L6-v2) | The exact model. 384-dim output, ~23 MB compressed, L2-normalised embeddings work well with cosine. |
| This plan §§3–8 | Existing architecture, GOV.UK styling, file conventions — reuse them. |

### 16.3 Architecture Decisions (additive — do not change without flagging)

| ID | Decision | Reason |
|----|----------|--------|
| SI1 | Runtime: `@xenova/transformers` 2.x with model `Xenova/all-MiniLM-L6-v2`. | Browser-native (WASM + ONNX). README's recommended default. |
| SI2 | Service catalogue is a plain ES module (`src/intent/catalogue.js`) with 8–12 entries. No JSON file, no remote source. | One file, easy to review and diff. |
| SI3 | Catalogue embeddings are computed once on first `/help` visit, then cached in `localStorage` keyed by both `CATALOGUE_VERSION` and the model name. | Avoids re-encoding ~12 entries every page load. Survives refresh. Invalidation by bumping `CATALOGUE_VERSION`. |
| SI4 | Ranking: cosine similarity over L2-normalised vectors, top-3 returned. No vector DB, no FAISS — the catalogue is small enough for a linear scan. | README explicitly says no vector DB. |
| SI5 | New route `/help`. Existing routes untouched. Eligibility flow tests unaffected. | Additive; minimises blast radius. |
| SI6 | Model and Transformers.js library are loaded **lazily** when the user lands on `/help`, not at app boot. Dynamic `await import('@xenova/transformers')`. | The library + model are heavy; do not penalise users who never use this feature. |
| SI7 | If the dynamic import or the model load fails (e.g., WebAssembly disabled, network blocked), fall back to a keyword-overlap scorer over the same catalogue. The page never errors — it degrades. | Resilience. Browsers without WASM still get something useful. |
| SI8 | Below a tunable similarity floor (default `0.30`), no result is shown; the page renders the full catalogue as a fallback list. | Avoids surfacing low-confidence false matches. |

### 16.4 Shared Contracts

**`src/intent/catalogue.js`**

```js
export const CATALOGUE_VERSION = 1;

/**
 * @typedef {Object} ServiceEntry
 * @property {string} id           - stable identifier, slug-style
 * @property {string} title        - display name
 * @property {string} description  - 15-25 plain-English words
 * @property {string} route        - in-app path (e.g. "/") or "#" for placeholders
 * @property {string[]} phrases    - 4-8 example natural-language phrases (informal OK)
 */

/** @type {ServiceEntry[]} */
export const SERVICE_CATALOGUE = [ /* ... entries ... */ ];
```

**`src/intent/matcher.js`**

```js
/**
 * Initialise the matcher. Loads the embedding model, computes (or restores
 * from cache) the catalogue embeddings. Safe to call multiple times — only
 * the first call does work.
 *
 * @returns {Promise<{ mode: 'embeddings' | 'keyword-fallback' }>}
 */
export async function initMatcher();

/** Returns true once initMatcher() has resolved. */
export function isMatcherReady();

/**
 * @typedef {Object} RankedIntent
 * @property {ServiceEntry} entry
 * @property {number} score   - cosine similarity in [-1, 1]; L2-normalised vectors usually fall in [0, 1]
 */

/**
 * Rank the catalogue against a natural-language query.
 * @param {string} query
 * @param {number} [k=3]
 * @returns {Promise<RankedIntent[]>}
 */
export async function rankIntents(query, k);
```

**localStorage cache shape (key `ghg:intent-cache:v1`)**

```json
{
  "catalogueVersion": 1,
  "modelName": "Xenova/all-MiniLM-L6-v2",
  "embeddings": [{ "id": "green-home-grant", "vector": [/* 384 floats */] }]
}
```

### 16.5 Tasks (each = one commit)

#### SI-T1 — Add `@xenova/transformers` dependency  *(~10 min)*

- Files: `wk03/starter/package.json`, `package-lock.json`.
- `npm install @xenova/transformers` — pin to `^2.x`.
- Verify `npm run build` exits 0. Note the new bundle size in the commit body.
- If Vite errors with "Failed to fetch dynamically imported module", add to `vite.config.js`: `optimizeDeps: { exclude: ['@xenova/transformers'] }`.
- Commit: `[Agent-X] chore(wk03): add @xenova/transformers dependency`.

#### SI-T2 — Service catalogue  *(~20 min)*

- Files: **create** `wk03/starter/src/intent/catalogue.js`.
- Write 8–12 service entries. At least these IDs (use real GOV.UK service names where applicable):
  - `green-home-grant` (route `/` — this app)
  - `apply-universal-credit`
  - `renew-passport`
  - `register-to-vote`
  - `free-school-meals`
  - `council-tax-reduction`
  - `replace-driving-licence`
  - `report-benefit-fraud`
- Each entry must have 4–8 `phrases` covering formal + informal language. Examples for the heating intent: `"my boiler is broken"`, `"I can't afford my heating bill"`, `"help with home insulation"`, `"replace my gas boiler with a heat pump"`.
- Export `CATALOGUE_VERSION = 1`.
- Acceptance: file lints clean and imports without runtime error.
- Commit: `[Agent-X] feat(wk03): add service catalogue for intent matching`.

#### SI-T3 — Cosine-similarity helper + tests  *(~15 min)*

- Files: **create** `wk03/starter/src/intent/cosine.js`, `wk03/starter/src/__tests__/cosine.test.js`.
- `cosineSimilarity(a: number[], b: number[]): number`. Guard zero-magnitude (return 0, not NaN). Throw on length mismatch.
- Optional helper: `normalize(v: number[]): number[]` returning the L2-normalised vector.
- Tests (Vitest): identical → 1; orthogonal → 0; opposite → -1; zero vector → 0; mismatched lengths → throws.
- Acceptance: 5 new tests pass.

#### SI-T4 — Matcher skeleton with keyword-overlap fallback  *(~30 min)*

- Files: **create** `wk03/starter/src/intent/matcher.js`, `wk03/starter/src/__tests__/matcher.test.js`.
- This task implements only the **fallback** path so the UI can be built and tested independently of Transformers.js.
- Algorithm: tokenise query and each entry's `title + description + phrases.join(' ')` (lowercase, split on `\W+`, drop short tokens). Score = `|Q ∩ E| / max(|Q|, 1)` (a simplified Jaccard / overlap-ratio).
- Public API matches §16.4. `initMatcher()` resolves with `{ mode: 'keyword-fallback' }`. `rankIntents()` returns top-k.
- Tests:
  - Query "my boiler is broken" → top match is `green-home-grant`.
  - Query "I want a new passport" → top match is `renew-passport`.
  - Empty query → returns empty array (do not surface garbage).
  - `rankIntents` returns entries sorted by descending score with stable tiebreak on `id`.
- Acceptance: 4 new tests pass.
- Commit: `[Agent-X] feat(wk03): add intent matcher with keyword-overlap fallback`.

#### SI-T5 — `/help` page UI (uses the fallback matcher from T4)  *(~45 min)*

- Files: **create** `wk03/starter/src/pages/HelpEntryPage.jsx`, **create** `wk03/starter/src/components/SimilarityBadge.jsx`. Modify `wk03/starter/src/router.jsx` (add `/help` route). Modify `wk03/starter/src/pages/StartPage.jsx` (add a secondary CTA link "Not sure? Describe your situation in your own words").
- HelpEntryPage structure (follow §6 reference patterns):
  - Back link to `/`.
  - `<h1>` "What do you need help with?".
  - `<form>` with `<label class="govuk-label">` + `<textarea class="govuk-textarea">` (rows=3) + hint text + submit button "Show services".
  - Results region with `aria-live="polite"` so screen readers announce updates.
  - Empty state: short instructional text.
  - With results: `<ol class="govuk-list">` of cards. Each card: `<h2>` title (acts as a `<Link>` to `route`), description, `<SimilarityBadge score={r.score} />`.
  - Below-threshold or no-query state: heading "Browse all services" + full catalogue list.
- `SimilarityBadge`: pill-shaped tag with text "84% match" (Math.round(score*100)). Colour by band — green ≥ 0.55, yellow 0.40–0.55, grey < 0.40.
- Set `document.title = "What do you need help with? - Green Home Grant - GOV.UK"`.
- File header comment + JSDoc per §5.
- Acceptance: in the browser, typing "boiler" then submit shows Green Home Grant as the top card with a non-zero score; tab order is correct.
- Commit: `[Agent-X] feat(wk03): add /help free-text intent entry page (fallback matcher)`.

#### SI-T6 — Wire Transformers.js + MiniLM embeddings  *(~75 min)*

- Files: rewrite `wk03/starter/src/intent/matcher.js`; **optionally** extract caching to `wk03/starter/src/intent/embeddingCache.js`.
- `initMatcher()`:
  1. Try `const { pipeline } = await import('@xenova/transformers')`. On failure, fall through to the keyword-overlap implementation from T4 and return `{ mode: 'keyword-fallback' }`.
  2. Read cache from `localStorage['ghg:intent-cache:v1']`. If present and `catalogueVersion === CATALOGUE_VERSION` and `modelName === 'Xenova/all-MiniLM-L6-v2'`, restore.
  3. Otherwise: `const extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2')`. For each `entry`, embed `${entry.title}. ${entry.description}. ${entry.phrases.join('. ')}`, L2-normalise, store in memory. Write the cache back to `localStorage`.
  4. Resolve with `{ mode: 'embeddings' }`.
- `rankIntents(query, k = 3)`:
  - If keyword-fallback mode, defer to the T4 implementation.
  - Otherwise: embed the query (same pipeline, same normalisation), compute cosine vs each cached vector, sort desc, return top-k mapped to `{ entry, score }`.
- Wrap every `localStorage` access in try/catch (private-browsing safety).
- Tests (Vitest): use `vi.mock('@xenova/transformers', ...)` to stub `pipeline` with a deterministic fake extractor that returns canned vectors. Cover:
  - Cold start: cache is empty, `pipeline` is called once per catalogue entry; cache is written.
  - Warm start: cache populated and valid → `pipeline` not called for catalogue entries (only for the live query).
  - Stale cache: bumping the in-test `CATALOGUE_VERSION` invalidates.
  - Import failure: forced rejection → returns `{ mode: 'keyword-fallback' }` and `rankIntents` still works.
  - `rankIntents` returns top-3 sorted desc.
- Acceptance: 5 new tests pass; in the browser, the matcher uses embeddings (devtools network tab shows the model download once, then nothing on refresh).
- Commit: `[Agent-X] feat(wk03): swap intent matcher to MiniLM embeddings with localStorage cache`.

#### SI-T7 — Loading + error UX on `/help`  *(~30 min)*

- Files: modify `wk03/starter/src/pages/HelpEntryPage.jsx`.
- While `initMatcher()` is in flight:
  - Disable the submit button (`aria-disabled="true"`).
  - Render a `govuk-notification-banner` (reuse the one already added in the Save-and-return PR) with copy: "Preparing the assistant — this only happens once, around 25 MB."
  - Provide a "Skip and browse all services" link that renders the full catalogue without waiting.
- If `initMatcher()` resolves with `{ mode: 'keyword-fallback' }`: render a `govuk-warning-text` (one new class in App.css) saying "Using a basic keyword search — your browser couldn't load the assistant."
- Use a single status string in an `aria-live="polite"` region: "Searching…", "3 services matched", "No strong matches — browse all services below".
- Acceptance: with DevTools "Slow 3G", the page is interactive immediately and shows the loading banner.

#### SI-T8 — Threshold tuning + threshold-aware UI  *(~20 min)*

- Files: modify `wk03/starter/src/pages/HelpEntryPage.jsx`, `wk03/starter/src/components/SimilarityBadge.jsx`.
- Constants at top of HelpEntryPage:
  - `HIGH_CONFIDENCE = 0.55`
  - `MEDIUM_CONFIDENCE = 0.40`
  - `MIN_CONFIDENCE = 0.30` (results below this are dropped)
- If after ranking the top result is `< MIN_CONFIDENCE`, hide the results list and render the "Browse all services" fallback list instead, with a `govuk-body` paragraph: "We couldn't find a strong match for that description. Browse all services below."
- Add a manual smoke checklist (in code as a JSDoc comment at the top of HelpEntryPage, or in a small `wk03/docs/research/intent-smoke-queries.md`) listing example queries: "boiler broken", "my house is cold", "I can't pay my rent", "lost my passport", "register to vote".
- Acceptance: gibberish ("asdf asdf asdf") returns no results and shows fallback; clear queries return matching services.

#### SI-T9 — Component tests for HelpEntryPage  *(~30 min)*

- Files: **create** `wk03/starter/src/__tests__/HelpEntryPage.test.jsx`.
- Use `vi.mock('../intent/matcher', ...)` to inject a controllable mock that exposes `initMatcher`, `isMatcherReady`, `rankIntents`.
- Tests:
  1. On mount, `initMatcher` is called exactly once.
  2. While not-ready, submit button is disabled and the loading banner is in the DOM.
  3. After ready, typing + submit calls `rankIntents` with the user query and renders 3 result cards with `SimilarityBadge`.
  4. Empty input does not call `rankIntents`.
  5. Failure path: `initMatcher` rejects → fallback list renders with the full catalogue.
  6. Below-threshold mock result → fallback list renders, top results hidden.
- Acceptance: 6 new tests pass.

#### SI-T10 — Manual smoke + AI_LOG entry  *(~15 min)*

- Files: append entry to `wk03/starter/AI_LOG.md` per the format in `wk03/CLAUDE.md`.
- Manual smoke (in browser): try the 5 example queries from SI-T8. Note for each (in the AI_LOG entry) the top match and whether it is sensible.
- AI_LOG entry must address the README's reflection prompt: "where did the AI help (model selection, similarity-threshold tuning) vs not (vector-DB choice — none needed; in-memory)".
- Commit: `[Agent-X] docs(wk03): AI_LOG entry for semantic intent matcher`.

### 16.6 Files to Create / Modify (summary)

| File | Status | Introduced in task |
|------|--------|--------------------|
| `wk03/starter/package.json` | modify | SI-T1 |
| `wk03/starter/src/intent/catalogue.js` | create | SI-T2 |
| `wk03/starter/src/intent/cosine.js` | create | SI-T3 |
| `wk03/starter/src/__tests__/cosine.test.js` | create | SI-T3 |
| `wk03/starter/src/intent/matcher.js` | create → rewrite | SI-T4 → SI-T6 |
| `wk03/starter/src/intent/embeddingCache.js` | create (optional) | SI-T6 |
| `wk03/starter/src/__tests__/matcher.test.js` | create | SI-T4 (extended SI-T6) |
| `wk03/starter/src/pages/HelpEntryPage.jsx` | create → extend | SI-T5 (extended SI-T7, SI-T8) |
| `wk03/starter/src/components/SimilarityBadge.jsx` | create | SI-T5 |
| `wk03/starter/src/router.jsx` | modify | SI-T5 |
| `wk03/starter/src/pages/StartPage.jsx` | modify | SI-T5 |
| `wk03/starter/src/App.css` | modify (small) | SI-T5 (textarea + badge), SI-T7 (warning text) |
| `wk03/starter/src/__tests__/HelpEntryPage.test.jsx` | create | SI-T9 |
| `wk03/starter/AI_LOG.md` | append | SI-T10 |
| `wk03/starter/vite.config.js` | modify (conditional) | SI-T1 only if dynamic-import error occurs |

### 16.7 Sequencing

```
SI-T1 ── SI-T2 ── SI-T3 ── SI-T4 ── SI-T5 ── SI-T6 ── SI-T7 ── SI-T8 ── SI-T9 ── SI-T10
   ^             ^             ^             ^
   pkg          catalogue     fallback     UI works against fallback (real model swapped in T6)
```

Each task is independently committable. T5 can ship before T6 — the page works with the keyword-overlap matcher and graduates to embeddings without UI changes.

### 16.8 GOV.UK & accessibility constraints

- Re-use GOV.UK classes: `govuk-label`, `govuk-textarea`, `govuk-hint`, `govuk-button`, `govuk-list`, `govuk-notification-banner`. Add the missing `.govuk-textarea` rule to App.css (existing CSS doesn't include it because the core app uses radios only).
- Results region: `aria-live="polite"` for async updates (WCAG 4.1.3).
- Disabled submit button must still be keyboard-focusable (don't visually remove from DOM); use `aria-disabled` plus a guard in the click handler.
- Reflow at 320 px: textarea full width, badge wraps below title on narrow viewports (WCAG 1.4.10).
- Resize-text test at 200 % zoom: no clipped text (WCAG 1.4.4).
- Match GOV.UK error pattern (§6.2) if/when validation is added — currently, only "empty input" is treated as "no query", not as an error.

### 16.9 Performance & footprint

- Library + WASM runtime + model ≈ 25–30 MB on first visit; ~12 entries × 384 floats × 4 bytes ≈ 18 KB cached after.
- Bundle impact at build time: only the Transformers.js library, not the model. Confirm `npm run build` reports the increase honestly in the commit body.
- Eager-load nothing for `/help` in `App.jsx`. The dynamic `import()` in `initMatcher()` is what triggers the network.
- Service-worker prefetch and IndexedDB-backed model cache are **out of scope** for this stretch — Transformers.js does its own model caching in browsers that support it; do not work around it.

### 16.10 Definition of Done

- [ ] Navigating to `/help` renders the page even before the model is ready.
- [ ] Submitting a query returns top-3 results with similarity badges.
- [ ] Top result for "boiler broken" is `green-home-grant`.
- [ ] Below-threshold queries fall back to the full catalogue list.
- [ ] `localStorage['ghg:intent-cache:v1']` is populated after the first run (verified in DevTools).
- [ ] Bumping `CATALOGUE_VERSION` invalidates the cache (test or manual).
- [ ] If Transformers.js fails to load, the page still ranks queries via the keyword-overlap fallback and shows a warning.
- [ ] `npm run test:run` — all pre-existing tests still pass; ~20 new tests pass (5 cosine + 4 matcher-T4 + 5 matcher-T6 + 6 HelpEntryPage).
- [ ] `npm run build` exits 0.
- [ ] AI_LOG entry in place per SI-T10.
- [ ] Smoke queries from SI-T8 produce sensible top matches.

### 16.11 Risks and gotchas

1. **Vite + dynamic imports of native-ish libraries.** If `npm run dev` chokes with `Failed to fetch dynamically imported module`, add `optimizeDeps: { exclude: ['@xenova/transformers'] }` to `vite.config.js` (do this in SI-T1 only if you actually hit the error — don't preemptively complicate the config).
2. **WebAssembly off / iOS Safari < 17.** Covered by SI-T7's keyword-fallback. Verify the fallback path in a Safari emulator if available.
3. **First-load size disclosure.** The "~25 MB, one-time" banner is essential — without it, users on metered connections will assume the app is broken. Do not skip SI-T7.
4. **Catalogue quality dominates results.** The default thresholds in SI-T8 are starting points. Re-tune after writing the catalogue in SI-T2 if smoke queries return weak top matches. Cheaper than swapping models.
5. **localStorage quota.** ~12 entries × 384 floats encoded as JSON is small (< 50 KB) and well within quota. If the catalogue grows past a few hundred entries, switch to IndexedDB — but not before.
6. **Privacy posture.** Free-text input could contain personal information. Do not log the query to console or analytics, and do not persist it. The cache holds embeddings of the **catalogue**, never the user's query.

---

*End of plan. Decisions in §3 and §4 are settled — do not change them without flagging to the user. If a task description is ambiguous, prefer fidelity to the content plan over creative interpretation.*

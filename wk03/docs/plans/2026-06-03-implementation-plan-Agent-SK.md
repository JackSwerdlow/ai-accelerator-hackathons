# Green Home Grant — Implementation Plan (4-agent parallel)

> **For agentic workers:** This plan implements the content defined in
> [`2026-06-03-content-plan.md`](./2026-06-03-content-plan.md). The work is
> partitioned into four lanes (A/B/C/D), one per agent, with **no shared file
> ownership** except a single coordination file (`AI_LOG.md`, append-only).
> Read the **Shared Contracts** (§3) and the **File Ownership Map** (§4) before
> writing any code. If you discover a need to change a contract, raise it in
> `AI_LOG.md` under your agent identifier and wait for consensus.

## 0. Purpose

Build a React + Vite multi-step eligibility checker for the (fictional) Green
Home Grant scheme, following GOV.UK design patterns and meeting WCAG 2.2 AA.

All content (page copy, options, eligibility rules, error messages, result
text, accessibility statement) is fixed by the content plan — do **not**
invent wording. Reference the content plan section number on every task that
ships copy.

## 1. Inputs and References

| Reference | Where | Used by |
|-----------|-------|---------|
| Content plan | `wk03/docs/plans/2026-06-03-content-plan.md` | All lanes |
| Starter scaffold | `wk03/starter/` | All lanes |
| Existing GOV.UK CSS variables and classes | `wk03/starter/src/App.css` | Lane A (extends), others (consume only) |
| Repo collaboration rules | `wk03/CLAUDE.md`, repo-root `CLAUDE.md` | All lanes |
| AI log | `wk03/starter/AI_LOG.md` | All lanes (append-only, one entry per AI session) |

External (read once, do not re-fetch):

- GOV.UK Design System patterns: question pages, error summary, error message, check answers, panel
- WCAG 2.2 AA criteria: 1.3.1, 1.4.11, 2.4.3, 2.4.6, 2.4.7, 2.5.8 (new in 2.2), 3.3.1, 3.3.2, 3.3.3, 3.3.7 (new in 2.2), 4.1.2, 4.1.3
- Vitest + React Testing Library on Vite

## 2. Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| React Context for form state | Avoids prop drilling through 5+ pages and the check-answers page. Single source of truth. |
| `FormProvider` in `App.jsx`, `useFormContext()` hook from `src/contexts/FormContext.jsx` | Provider lives at the top so the context is available on every route. Custom hook hides implementation. |
| Pure `eligibility(answers)` function in `src/eligibility.js` | Pure function = unit-testable without DOM. |
| Vitest + `@testing-library/react` (NOT Playwright) | Vitest runs in the same toolchain as Vite, no separate browser binary. Sufficient for unit + light component tests. |
| One question pattern via `QuestionPage` component | Five question pages share identical structure (legend = H1, radios, hint, error, Continue). Building one component beats five copies. |
| Page `<title>` updated via `useEffect` in each page | No `react-helmet` dep needed for one element. Document title is part of WCAG 2.4.2. |
| Each page reads/writes a single field via context | Pages know nothing about each other. Adding/removing a question only touches its own page + the route table. |
| Use semantic HTML, native `<input type="radio">`, native `<button>` | WCAG 4.1.2 — let the browser do the work; avoid custom ARIA. |

## 3. Shared Contracts (DO NOT CHANGE without consensus in `AI_LOG.md`)

These are the API surfaces the four lanes must agree on. Once Lane A pushes
the FormContext stub (Lane A — Task A2), the contract is real and other lanes
can import it.

### 3.1 Form state shape

```js
// Authoritative shape — Lane B/C/D must use exactly these field names.
{
  propertyType: "",       // "" | "detached" | "semi-detached" | "terraced" | "flat" | "bungalow"
  ownership:    "",       // "" | "owner" | "private-renter" | "housing-association" | "council"
  incomeBand:   "",       // "" | "low" | "mid" | "high"
  insulation:   "",       // "" | "none" | "partial" | "full"
  heating:      "",       // "" | "gas-boiler" | "oil-boiler" | "electric-storage" | "heat-pump" | "other"
}
```

Empty string `""` means "not yet answered". Pages must treat empty string as
falsy (no preselection) and a non-empty value as the user's previous answer.

### 3.2 `useFormContext()` hook

```js
// Export from: src/contexts/FormContext.jsx
const { answers, setAnswer, resetAnswers } = useFormContext();

// answers: the object in §3.1
// setAnswer(field, value): updates one field. field must be a key of answers.
// resetAnswers(): clears all fields back to "" (used by a "Start again" link if added).
```

### 3.3 `eligibility(answers)` function

```js
// Export from: src/eligibility.js
import { eligibility } from "./eligibility";

const result = eligibility(answers);
// result = {
//   outcome:  "eligible" | "partial" | "ineligible",
//   reason:   string,                  // see table below
//   measures: string[],                // display labels (e.g. "Loft insulation")
// }
```

Reason codes (Result page consumes these to choose the right copy variant —
see content plan §7):

| `outcome` | `reason` | Meaning |
|-----------|----------|---------|
| `eligible` | `"owner-low-income"` | Rule 5 matched. |
| `partial` | `"renter"` | Rule 3 matched. |
| `partial` | `"owner-mid-income"` | Rule 4 matched. |
| `ineligible` | `"income-too-high"` | Rule 1 matched. |
| `ineligible` | `"no-measures-needed"` | Rule 2 matched. |
| `ineligible` | `"default"` | No rule matched (fallback). |

Rules evaluated in priority order per content plan §5. **Do not change rule
order or priority.**

### 3.4 `<QuestionPage>` component

```jsx
// Export from: src/components/QuestionPage.jsx
<QuestionPage
  pageTitle="What type of property do you live in?"   // used for document.title and as H1/legend
  fieldName="propertyType"                            // key in formState (§3.1)
  hint="Optional hint text"                           // omit if none
  errorMessage="Select the type of property you live in"
  options={[
    { value: "detached",      label: "Detached house" },
    { value: "semi-detached", label: "Semi-detached house" },
    // ...
  ]}
  backHref="/"
  onContinueNavigateTo="/ownership"
/>
```

Behaviour the component must implement (every question page gets these for
free by using it):

1. Reads `answers[fieldName]` from context to pre-select on render.
2. Updates `answers[fieldName]` via `setAnswer` when user picks an option.
3. Renders `<a class="govuk-back-link" href={backHref}>Back</a>` above main.
4. Renders the GOV.UK fieldset/legend-as-H1 pattern (see §6.1).
5. On Continue: if no option selected, sets local error state and renders the
   error pattern (see §6.2); otherwise calls `navigate(onContinueNavigateTo)`.
6. Sets `document.title` via `useEffect` to:
   - `"<pageTitle> - Green Home Grant - GOV.UK"` (normal)
   - `"Error: <pageTitle> - Green Home Grant - GOV.UK"` (when error visible)
7. When error is set, moves keyboard focus to the error summary
   (`tabindex="-1"` + `.focus()` after paint).
8. Supports the "Change" flow from check-answers: if the user navigated here
   from `/check-answers`, the Continue button should send them back to
   `/check-answers` instead of the next question. **Mechanism**: read the
   `from` query parameter (e.g. `/property-type?from=check-answers`); if
   present, override `onContinueNavigateTo` with `/check-answers`.

### 3.5 `<ErrorSummary>` and `<Panel>` components (optional but recommended)

Lane C extracts small helper components for the error summary and the result
panel. Their signatures are not contracts — only `QuestionPage` uses
`ErrorSummary`, and only `ResultPage` uses `Panel`, so the owning lane
controls them.

### 3.6 Routes

Routes are defined in `App.jsx` (Lane A). All lanes navigate using these
exact paths:

| Path | Page | Owner |
|------|------|-------|
| `/` | StartPage | A |
| `/property-type` | PropertyTypePage | B |
| `/ownership` | OwnershipPage | B |
| `/income` | IncomePage | B |
| `/insulation` | InsulationPage | C |
| `/heating` | HeatingPage | C |
| `/check-answers` | CheckAnswersPage | C |
| `/result` | ResultPage | C |
| `/accessibility-statement` | AccessibilityStatementPage | A |

## 3a. Coding Standards & Conventions (apply to all lanes)

These are not contracts (no API to clash on) but **rules every lane follows**.
Reviewers may reject a commit that breaks them.

### 3a.1 State management

| Rule | Reason |
|------|--------|
| Form answers live **only** in `FormContext` (§3.1). | Single source of truth across pages. |
| Local component `useState` is allowed for **transient UI state** only (e.g. local error flags, expanded/collapsed hint). | Keeps "is the radio selected" and "is the error showing" in the right scope. |
| Do **not** add Redux, Zustand, Recoil, MobX, jotai, or any other state library. | Scope is small; context is enough. Anyone proposing a library raises it in `AI_LOG.md` first. |
| Do **not** add new React contexts without consensus in `AI_LOG.md`. | Multiple contexts make data-flow harder to follow. |
| **Derive, don't store**: anything computable from `answers` (eligibility, measures, display labels) is computed at render time. | Avoids stale-data bugs. |

### 3a.2 React hook rules

| Rule | Reason |
|------|--------|
| Follow [Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks): top-level only, never inside conditionals/loops/early-returns. | Required by React. |
| Use only these hooks: `useState`, `useEffect`, `useRef`, `useContext`. `useMemo`/`useCallback` only with a measured reason. | Smaller surface = fewer subtle bugs. |
| Router hooks allowed: `useNavigate`, `useLocation`, `useSearchParams`, `useParams`. | Standard react-router-dom v6 APIs. |
| Custom hooks live in `src/hooks/`, file name `useXxx.js`, exported function `useXxx`. | Predictable file/import layout. |
| Effect dependency arrays must be **complete** — no `// eslint-disable react-hooks/exhaustive-deps` unless commented with the precise reason. | Catches stale-closure bugs. |
| No `useReducer` in v1. | Overkill for the state shape we have. |

### 3a.3 Dedicated routes file

Routes live in **`src/router.jsx`**, not inline in `App.jsx`. This makes the
route table grep-able and lets reviewers see all paths in one place.

```jsx
// src/router.jsx — Lane A owns this file.
import { Routes, Route } from "react-router-dom";
import StartPage from "./pages/StartPage";
import PropertyTypePage from "./pages/PropertyTypePage";
// ... etc.

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<StartPage />} />
      <Route path="/property-type" element={<PropertyTypePage />} />
      <Route path="/ownership" element={<OwnershipPage />} />
      <Route path="/income" element={<IncomePage />} />
      <Route path="/insulation" element={<InsulationPage />} />
      <Route path="/heating" element={<HeatingPage />} />
      <Route path="/check-answers" element={<CheckAnswersPage />} />
      <Route path="/result" element={<ResultPage />} />
      <Route path="/accessibility-statement" element={<AccessibilityStatementPage />} />
    </Routes>
  );
}

export default AppRoutes;
```

`App.jsx` imports and mounts `<AppRoutes />` — that's the only routing
mention in `App.jsx`.

### 3a.4 Per-agent change log (`wk03/docs/agents/Agent-<id>-changes.md`)

Each agent maintains **their own** change-log file. Append-only. The path
embeds the agent identifier so there are zero merge conflicts.

**Why this is separate from `AI_LOG.md`:**

- `AI_LOG.md` is the **prompt log** (what the AI was asked, what was generated, what was changed and why) — required by the hackathon brief.
- `Agent-<id>-changes.md` is the **change log** (what files this agent edited and what they now do) — required by this plan so the next agent picking up the repo can read it in seconds.

Format (Markdown, dated entries, newest at top):

```markdown
# Agent-SK — Changes

## 2026-06-03 — feat: implement StartPage (Task A6)
Files: src/pages/StartPage.jsx
What changed: replaced placeholder with full content-plan §2 implementation. Added navigation handler using useNavigate. Set document.title via useEffect.
Why: complete acceptance criteria for Lane A Task A6.

## 2026-06-03 — feat: add FormContext (Task A2)
Files: src/contexts/FormContext.jsx (new)
What changed: created FormProvider with answers state matching plan §3.1, plus setAnswer and resetAnswers. useFormContext hook throws if used outside provider.
Why: unblocks Lane B/C/D — published the state contract.
```

One entry per task (or per commit). Keep entries terse: files + what + why.

### 3a.5 Responsive design

| Breakpoint | Reason | Requirement |
|------------|--------|-------------|
| **320px** | Smallest viewport per GOV.UK + the hackathon AC. | No horizontal scroll. All forms operable. |
| **640px** | Mobile/tablet boundary (matches existing CSS media query). | Typography scales down per existing `App.css` rules. |
| **769px+** | Default desktop layout. | Max content width 960px (already enforced by `govuk-width-container`). |

Each lane validates its own pages at **320px and 640px** as part of self-QA.
Lane A owns adding any new media queries to `App.css` (others request via
`AI_LOG.md`).

Specific responsive rules:
- Tap targets ≥ 24×24 CSS px (WCAG 2.5.8). Existing GOV.UK radios are 40px — do not shrink them.
- No fixed-pixel widths on form containers that exceed 320px - 30px (account for padding).
- Test at narrowest width: enable DevTools mobile emulation at 320×568 (iPhone SE).

### 3a.6 Naming conventions

| Thing | Convention | Examples |
|-------|------------|----------|
| **JSX component files** | `PascalCase.jsx` | `QuestionPage.jsx`, `GovukHeader.jsx` |
| **Non-component .js files** | `camelCase.js` | `eligibility.js`, `displayLabels.js` |
| **Components / exported types** | `PascalCase` | `QuestionPage`, `FormProvider` |
| **Variables / functions / hooks** | `camelCase` | `setAnswer`, `useFormContext`, `handleContinue` |
| **Constants (module-level, immutable)** | `UPPER_SNAKE_CASE` | `ROUTES`, `INITIAL_ANSWERS` |
| **Booleans** | `is…`/`has…`/`can…`/`should…` | `isOpen`, `hasError`, `canContinue` |
| **Event handlers** | `handleX` for own handlers, `onX` for props | `handleContinue`, `<Button onClick={handleClick}>` |
| **Refs** | `xRef` | `summaryRef`, `inputRef` |
| **CSS classes** | `govuk-` prefix, kebab-case | `govuk-button--start` |

Forbidden:
- Single-letter variables outside of small map/filter callbacks (`a`, `b`, `x`).
- Hungarian notation (`strName`, `boolFlag`).
- Abbreviations that aren't standard in the domain (`btn` is OK, `qpg` is not).
- Mixing American/British spelling in the same file — content uses British English (`colour`, `behaviour`), code uses standard library spelling (`color`, `behavior`).

### 3a.7 Comments and documentation

Comment for **why**, not what. The reader can see what the code does — your
job is to explain intent that isn't obvious.

| Element | Required documentation |
|---------|------------------------|
| **New file** | Top-of-file comment (1-3 lines) stating the file's purpose. |
| **Exported function/component** | JSDoc block: brief description + `@param` + `@returns`. |
| **Non-obvious logic** | One-line comment above the block stating the *intent*. |
| **Workarounds / hacks** | A comment naming the constraint and why this is the chosen workaround. |
| **TODO** | Format `// TODO(Agent-XX): <action> — <reason>`. Owner included so anyone can ping. |

Example:

```jsx
/**
 * QuestionPage — generic GOV.UK one-thing-per-page radio question.
 *
 * Reads answers[fieldName] from FormContext, lets the user pick one option,
 * validates on Continue, then navigates onward (or back to /check-answers if
 * arrived via a Change link).
 *
 * @param {{
 *   pageTitle: string,
 *   fieldName: keyof Answers,
 *   options: { value: string, label: string }[],
 *   hint?: string,
 *   errorMessage: string,
 *   backHref: string,
 *   onContinueNavigateTo: string,
 * }} props
 * @returns {JSX.Element}
 */
function QuestionPage(props) { ... }
```

Forbidden:
- Comments restating identifier names (`// set the user's name`).
- Block comments at every line.
- Commented-out code committed to main. Delete it; `git` remembers.

### 3a.8 Contextual help / tooltips

The user has asked for **tooltips on UI bits that need more explanation**.
GOV.UK explicitly avoids hover-only tooltips because they fail on touch
devices, hide from many screen readers, and break keyboard navigation. We
follow a three-tier rule so the *intent* (more help where needed) lands
without breaking accessibility.

**Tier 1 — Always-visible hint text** *(default, preferred)*

For anything attached to a form input, use the GOV.UK hint pattern. This is
already the QuestionPage `hint` prop (§3.4) and is implemented in §6.1.

```jsx
<div id={`${fieldName}-hint`} className="govuk-hint">
  Include the income of all adults living in your home, before tax.
</div>
```

Wired via `aria-describedby` on the fieldset. Screen-reader compatible.
Touch-compatible. Keyboard-compatible.

**Tier 2 — Expandable "Help with this question"** *(use when explanation is longer than a sentence or two)*

Use the native `<details>`/`<summary>` element. Keyboard-accessible, screen-
reader-accessible, and degrades gracefully without JavaScript.

```jsx
<details className="govuk-details" data-module="govuk-details">
  <summary className="govuk-details__summary">
    <span className="govuk-details__summary-text">
      Help with annual household income
    </span>
  </summary>
  <div className="govuk-details__text">
    Include earnings from employment, self-employment, pensions, rental
    income, and benefits. Do not include one-off payments like inheritance
    or lottery winnings. If anyone in your household is paid in a non-UK
    currency, convert at the current rate.
  </div>
</details>
```

When to use:
- Income page (`/income`) — clarify what counts as income.
- Insulation page (`/insulation`) — clarify "loft only", "walls only", "full".
- Heating page (`/heating`) — clarify "Other" (e.g. district heating, solid fuel).
- CheckAnswers / Result — clarify what "partial" or "no measures available" means.

**Lane B and Lane C must add at least one `<details>` block per question
page that has a non-trivial choice (Income, Insulation, Heating).** The
exact text is at each agent's discretion but must be reviewed against the
content plan's voice (plain English, no jargon, second person).

Required CSS for `<details>` (Lane A adds to `App.css`):

```css
.govuk-details { margin-bottom: var(--govuk-spacing-4); }
.govuk-details__summary { color: var(--govuk-link-colour); cursor: pointer; display: inline-block; padding-left: 25px; position: relative; }
.govuk-details__summary:focus { outline: 3px solid var(--govuk-focus-colour); }
.govuk-details__summary-text { text-decoration: underline; }
.govuk-details__text { padding: var(--govuk-spacing-2) 0 var(--govuk-spacing-2) var(--govuk-spacing-3); border-left: 5px solid var(--govuk-mid-grey); margin-top: var(--govuk-spacing-2); }
```

**Tier 3 — Accessible tooltip** *(only for supplementary, non-essential info on non-form UI)*

If you genuinely need a hover/focus popup (e.g. an inline `(?)` icon next to
a panel heading on the Result page), implement it with the following
constraints — otherwise use Tier 1 or 2.

- The trigger is a `<button>` (not a `<span>` or `<div>`), so it is focusable.
- The popup is visible on **both hover and focus** (not hover alone).
- The popup is dismissable with `Esc` and by clicking elsewhere.
- The popup content is associated via `aria-describedby` on the trigger button.
- The trigger is **not** the only way to learn the information — the same
  info is also available in fully-visible body text or via Tier 2 details.
- Do **not** use tooltips on form labels, form inputs, or error messages.

Forbidden patterns:
- Title-attribute "tooltips" (`<span title="...">`) — invisible on touch, inconsistent across screen readers.
- Hover-only popups — fail on touch + keyboard.
- Tooltips holding the only copy of important information — duplicate it elsewhere.

If in doubt: **use Tier 1 (hint) or Tier 2 (details).** Tier 3 is reserved
for genuine "icon-with-extra-context" use cases.

### 3a.9 Other code-quality rules

- No `console.log` in committed code. Use `console.warn`/`console.error` only for genuinely abnormal conditions (and add a one-line comment explaining when it would fire).
- Prefer pure functions: pages should compute, not mutate.
- Prefer early returns over deeply nested ternaries.
- Lines under ~100 characters where reasonable.

---

## 4. File Ownership Map (CRITICAL — prevents merge conflicts)

Each file is owned by **exactly one lane**. Other lanes must not edit it. If
you need a change in another lane's file, post a note in `AI_LOG.md` and
coordinate.

| File | Owner | Status |
|------|-------|--------|
| `src/App.jsx` | A | Modify (already has TODOs) |
| `src/App.css` | **A** | Modify (extend with missing classes) |
| `src/main.jsx` | A | No change expected |
| `src/contexts/FormContext.jsx` | **A** | **Create** |
| `src/router.jsx` | **A** | **Create** (routes table, see §3a.3) |
| `src/components/GovukHeader.jsx` | A | Modify (service name link) |
| `src/components/GovukFooter.jsx` | A | Modify if needed |
| `src/components/GovukButton.jsx` | A | Modify (add `aria-disabled`, link variant if needed) |
| `src/components/PhaseBanner.jsx` | A | Modify if needed |
| `src/components/SkipLink.jsx` | **A** | **Create** (WCAG 2.4.1) |
| `src/pages/StartPage.jsx` | A | Modify |
| `src/pages/AccessibilityStatementPage.jsx` | A | Modify |
| `src/components/QuestionPage.jsx` | **B** | **Create** |
| `src/components/ErrorSummary.jsx` | B | **Create** (consumed by QuestionPage) |
| `src/pages/PropertyTypePage.jsx` | B | Modify |
| `src/pages/OwnershipPage.jsx` | B | Modify |
| `src/pages/IncomePage.jsx` | B | Modify |
| `src/pages/InsulationPage.jsx` | C | Modify |
| `src/pages/HeatingPage.jsx` | C | Modify |
| `src/pages/CheckAnswersPage.jsx` | C | Modify |
| `src/pages/ResultPage.jsx` | C | Modify |
| `src/components/SummaryList.jsx` | C | **Create** (optional helper) |
| `src/components/Panel.jsx` | C | **Create** (optional helper) |
| `src/eligibility.js` | **D** | **Create** |
| `src/__tests__/eligibility.test.js` | D | **Create** |
| `src/__tests__/QuestionPage.test.jsx` | D | **Create** (light component test) |
| `src/__tests__/setup.js` | D | **Create** |
| `package.json` | **D** | Modify (add test deps + script) |
| `vite.config.js` | D | Modify (add `test` block) |
| `AI_LOG.md` | All (append-only) | Each agent appends own entries |
| `wk03/docs/agents/Agent-<id>-changes.md` | Each lane (own file) | Created and maintained by each agent — no overlap |

Bold rows = **new files**. Coordinating on new files is cheaper than
coordinating on shared edits.

### 4.1 Coordination rules

- **App.css** is owned by Lane A but read by everyone. If Lane B/C/D needs a
  new class, append a request to `AI_LOG.md` with the class name, the
  proposed CSS, and the reason. Lane A adds it.
- **AI_LOG.md** is append-only. Each entry is a new section at the bottom
  prefixed with your agent identifier. Do not edit other agents' entries.
- **package.json** version bumps and new deps go through Lane D only.
- Lane A must complete **Task A2 (FormContext stub)** and push to main
  before Lanes B/C/D start their context-consuming work. See §6.

## 5. Pre-flight (run once by Lane A before any task starts)

1. From repo root: `git pull --rebase origin main`.
2. `cd wk03/starter && npm install` — verify scaffold builds.
3. Run `npm run dev`, browse `http://localhost:5173/`, confirm a 200 with
   the placeholder StartPage rendering.
4. Stop dev server.
5. Open `wk03/starter/AI_LOG.md` and add a new entry under your agent
   identifier announcing the start of the implementation plan execution.
6. Commit and push the unchanged install (so `node_modules` exists locally
   for everyone, but is gitignored — confirm `node_modules/` is in
   `.gitignore`). If not, **stop**, post to `AI_LOG.md`, fix `.gitignore`
   before anyone else runs `npm install`.

After pre-flight succeeds, Lane A starts Task A1. Lanes B/C/D wait for
**Task A2 push to main** before starting their dependent tasks.

## 6. Reference patterns (copy-paste templates used by multiple lanes)

### 6.1 Question page HTML pattern (used by Lane B and Lane C question pages)

```jsx
<a href={backHref} className="govuk-back-link">Back</a>

{hasError && <ErrorSummary firstFieldId={`${fieldName}-1`} message={errorMessage} />}

<div className={`govuk-form-group${hasError ? ' govuk-form-group--error' : ''}`}>
  <fieldset className="govuk-fieldset" aria-describedby={describedBy}>
    <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
      <h1 className="govuk-fieldset__heading">{pageTitle}</h1>
    </legend>
    {hint && <div id={`${fieldName}-hint`} className="govuk-hint">{hint}</div>}
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

<GovukButton onClick={handleContinue}>Continue</GovukButton>
```

Where `describedBy` is computed as: hint id + error id (space-separated, only
the ones that are present). Example: `"propertyType-hint propertyType-error"`.

### 6.2 Error summary pattern (consumed by `<QuestionPage>`)

```jsx
<div className="govuk-error-summary" tabIndex="-1" ref={summaryRef} role="alert">
  <h2 className="govuk-error-summary__title">There is a problem</h2>
  <div className="govuk-error-summary__body">
    <ul className="govuk-error-summary__list">
      <li>
        <a href={`#${firstFieldId}`}>{message}</a>
      </li>
    </ul>
  </div>
</div>
```

The component must focus itself on mount (Lane B owns the implementation).

### 6.3 Document title pattern

```jsx
useEffect(() => {
  const base = `${pageTitle} - Green Home Grant - GOV.UK`;
  document.title = hasError ? `Error: ${base}` : base;
}, [pageTitle, hasError]);
```

### 6.4 Check-answers summary list (used by Lane C only)

```jsx
<dl className="govuk-summary-list">
  <div className="govuk-summary-list__row">
    <dt className="govuk-summary-list__key">Property type</dt>
    <dd className="govuk-summary-list__value">{labelFor("propertyType", answers.propertyType)}</dd>
    <dd className="govuk-summary-list__actions">
      <a className="govuk-link" href="/property-type?from=check-answers">
        Change<span className="govuk-visually-hidden"> property type</span>
      </a>
    </dd>
  </div>
  {/* repeat per content plan §4 */}
</dl>
```

`labelFor(field, value)` maps stored value → display label per content plan
§4 (label mapping table). Lane C may keep this in `src/displayLabels.js`
or inline it inside CheckAnswersPage — but **must not duplicate** the mapping
across files. Recommended: tiny `displayLabels.js` (owned by Lane C, also
imported by ResultPage for measures rendering).

### 6.5 Result page panel (Lane C)

```jsx
<div className={`govuk-panel ${outcome === "ineligible" ? "govuk-panel--not-eligible" : ""}`}>
  <h1 className="govuk-panel__title">{panelTitle}</h1>
  {panelBody && <div className="govuk-panel__body">{panelBody}</div>}
</div>
```

Panel titles + bodies per content plan §7.

---

## 7. Lane Assignments

Each lane has an ordered list of small tasks. A task is a single commit. Each
task lists: files touched, acceptance criteria, and (where relevant) the
content-plan section reference.

### Lane A — Foundation, state, chrome, start, accessibility

**Agent identifier convention:** `Agent-A-<your-name>` in commits and
`AI_LOG.md`.

**Pre-flight:** §5.

---

**Task A1 — Confirm starter builds and add gitignore for node_modules** (~5 min)

- Files: `.gitignore` (if missing the entry), no source changes.
- Acceptance:
  - [ ] `wk03/starter/.gitignore` contains `node_modules/` and `dist/`.
  - [ ] `npm run dev` starts on port 5173 without errors.
- Commit message: `[Agent-A] chore(wk03): confirm starter scaffold builds`.

---

**Task A2 — Create FormContext provider and hook** (~15 min, **BLOCKS B/C**)

- Files: **create** `wk03/starter/src/contexts/FormContext.jsx`.
- Implement:
  - `FormProvider`: holds `answers` via `useState` (initial shape from §3.1).
  - `setAnswer(field, value)`: validates that `field` is a key of `answers`;
    `setAnswers(prev => ({ ...prev, [field]: value }))`.
  - `resetAnswers()`: resets to initial.
  - Exports: `FormProvider`, `useFormContext`.
  - `useFormContext()` throws if used outside the provider (helps catch bugs).
- Acceptance:
  - [ ] File compiles, no console warnings in dev.
  - [ ] Snapshot of shape matches §3.1 exactly.
- Commit: `[Agent-A] feat(wk03): add FormContext with answers/setAnswer/resetAnswers`.
- **After commit: push to main. Notify lanes B/C/D in `AI_LOG.md` that the
  context contract is live.**

---

**Task A2.5 — Extract routes to `src/router.jsx`** (~10 min) (see §3a.3)

- Files: **create** `wk03/starter/src/router.jsx`; modify `wk03/starter/src/App.jsx`.
- Implement:
  - Move the `<Routes>` block from `App.jsx` into a new `AppRoutes` component in `router.jsx`.
  - `App.jsx` imports and renders `<AppRoutes />` only — no `<Route>` declarations remain in `App.jsx`.
  - File header comment in `router.jsx` per §3a.7.
- Acceptance:
  - [ ] `App.jsx` contains no `<Route>` JSX.
  - [ ] All 9 routes still resolve in the browser.
  - [ ] `grep -R "<Route " src/` returns only matches inside `router.jsx`.
- Commit: `[Agent-A] refactor(wk03): extract routes into router.jsx`.

---

**Task A3 — Mount FormProvider, PhaseBanner, GovukFooter in App.jsx** (~10 min)

- Files: `wk03/starter/src/App.jsx`.
- Implement (do not break existing routes):
  - Wrap `<AppRoutes />` (from Task A2.5) and chrome in `<FormProvider>`.
  - Mount `<SkipLink />` first (Task A4 dep — if not done, this is a TODO).
  - Mount `<GovukHeader />` (existing).
  - Mount `<PhaseBanner phase="alpha" feedbackHref="#" />` after the header
    per content plan §1.
  - Mount `<GovukFooter />` after `</main>`.
- Acceptance:
  - [ ] Every route renders with header + phase banner + footer.
  - [ ] No console errors.
- Commit: `[Agent-A] feat(wk03): mount FormProvider + phase banner + footer`.

---

**Task A4 — Skip link** (~10 min) (WCAG 2.4.1)

- Files: **create** `wk03/starter/src/components/SkipLink.jsx`. Mount in App.jsx.
- Implement: visible-on-focus link "Skip to main content" pointing to
  `#main-content`. Add `id="main-content"` to `<main>` in `App.jsx`. Add
  CSS rule in `App.css` for `.govuk-skip-link` (visually hidden, focusable).
- Acceptance:
  - [ ] Tab from a fresh page reveals the skip link as the first focused element.
  - [ ] Activating it jumps focus to `<main>`.
- Commit: `[Agent-A] feat(wk03): add skip-to-main-content link`.

---

**Task A5 — Extend App.css with missing GOV.UK classes** (~20 min)

- Files: `wk03/starter/src/App.css`.
- Add styles for any class currently used in components but not in the CSS:
  - `.govuk-phase-banner`, `.govuk-phase-banner__content`,
    `.govuk-phase-banner__content__tag`, `.govuk-tag`
  - `.govuk-footer`, `.govuk-footer__meta`, `.govuk-footer__meta-item`,
    `.govuk-footer__inline-list`, `.govuk-footer__inline-list-item`,
    `.govuk-footer__link`
  - `.govuk-hint` (`color: var(--govuk-dark-grey)`)
  - `.govuk-link` (matches default `a` for now)
  - `.govuk-skip-link` (visually hidden until focused; jumps to top-left when focused)
  - `.govuk-fieldset__legend--l` (uses 36px font, ties to govuk-heading-l)
  - `.govuk-fieldset__heading` (margin: 0, font: inherit)
  - `.govuk-grid-column-two-thirds` (max-width: 66.66%; layout helper)
  - `.govuk-details`, `.govuk-details__summary`, `.govuk-details__summary-text`, `.govuk-details__text` (see exact rules in §3a.8 Tier 2)
- Acceptance:
  - [ ] No unstyled elements in dev tools "audit".
  - [ ] Phase banner and footer render with GOV.UK look (black/grey palette).
  - [ ] `<details>` block expands/collapses on click and is keyboard-operable.
- Commit: `[Agent-A] style(wk03): add missing GOV.UK class styles`.

---

**Task A6 — StartPage** (~20 min) (content plan §2)

- Files: `wk03/starter/src/pages/StartPage.jsx`.
- Implement per content plan §2:
  - H1: "Check if you can get a Green Home Grant"
  - Description paragraphs (exact copy, in two-thirds column).
  - Bulleted list of what the user will need.
  - `<GovukButton variant="start" onClick={() => navigate('/property-type')}>Start now</GovukButton>`
  - Set `document.title` to `"Check if you can get a Green Home Grant - Green Home Grant - GOV.UK"`.
- Acceptance:
  - [ ] All copy matches content plan §2 verbatim.
  - [ ] Clicking "Start now" navigates to `/property-type`.
  - [ ] Page has exactly one H1.
- Commit: `[Agent-A] feat(wk03): implement StartPage per content plan §2`.

---

**Task A7 — AccessibilityStatementPage** (~20 min) (content plan §9)

- Files: `wk03/starter/src/pages/AccessibilityStatementPage.jsx`.
- Implement per content plan §9:
  - H1: "Accessibility statement"
  - Sub-sections: service name; compliance status; known issues; preparation
    date; last reviewed; contact email.
  - Use `<h2>` for each sub-section, `<p>` for body text.
  - Set `document.title` to `"Accessibility statement - Green Home Grant - GOV.UK"`.
- Acceptance:
  - [ ] All fields from content plan §9 rendered.
  - [ ] Reachable via footer "Accessibility statement" link.
- Commit: `[Agent-A] feat(wk03): implement accessibility statement page`.

---

**Task A8 — GovukHeader: service-name link** (~10 min)

- Files: `wk03/starter/src/components/GovukHeader.jsx`.
- Modify: add a second line/region under "GOV.UK" with the service name
  "Green Home Grant" as a link to `/`, styled per the existing
  `.govuk-header__link` rule (you may add `.govuk-header__service-name` if
  needed in App.css).
- Acceptance:
  - [ ] Header shows "GOV.UK" and "Green Home Grant" on every page.
  - [ ] Clicking "Green Home Grant" goes to `/`.
- Commit: `[Agent-A] feat(wk03): add service name to header`.

---

**Task A9 — Lane A self-QA (includes responsive + accessibility)** (~15 min)

- Files: none (testing only).
- Run through:
  - [ ] All routes mounted in App.jsx render.
  - [ ] FormContext available everywhere (`useFormContext()` in any page does not throw).
  - [ ] StartPage and AccessibilityStatementPage match content plan copy.
  - [ ] Tab order: SkipLink → Header → Main → Footer links.
  - [ ] No console errors on any page.
  - [ ] **Responsive at 320×568 (iPhone SE):** no horizontal scroll on Start, Accessibility Statement, and any route. (§3a.5)
  - [ ] **Responsive at 640px:** typography scales per `@media` rules.
- Log results in `AI_LOG.md`.
- No commit unless fixes needed.

---

**Task A10 — Lane A change log entry** (~5 min) (see §3a.4)

- Files: **create** `wk03/docs/agents/Agent-<your-id>-changes.md`.
- Implement: one Markdown entry per task you completed in Lane A. Format
  shown in §3a.4. Most recent first.
- Acceptance:
  - [ ] File exists at the expected path.
  - [ ] Has one entry per completed Lane A task (A1–A9).
- Commit: `[Agent-A] docs(wk03): Lane A change log`.

---

### Lane B — Reusable QuestionPage + Property/Ownership/Income

**Agent identifier convention:** `Agent-B-<your-name>`.

**Pre-flight:** wait for Lane A task **A2** push to main; then `git pull`.

---

**Task B1 — ErrorSummary component** (~20 min)

- Files: **create** `wk03/starter/src/components/ErrorSummary.jsx`.
- Implement per §6.2:
  - Props: `firstFieldId`, `message`.
  - On mount, focus the wrapping div (`tabIndex="-1"` + ref + `.focus()` in `useEffect`).
  - Render the `role="alert"` block with the link to `#<firstFieldId>`.
- Acceptance:
  - [ ] Renders the GOV.UK error summary structure exactly.
  - [ ] Element is focused on mount (verify in browser).
- Commit: `[Agent-B] feat(wk03): add ErrorSummary component`.

---

**Task B2 — QuestionPage component** (~60 min) (the centrepiece of Lane B)

- Files: **create** `wk03/starter/src/components/QuestionPage.jsx`.
- Implement the §6.1 pattern with all behaviour from §3.4 (1-8).
- Use `useFormContext()` for state.
- Use `useNavigate()` for routing.
- Use `useSearchParams()` to detect `?from=check-answers` and override the
  destination accordingly.
- Use `useEffect` to maintain `document.title` (§6.3).
- Set focus to error summary when error becomes visible.
- **Support an optional `helpDetails` prop** with shape `{ summaryText: string, bodyText: string }`. When provided, render a `<details>` block below the hint (Tier 2 of §3a.8). Lane B Task B5 (Income) is required to supply this; B3/B4 optional.
- File header comment + JSDoc on the component per §3a.7.
- Acceptance:
  - [ ] Compiles, no React warnings.
  - [ ] Pre-selects the saved value when revisited.
  - [ ] Shows error if Continue clicked with no selection.
  - [ ] Error inline message has `id={fieldName}-error` and is referenced in
        the fieldset's `aria-describedby`.
  - [ ] `?from=check-answers` redirects back to `/check-answers` on submit.
  - [ ] When `helpDetails` is passed, a `<details>`/`<summary>` block renders below the hint.
  - [ ] JSDoc present per §3a.7.
- Commit: `[Agent-B] feat(wk03): add reusable QuestionPage component`.

---

**Task B3 — PropertyTypePage** (~10 min) (content plan §3 question 1)

- Files: `wk03/starter/src/pages/PropertyTypePage.jsx`.
- Implement: thin wrapper around `<QuestionPage>` with the props from the
  content plan:
  - `pageTitle`: "What type of property do you live in?"
  - `fieldName`: `"propertyType"`
  - `backHref`: `"/"`
  - `onContinueNavigateTo`: `"/ownership"`
  - `errorMessage`: "Select the type of property you live in"
  - `options`: 5 options from content plan §3 Q1
  - no `hint`
- Acceptance:
  - [ ] Renders 5 radio options, correct labels, correct values.
  - [ ] Continue with no answer shows error summary at top + inline error.
  - [ ] Continue with answer navigates to `/ownership`.
- Commit: `[Agent-B] feat(wk03): implement PropertyTypePage`.

---

**Task B4 — OwnershipPage** (~10 min) (content plan §3 question 2)

- Files: `wk03/starter/src/pages/OwnershipPage.jsx`.
- Implement: `<QuestionPage>` with:
  - `pageTitle`: "What is your ownership status?"
  - `fieldName`: `"ownership"`
  - `backHref`: `"/property-type"`
  - `onContinueNavigateTo`: `"/income"`
  - `hint`: 'If you own your home with a mortgage, select "I own my home".'
  - `errorMessage`: "Select your ownership status"
  - `options`: 4 options from content plan §3 Q2
- Acceptance: as B3 (with the right copy).
- Commit: `[Agent-B] feat(wk03): implement OwnershipPage`.

---

**Task B5 — IncomePage** (~10 min) (content plan §3 question 3)

- Files: `wk03/starter/src/pages/IncomePage.jsx`.
- Implement: `<QuestionPage>` with:
  - `pageTitle`: "What is your total annual household income?"
  - `fieldName`: `"incomeBand"`
  - `backHref`: `"/ownership"`
  - `onContinueNavigateTo`: `"/insulation"`
  - `hint`: "Include the income of all adults living in your home, before tax and other deductions."
  - `errorMessage`: "Select your annual household income"
  - `options`: 3 options from content plan §3 Q3
- Acceptance: as B3.
- Commit: `[Agent-B] feat(wk03): implement IncomePage`.

---

**Task B6 — Lane B self-QA (includes responsive)** (~15 min)

- Run through:
  - [ ] Click through Start → Property → Ownership → Income → (404 OK; next lane).
  - [ ] Each page back link works.
  - [ ] Each page error pattern fires.
  - [ ] Page `<title>` updates correctly (check in browser tab).
  - [ ] Pre-selection persists when navigating back via Back link.
  - [ ] At least one `<details>` "Help with this question" block on Income page (Tier 2 per §3a.8).
  - [ ] **Responsive at 320px:** all radio labels readable, no horizontal scroll, Continue button reachable.
  - [ ] **Responsive at 640px:** typography scales.
- Log results in `AI_LOG.md`.

---

**Task B7 — Lane B change log entry** (~5 min) (see §3a.4)

- Files: **create** `wk03/docs/agents/Agent-<your-id>-changes.md`.
- Implement: one Markdown entry per task completed in Lane B. Newest first.
- Acceptance:
  - [ ] File exists.
  - [ ] One entry per completed Lane B task (B1–B6).
- Commit: `[Agent-B] docs(wk03): Lane B change log`.

---

### Lane C — Insulation, Heating, Check Answers, Result

**Agent identifier convention:** `Agent-C-<your-name>`.

**Pre-flight:** wait for Lane A task A2 push to main AND Lane B task B2
push to main; then `git pull`. (B2 publishes the QuestionPage component
that C5/C6 will consume.)

If Lane B is delayed, C may proceed with **C1/C2/C3 (display labels +
SummaryList + Panel + ResultPage)** which do not require QuestionPage.

---

**Task C1 — displayLabels helper** (~15 min)

- Files: **create** `wk03/starter/src/displayLabels.js`.
- Implement: `labelFor(field, value)` returning the display string per
  content plan §4 mapping table. Also `measuresFor(answers)` returning the
  ordered list of measure labels per content plan §6.
- Export both as named exports.
- Acceptance:
  - [ ] All 21 (field, value) pairs from the content plan §4 table return correct labels.
  - [ ] `measuresFor` returns the right measures per content plan §6.
  - [ ] Exhaustive map; calling with an unknown value returns the raw value (graceful fallback).
- Commit: `[Agent-C] feat(wk03): add display label and measures helpers`.

---

**Task C2 — Panel component** (~10 min)

- Files: **create** `wk03/starter/src/components/Panel.jsx`.
- Props: `title`, `body` (string or null), `variant` (`"confirmation"` |
  `"not-eligible"`).
- Render per §6.5.
- Acceptance:
  - [ ] Title rendered as H1 inside the panel (matches GOV.UK).
  - [ ] Variant `not-eligible` switches background to dark grey.
- Commit: `[Agent-C] feat(wk03): add Panel component`.

---

**Task C3 — SummaryList component** (~15 min)

- Files: **create** `wk03/starter/src/components/SummaryList.jsx`.
- Props: `rows` (array of `{ key, value, changeHref, changeHiddenText }`).
- Render the `<dl>` pattern per §6.4. The visually-hidden span inside each
  Change link uses `changeHiddenText`.
- Acceptance:
  - [ ] One `<div class="govuk-summary-list__row">` per row.
  - [ ] Change link points to `${changeHref}?from=check-answers`.
- Commit: `[Agent-C] feat(wk03): add SummaryList component`.

---

**Task C4 — CheckAnswersPage** (~20 min) (content plan §4)

- Files: `wk03/starter/src/pages/CheckAnswersPage.jsx`.
- Implement:
  - Back link to `/heating`.
  - H1: "Check your answers".
  - Intro paragraph per content plan §4.
  - 5 rows in `<SummaryList>` (PropertyType, Ownership, IncomeBand,
    Insulation, Heating) — values rendered via `labelFor` from C1.
  - Submit button "Submit and see result" → `navigate('/result')`.
  - Guard: if any answer is empty (e.g. user landed here without
    completing), redirect to the first unanswered question.
  - Set document.title.
- Acceptance:
  - [ ] All 5 rows show the human-readable answer.
  - [ ] Change link on each row goes to `<question>?from=check-answers`.
  - [ ] Submit goes to `/result`.
  - [ ] If `propertyType === ""`, user is redirected to `/property-type`.
- Commit: `[Agent-C] feat(wk03): implement CheckAnswersPage`.

---

**Task C5 — InsulationPage** (~10 min) (content plan §3 question 4)

- Files: `wk03/starter/src/pages/InsulationPage.jsx`.
- Implement: `<QuestionPage>` (from Lane B) with:
  - `pageTitle`: "What insulation does your home currently have?"
  - `fieldName`: `"insulation"`
  - `backHref`: `"/income"`
  - `onContinueNavigateTo`: `"/heating"`
  - `hint`: "If you are not sure, check your Energy Performance Certificate (EPC). Your landlord or mortgage provider may have a copy."
  - `errorMessage`: "Select the insulation your home currently has"
  - 3 options from content plan §3 Q4
- Acceptance: as Lane B's question pages.
- Commit: `[Agent-C] feat(wk03): implement InsulationPage`.

---

**Task C6 — HeatingPage** (~10 min) (content plan §3 question 5)

- Files: `wk03/starter/src/pages/HeatingPage.jsx`.
- Implement: `<QuestionPage>` with:
  - `pageTitle`: "What is your current main heating system?"
  - `fieldName`: `"heating"`
  - `backHref`: `"/insulation"`
  - `onContinueNavigateTo`: `"/check-answers"`
  - `hint`: "Select the system that heats most of your home."
  - `errorMessage`: "Select your current main heating system"
  - 5 options from content plan §3 Q5
- Acceptance: as Lane B's question pages.
- Commit: `[Agent-C] feat(wk03): implement HeatingPage`.

---

**Task C7 — ResultPage** (~30 min) (content plan §7)

- Files: `wk03/starter/src/pages/ResultPage.jsx`.
- Implement:
  - No back link (per content plan §7).
  - Read `answers` from context. If empty, redirect to `/`.
  - Compute `const { outcome, reason, measures } = eligibility(answers)`
    (from Lane D).
  - Branch on `outcome` to pick panel + body + next-steps copy:
    - `eligible` (reason `owner-low-income`): variant A copy.
    - `partial` (reason `renter`): variant B-renter copy.
    - `partial` (reason `owner-mid-income`): variant B-owner copy.
    - `ineligible` (reason `income-too-high`): variant C-income copy.
    - `ineligible` (reason `no-measures-needed`): variant C-already-fitted copy.
    - `ineligible` (reason `default`): variant C-already-fitted fallback (use the same copy).
  - Render `<Panel>` (C2) at the top.
  - Render `<ul class="govuk-list govuk-list--bullet">` of measures when
    eligible/partial-owner. Use `measuresFor(answers)` from C1.
  - Render "What to do next" H2 + copy per variant.
  - Render the final link ("Find an approved installer" or "Find other
    energy efficiency schemes") with `href="#"`.
  - Set `document.title` to a variant-appropriate string ending with
    `" - Green Home Grant - GOV.UK"`.
- Acceptance:
  - [ ] Each variant's copy matches content plan §7 verbatim.
  - [ ] Eligible variant shows the measures bullet list.
  - [ ] Ineligible-no-measures variant does NOT show measures bullets.
  - [ ] No back link rendered.
  - [ ] All copy uses helpers (no hardcoded display labels — comes from C1).
- Commit: `[Agent-C] feat(wk03): implement ResultPage with all outcome variants`.

---

**Task C8 — Lane C self-QA (includes responsive)** (~20 min)

- Run through 3 happy paths end-to-end (one per outcome):
  - Owner + low income + partial insulation + gas boiler → eligible.
  - Private renter + any income (not high) → partial.
  - High income → ineligible.
- And the edge cases:
  - Owner + full insulation + heat pump → ineligible (no-measures-needed).
  - Owner + mid income → partial.
- For each path, confirm:
  - [ ] Document title updates correctly on each step.
  - [ ] Back link, error pattern, pre-selection on Back, all work.
  - [ ] Change link from check-answers returns to check-answers.
  - [ ] At least one `<details>` block on Insulation and Heating pages (Tier 2 per §3a.8).
  - [ ] **Responsive at 320px:** check-answers summary list reflows to single-column (existing CSS rule); result page panel readable.
  - [ ] **Responsive at 640px:** layouts adapt cleanly.
- Log results in `AI_LOG.md`.

---

**Task C9 — Lane C change log entry** (~5 min) (see §3a.4)

- Files: **create** `wk03/docs/agents/Agent-<your-id>-changes.md`.
- Implement: one Markdown entry per task completed in Lane C. Newest first.
- Acceptance:
  - [ ] File exists.
  - [ ] One entry per completed Lane C task (C1–C8).
- Commit: `[Agent-C] docs(wk03): Lane C change log`.

---

### Lane D — Eligibility logic + tests + test infra

**Agent identifier convention:** `Agent-D-<your-name>`.

**Pre-flight:** No dependency on Lane A/B/C for Tasks D1–D4. Tasks D5–D6
(component tests) need the components from Lane B/C to exist.

---

**Task D1 — Test infrastructure: add Vitest + RTL** (~15 min)

- Files: `wk03/starter/package.json`, `wk03/starter/vite.config.js`,
  **create** `wk03/starter/src/__tests__/setup.js`.
- Modify `package.json`:
  - Add to `devDependencies`:
    ```
    "vitest": "^2.1.0",
    "@vitest/ui": "^2.1.0",
    "@testing-library/react": "^16.1.0",
    "@testing-library/jest-dom": "^6.6.0",
    "@testing-library/user-event": "^14.5.2",
    "jsdom": "^25.0.0"
    ```
  - Add to `scripts`:
    ```
    "test": "vitest",
    "test:run": "vitest run"
    ```
- Modify `vite.config.js`:
  - Add `/// <reference types="vitest" />` at top.
  - Inside `defineConfig({ ... })` add:
    ```js
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/__tests__/setup.js',
      css: false,
    },
    ```
- Create `src/__tests__/setup.js`:
  ```js
  import '@testing-library/jest-dom/vitest';
  import { cleanup } from '@testing-library/react';
  import { afterEach } from 'vitest';
  afterEach(() => cleanup());
  ```
- Acceptance:
  - [ ] `npm install` succeeds with new deps.
  - [ ] `npm run test:run` exits 0 with "no tests" (no tests yet).
- Commit: `[Agent-D] chore(wk03): add Vitest + RTL test infrastructure`.

---

**Task D2 — eligibility.js function** (~30 min) (content plan §5 + §6)

- Files: **create** `wk03/starter/src/eligibility.js`.
- Implement per §3.3 contract and content plan §5 rules:
  - Pure function `eligibility(answers)`.
  - Apply rules in priority order. First match wins.
  - Compute `measures` array from content plan §6 (call `measuresFor` from
    `displayLabels.js` if Lane C has shipped C1; otherwise inline a local
    copy and replace later — coordinate via `AI_LOG.md`).
  - Return the shape from §3.3.
- Acceptance: covered by Task D3 tests.
- Commit: `[Agent-D] feat(wk03): add eligibility function per content plan §5`.

---

**Task D3 — Eligibility unit tests** (~45 min)

- Files: **create** `wk03/starter/src/__tests__/eligibility.test.js`.
- Minimum 8 tests — exactly one per rule branch, plus measures:
  1. Rule 1 — high income returns `ineligible` / `income-too-high` regardless of other fields.
  2. Rule 2 — full insulation + heat pump returns `ineligible` / `no-measures-needed`.
  3. Rule 3 — private renter returns `partial` / `renter`.
  4. Rule 3 — council tenant returns `partial` / `renter`.
  5. Rule 3 — housing association returns `partial` / `renter`.
  6. Rule 4 — owner + mid income returns `partial` / `owner-mid-income`.
  7. Rule 5 — owner + low income returns `eligible` / `owner-low-income`.
  8. Default — owner + missing fields (or unmatched combination) returns `ineligible` / `default`.
  9. Measures — flat does NOT get loft insulation in the measures list.
  10. Measures — full insulation removes both insulation measures.
  11. Measures — heat pump owner does not get the heat-pump measure suggested again.
- Acceptance:
  - [ ] `npm run test:run` reports >= 8 passing tests.
  - [ ] Every rule (1–5) has a passing test.
- Commit: `[Agent-D] test(wk03): unit tests for eligibility rules and measures`.

---

**Task D4 — Bug-bash eligibility on edge cases** (~15 min)

- Files: extend `eligibility.test.js` with edge cases:
  - Empty answers object → does not throw; returns `ineligible` / `default`.
  - Unknown values (e.g. `propertyType: "boat"`) → returns `ineligible` /
    `default`, does not crash.
- Acceptance:
  - [ ] Tests added and passing.
  - [ ] `eligibility` does not throw on any input.
- Commit: `[Agent-D] test(wk03): edge-case coverage for eligibility`.

---

**Task D5 — Light component test for QuestionPage** (~30 min)

- Files: **create** `wk03/starter/src/__tests__/QuestionPage.test.jsx`.
- Requires Lane B Task B2 to be on main.
- Wrap in `<MemoryRouter>` + `<FormProvider>` for context.
- Test scenarios:
  1. Renders all radio options provided.
  2. Clicking Continue without selection shows the error summary AND the
     inline error message.
  3. Error summary is focused after error appears (use `document.activeElement`).
  4. Pre-selects the option matching the value already in form state.
- Acceptance:
  - [ ] `npm run test:run` shows >= 4 passing tests for QuestionPage.
- Commit: `[Agent-D] test(wk03): component tests for QuestionPage`.

---

**Task D6 — README test instructions + AI_LOG entry** (~5 min)

- Files: append a short "Running tests" section to `wk03/starter/README.md`
  (or create a new section if absent) with:
  ```
  npm run test         # watch mode
  npm run test:run     # single run
  ```
- Log final entry in `AI_LOG.md`.
- Commit: `[Agent-D] docs(wk03): add test running instructions`.

---

**Task D7 — Lane D change log entry** (~5 min) (see §3a.4)

- Files: **create** `wk03/docs/agents/Agent-<your-id>-changes.md`.
- Implement: one Markdown entry per task completed in Lane D. Newest first.
- Acceptance:
  - [ ] File exists.
  - [ ] One entry per completed Lane D task (D1–D6).
- Commit: `[Agent-D] docs(wk03): Lane D change log`.

---

## 8. Cross-lane sequencing

```
Lane A ──[A1]──[A2 BLOCKING]──[A3]──[A4]──[A5]──[A6]──[A7]──[A8]──[A9 QA]
                  │
                  ▼ (push to main)
Lane B ──────────[B1]──[B2 BLOCKING]──[B3]──[B4]──[B5]──[B6 QA]
                            │
                            ▼ (push to main)
Lane C ────[C1]──[C2]──[C3]──[C4]──[C5]──[C6]──[C7]──[C8 QA]
                            (C5/C6/C7 need B2 on main)

Lane D ──[D1]──[D2]──[D3]──[D4]────────────────[D5]──[D6]
                                                 ▲ needs B2 on main
```

Critical-path tasks (delay anything else):

- **A2** (FormContext) — blocks all context-consuming work in B/C.
- **B2** (QuestionPage) — blocks B3/B4/B5/C5/C6 page implementations and D5.
- **D2** (`eligibility.js`) — blocks Lane C Task C7 (ResultPage). Lane C
  should mock the function temporarily if needed to avoid a stall.

If a blocking task slips by > 60 min, mention it in `AI_LOG.md` so other
lanes can re-plan.

## 9. Integration checklist (anyone runs after their lane finishes)

A "lane complete" PR is the last commit in the lane. After every lane has
pushed to main, anyone may run this integration sweep:

**Functional**
- [ ] `npm install && npm run dev` — app loads at `/`.
- [ ] Click "Start now" → property-type → ownership → income → insulation → heating → check-answers → result. No 404s, no console errors.
- [ ] On a question page, click Continue with no answer → error summary appears at top, inline error appears, error summary is focused. (WCAG 3.3.1, 4.1.3)
- [ ] Click error summary link → focus jumps to first radio of the errored field.
- [ ] On check-answers page, click "Change" on any row → returns to that question → answer → Continue → returns to check-answers. (3.3.7)
- [ ] On result page, no back link. Three outcome variants are reachable.
- [ ] `document.title` updates on every page navigation. (2.4.2)

**Accessibility**
- [ ] Tab through any page: skip-link is first, then header, then back link, then form, then footer. (2.4.3)
- [ ] No `title`-attribute tooltips anywhere; all "more info" is via hint text or `<details>` (§3a.8).
- [ ] All `<details>` elements expand/collapse with keyboard and screen reader.

**Responsive (§3a.5)**
- [ ] At 320×568 (devtools mobile), no horizontal scrolling on any page.
- [ ] At 640px, typography scales (use DevTools at exactly 640px).
- [ ] At default desktop (≥1024px), content centred and max-width 960px.
- [ ] All tap targets ≥ 24×24 CSS px at every breakpoint. (2.5.8)

**Architecture / standards (§3a)**
- [ ] No state libraries in `package.json` (Redux/Zustand/etc.). (§3a.1)
- [ ] No `<Route>` JSX outside `src/router.jsx`. (§3a.3)
- [ ] `grep -R "console.log" src/` returns nothing. (§3a.9)
- [ ] Every new file has a header comment; every exported component has JSDoc. (§3a.7)
- [ ] No commented-out code blocks committed.

**Logs and changelogs**
- [ ] `npm run test:run` reports >= 12 passing tests (8 eligibility + 4 QuestionPage).
- [ ] `AI_LOG.md` has at least 3 entries across the four agents.
- [ ] `wk03/docs/agents/` contains one `Agent-<id>-changes.md` file per agent that worked. (§3a.4)

## 10. Commit / branch workflow

All four lanes commit to `main`. The repo expects frequent small commits
rather than long-lived branches. Workflow:

1. Before any session: `git pull --rebase origin main`.
2. Read the tail of `AI_LOG.md` for new context.
3. Make changes scoped to one task.
4. `git add -- <only-your-files>` then `git commit -m "[Agent-X] <type>(wk03): <one-line summary>"`.
5. `git pull --rebase origin main` (catch any new commits from other lanes).
6. `git push origin main`.
7. If rebase has conflicts on a file you don't own, **stop**, open
   `AI_LOG.md`, post the conflict, and coordinate.

Commit message types: `feat`, `fix`, `chore`, `style`, `test`, `docs`,
`refactor`. Scope is always `wk03`.

## 11. Definition of done (whole plan)

- [ ] All 16 acceptance-criteria boxes in the README of `w03-hackathon-citizen-service` pass (the labs README, not this plan).
- [ ] Day 1 target met: at least one full path renders and reaches the result page with the right outcome.
- [ ] AI_LOG.md has at least 3 entries with four fields each, one per AI-assisted session.
- [ ] Every agent has their own `wk03/docs/agents/Agent-<id>-changes.md` with one entry per completed task. (§3a.4)
- [ ] Tests pass: `npm run test:run` exit code 0.
- [ ] Dev server starts cleanly.
- [ ] No `console.error` or `console.warn` in dev mode for any route.
- [ ] All §9 integration checks pass (functional, accessibility, responsive, standards, logs).

## 12. Open questions (raise in `AI_LOG.md` if you hit them)

- Should there be a real "Skip to main content" focus management when an
  in-page link is clicked (vs. relying on the browser default)? Default is
  acceptable for AA; if testing reveals a focus-management gap, file a
  follow-up.
- Should Result page provide a "Start again" link? Not required by the
  content plan or AC. Defer unless a reviewer asks.
- Live announcement of validation errors via `aria-live` — using
  `role="alert"` on the error summary already covers this. No additional
  `aria-live` region needed.

---

*End of plan. If a task description is ambiguous, prefer fidelity to the
content plan over creative interpretation. When in doubt, ask in `AI_LOG.md`.*

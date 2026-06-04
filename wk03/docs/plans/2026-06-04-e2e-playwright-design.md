# Design: End-to-end tests with Playwright (stretch goal)

**Author:** Agent-Jack
**Date:** 2026-06-04
**Status:** Design — pending user review, then `writing-plans`
**Stretch goal:** README §"Stretch Goals" — *"Add end-to-end tests with Playwright covering the full user journey."*

---

## 1. Goal & scope

Add a committed, repeatable, browser-driven end-to-end (E2E) test suite that exercises the
**full user journey** of the Green Home Grant eligibility checker in a real browser — the wiring
that the existing jsdom tests (Vitest + React Testing Library) cannot fully prove: real navigation,
the production-style render, `localStorage` persistence across a reload, a real file download, focus
management on route change, keyboard operation, and responsive reflow.

**Coverage decision (confirmed with user): comprehensive.** Both pathways (owner / tenant), all six
eligibility outcomes, plus the cross-cutting behaviours below and automated WCAG scans.

This is **additive test infrastructure only** — no application source changes are planned. The suite
*acceptance-tests existing behaviour*; a failing test means either a selector mistake (fix the test)
or a genuine app defect (surface it, do not paper over it).

**Out of scope:** changing app behaviour, replacing the Vitest unit/integration suite (it stays),
CI pipeline wiring (no CI exists in this repo), cross-browser beyond Chromium.

## 2. What already exists (and why E2E still earns its keep)

- `src/__tests__/journey.test.jsx` already drives both pathways through the real router/context/guards
  in **jsdom**. It is an excellent **selector cheat-sheet** (exact roles, labels, headings, result copy)
  and we reuse those queries verbatim.
- jsdom **cannot** validate: a real browser render, `page.reload()` persistence, an actual `download`
  event from the lazy-loaded jsPDF path, `<main>` focus on route change in a real a11y tree,
  keyboard tab-order, 320px reflow/horizontal-scroll, or axe-core WCAG scanning. Those are exactly
  what this suite adds, and several map directly to README acceptance criteria (see §8).

## 3. Harness — proven before designing (spike results, 2026-06-04)

- App is a Vite 5.4 + React 18 SPA, `BrowserRouter`, react-router v6. Dev server binds `0.0.0.0`.
- `os.hostname()` → `lab14102.labs.decoded.com`, resolving to the VM's own interface `192.168.14.102`.
  Per project CLAUDE.md we must **not** use `localhost`/`127.0.0.1`; we use the lab hostname (also more
  robust here — `localhost` resolves to IPv6 `::1` first, which would miss an IPv4 `0.0.0.0` bind).
- Spike (curl): **both** `vite dev` (port 5050) and `vite preview` (4173) return HTTP 200 with the real
  app via localhost, the lab hostname, **and** the IP — **no host-check / `allowedHosts` rejection**.
  So **no `vite.config.js` server changes are required.**
- Spike (Playwright MCP browser → dev server at the lab hostname): the SPA renders fully — header,
  phase banner, H1, intro, the 5-item list, **Start now** button, footer — and `main [active]`
  confirms focus-on-route-change works. Headless Chromium reachability is proven end-to-end.
- Tooling ready: Playwright browser binaries already cached in `~/.cache/ms-playwright`
  (chromium-1224, firefox-1522, …); npm registry reachable (`@playwright/test` 1.60.0 resolvable).
- `.gitignore` (repo root) **already** has a Playwright section pre-added for this stretch goal:
  `playwright-report/`, `test-results/`, `.playwright/`, `.playwright-mcp/`. `*.spec.js` files are
  **not** caught by the Python `*.spec` rule (verified via `git check-ignore`).

## 4. Approach (chosen)

**`@playwright/test` driving the Vite *dev* server, auto-started by Playwright's `webServer`.**

Rejected alternatives: (B) `vite preview` — tests the prod bundle and gives a clean console, but adds a
build step + stale-dist footgun and is the less-proven path here; its only real advantage (clean console)
doesn't matter because we are not asserting console-cleanliness. (C) Playwright MCP interactively — not a
committed, runnable regression suite, which defeats the goal.

Dev-server trade-off accepted: the dev server's HMR `wss://` retry fails in headless Chromium (console
noise) and React StrictMode double-invokes effects in dev. Both are **harmless** to these tests — the
app's effects are idempotent (focus, localStorage write, guard `navigate(..., {replace:true})`), and we
do **not** assert console cleanliness.

## 5. Architecture & file layout

All paths under `wk03/starter/` (the npm project root).

| File | Purpose |
|------|---------|
| `playwright.config.js` | `testDir: './e2e'`; chromium-only project; `use.baseURL` = `process.env.E2E_BASE_URL ?? `http://${os.hostname()}:5050``; `webServer` runs `npm run dev` with `env: { VITE_PORT: '5050' }`, `url` = baseURL, `reuseExistingServer: true`, generous `timeout`; `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`, `reporter: [['list'], ['html', { open: 'never' }]]`, `retries: process.env.CI ? 1 : 0`, `fullyParallel: true`. |
| `e2e/helpers.js` | Reusable, journey-readable step helpers + answer-set constants (see §7). |
| `e2e/journeys.spec.js` | The six end-to-end outcome journeys (§6.1). |
| `e2e/navigation.spec.js` | Start→Q1, path-aware step indicator, Back preserves answer, tenant branch routing (§6.2). |
| `e2e/check-answers.spec.js` | Path-aware summary rows + "Change" round-trip + Submit (§6.3). |
| `e2e/validation.spec.js` | GOV.UK empty-field error pattern (§6.4). |
| `e2e/guards.spec.js` | Deep-link redirect guards (§6.5). |
| `e2e/save-and-return.spec.js` | `localStorage` persistence across reload + resume banner (§6.6). |
| `e2e/pdf-download.spec.js` | Real PDF `download` event from the Result page (§6.7). |
| `e2e/accessibility.spec.js` | Skip link, focus-on-route-change, keyboard-only step, 320px reflow, a11y-statement nav, **axe-core** scans (§6.8). |
| `e2e/README.md` | How to run (`npm run test:e2e`; `npx playwright install chromium` note). |

**`package.json`** — add devDeps `@playwright/test` (^1.60.0) and `@axe-core/playwright`; add scripts
`"test:e2e": "playwright test"` and `"test:e2e:report": "playwright show-report"`. `npm test` (Vitest)
is unchanged and stays the unit/integration entry point.

**`vite.config.js`** — single vitest-only change: narrow `test.include` to
`['src/**/*.{test,spec}.{js,jsx}']` so Vitest never tries to execute the Playwright specs (Vitest's
default `include` matches `e2e/*.spec.js`, and `@playwright/test`'s `test`/`expect` would crash under
Vitest). No `server`/`hmr`/`plugins` changes. Verify `npm test` still discovers all 61 existing tests.

## 6. Test coverage

### 6.1 `journeys.spec.js` — all six outcomes, Start → … → Result

Selectors/copy taken verbatim from the page sources and `journey.test.jsx`.

| # | Path | Answers | Outcome / reason | Key result-page assertions |
|---|------|---------|------------------|----------------------------|
| 1 | Owner | own / low / none / gas-boiler | **eligible** / owner-low-income | Panel "You may be eligible for a Green Home Grant" + "up to £10,000"; measures bullets (Loft, Internal wall, Air source heat pump); "What to do next"; "Find an approved installer" |
| 2 | Owner | own / mid / none / gas-boiler | **partial** / owner-mid-income | "You may be partially eligible…"; "up to £5,000" |
| 3 | Owner | own / high / none / gas-boiler | **ineligible** / income-too-high | "You are not eligible…"; "above the threshold" |
| 4 | Owner | own / low / full / heat-pump | **ineligible** / no-measures-needed | "already has the insulation and heating measures" |
| 5 | Tenant | private-renter / consent **yes** / partial | **partial** / renter | "You may be partially eligible…"; "your landlord needs to apply…"; indicative measures list |
| 6 | Tenant | council / consent **no** / none | **ineligible** / no-landlord-consent | "You are not eligible…"; "do not have your landlord's permission" |

(The `default` reason is unreachable through the UI — not forced.)

### 6.2 `navigation.spec.js`
- Start page **Start now** → URL `/property-type`.
- Step indicator path-awareness: owner shows "Step 2 of 5"; choosing a renter shows "Step 2 of 4".
- **Back** link returns to the prior question with the previously-chosen radio still **checked**.
- Tenant branch routing: `private-renter` Continue → `/landlord-consent` (not `/income`); from Insulation,
  Continue → `/check-answers` (heating skipped).

### 6.3 `check-answers.spec.js`
- Owner: summary shows 5 rows with correct keys + display values; tenant: 4 rows (no income/heating).
- **Change** round-trip: click "Change" on a row → lands on that question with the value pre-checked →
  change it → Continue returns to `/check-answers` (the `?from=check-answers` override) → summary reflects
  the new value.
- **Submit and see result** → `/result`.

### 6.4 `validation.spec.js`
- Continue with no selection: error summary "There is a problem" rendered at top **and focused**, its link
  targets the first radio (`#<field>-1`); inline `.govuk-error-message` with visually-hidden "Error:";
  `document.title` prefixed "Error:". Clicking the summary link moves focus to the radio.

### 6.5 `guards.spec.js`
- Deep-link `/check-answers` on empty state → redirected to `/property-type`.
- Deep-link `/result` on empty state → redirected to `/`.

### 6.6 `save-and-return.spec.js`
- Answer ≥1 question; assert `localStorage['ghg:answers:v1']` populated (via `page.evaluate`).
- `page.reload()` then go to `/` → "You have a partially completed check" banner with **Continue your
  check** / **Start again**.
- **Continue your check** resumes the flow; **Start again** clears state (banner gone, storage cleared).

### 6.7 `pdf-download.spec.js`
- Complete journey #1 to `/result`; `const dl = page.waitForEvent('download')` **before** clicking
  "Download your result (PDF)" (the handler lazy-`import()`s `resultPdf`, so the click→download has an
  async tick — `waitForEvent` covers it); assert `download.suggestedFilename() === 'green-home-grant-result.pdf'`
  and the saved file is non-empty.

### 6.8 `accessibility.spec.js`
- **Skip link**: first Tab focuses "Skip to main content"; its target is `#main-content`.
- **Focus on route change**: after Start, the focused element is `<main id="main-content">`.
- **Keyboard-only step**: complete one question using only Tab / Arrow / Space / Enter (no mouse).
- **320px reflow**: `setViewportSize({ width: 320, height: 800 })` on a question page → no horizontal
  scroll (`scrollWidth <= clientWidth`).
- **A11y statement**: footer "Accessibility statement" link → `/accessibility-statement` renders the
  PSBAR section headings; Back returns.
- **axe-core (`@axe-core/playwright`)**: scan Start, a question page, Check-answers, an (eligible) Result
  page, and the Accessibility-statement page with `new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']).analyze()`; assert **zero** violations. If pre-existing violations surface,
  surface them to the user and fix small ones or scope the specific rule with a documented comment — do
  not silently disable broadly.

## 7. `e2e/helpers.js` (interface sketch)

Keeps each spec a readable journey rather than a wall of clicks.

```js
// Label-driven (matches GOV.UK <label> association; mirrors journey.test.jsx getByLabelText).
export async function chooseAndContinue(page, label) { … getByLabel(label).check(); getByRole('button',{name:'Continue'}).click(); }
export async function startCheck(page) { goto('/'); getByRole('button',{name:'Start now'}).click(); }
// Whole-path shortcuts returning at /check-answers (or /result via submit()).
export async function answerOwner(page, { propertyType, income, insulation, heating }) { … }
export async function answerTenant(page, { propertyType, ownership, consent, insulation }) { … }
export const LABELS = { /* option value → visible label, mirrored from the page sources */ };
```

Exact option labels (from sources): property — "Detached house" / "Semi-detached house" /
"Terraced house" / "Flat or apartment" / "Bungalow"; ownership — "I own my home" / "I rent from a private
landlord" / "I rent from a housing association" / "I rent from a council or local authority"; income —
"Under £31,000" / "£31,000 to £60,000" / "Over £60,000"; consent — "Yes" / "No" / "Not sure"; insulation
— "No insulation" / "Some insulation (for example, loft only or walls only)" / "Full insulation (loft and
walls)"; heating — "Gas boiler" / "Oil boiler" / "Electric storage heaters" / "Heat pump (air source or
ground source)" / "Other". Buttons: "Start now", "Continue", "Submit and see result", "Download your
result (PDF)", "Start a new check", "Continue your check", "Start again".

## 8. Mapping to README acceptance criteria

The suite gives browser-level evidence for many acceptance criteria, complementing the unit tests:
Start→Q1 nav; ≥5 question pages w/ Continue; Back link; Check-answers summary; per-row Change links;
result eligibility (eligible/partial/ineligible); labelled inputs (axe + label-driven selectors);
keyboard operability (keyboard-only step); 320px reflow; client-side validation + GOV.UK error pattern
(summary at top + inline per field).

## 9. Verification gates (before commit)

1. `npm run test:e2e` → **all green** in real Chromium.
2. `npm test` (Vitest) → still **61/61** and discovers no e2e files.
3. `npm run build` → exits 0.
4. Adversarial review pass (coverage completeness, flakiness/anti-patterns, selector correctness,
   acceptance-criterion mapping) before committing.
5. Repo workflow: feature branch (`agent-jack/e2e-playwright`), `AI_LOG.md` entry in the same commit,
   `git pull --rebase` before push, push, open PR.

## 10. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| `webServer.env` not honoured → server on 5002, baseURL 5050 fails | Caught immediately by the first smoke run; fall back to `command: 'VITE_PORT=5050 npm run dev'` (Linux target). |
| Cached chromium revision ≠ @playwright/test 1.60.0's pinned revision | `npx playwright install chromium` (registry reachable) — fast, browsers mostly cached. |
| axe finds pre-existing violations | Surface to user; fix small issues or scope the specific rule with a comment; never broad-disable. |
| Flaky waits | Use Playwright web-first auto-waiting assertions (`expect(locator).toBeVisible()`, URL assertions) — no manual sleeps. |
| Port 5050 already busy | `reuseExistingServer: true` reuses a compatible server; otherwise Playwright errors clearly. |

## 11. Non-goals
No app source changes; no CI config; no replacement of Vitest; no webkit/firefox; no visual-regression
screenshots as assertions (screenshots only on failure for debugging).

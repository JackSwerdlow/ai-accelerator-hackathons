# Playwright E2E Suite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a comprehensive, browser-driven Playwright E2E suite covering the full user journey of the Green Home Grant eligibility checker.

**Architecture:** `@playwright/test` drives the Vite **dev** server (auto-started by Playwright's `webServer`), chromium-only, `baseURL` at the lab hostname on a dedicated port 5050. Specs live in `wk03/starter/e2e/`, share `e2e/helpers.js`, and are isolated per-test by Playwright's default fresh-context model (so `localStorage` never leaks between tests). The suite acceptance-tests existing behaviour — no application source changes.

**Tech Stack:** `@playwright/test` ^1.60.0, `@axe-core/playwright`, Vite 5 dev server, React 18 SPA (`BrowserRouter`, react-router v6).

**Companion design spec:** `wk03/docs/plans/2026-06-04-e2e-playwright-design.md`.

**Repo-workflow note (overrides the skill's per-step commits):** the wk03 repo requires one `AI_LOG.md`-bearing commit per task on a feature branch + PR. So the TDD loop (write spec → run → confirm green) runs locally per task, but we **commit once** at the end (Task 11) with the AI_LOG entry, not after every file. The design commit (`ed7ff42`) is already on branch `agent-jack/e2e-playwright`.

**Key selector facts (verified against source — use verbatim):**
- Radio **labels** (question pages): property — `Detached house` / `Semi-detached house` / `Terraced house` / `Flat or apartment` / `Bungalow`; ownership — `I own my home` / `I rent from a private landlord` / `I rent from a housing association` / `I rent from a council or local authority`; consent — `Yes` / `No` / `Not sure`; income — `Under £31,000` / `£31,000 to £60,000` / `Over £60,000`; insulation — `No insulation` / `Some insulation (for example, loft only or walls only)` / `Full insulation (loft and walls)`; heating — `Gas boiler` / `Oil boiler` / `Electric storage heaters` / `Heat pump (air source or ground source)` / `Other`.
- ⚠️ **Check-answers summary VALUES use SHORT labels** (`labelFor`): `Some insulation`, `Full insulation`, `Heat pump` — different from the long radio labels. Select radios with the long label (use a regex for insulation/heat-pump); assert summary values with the short label.
- ⚠️ `getByLabel('No')` must use `{ exact: true }` or it also matches `Not sure`. Apply `{ exact: true }` to all string labels.
- Buttons: `Start now`, `Continue`, `Submit and see result`, `Download your result (PDF)`, `Start a new check`, `Continue your check`, `Start again`.
- Result panel `<h1>` titles: eligible `You may be eligible for a Green Home Grant`; partial `You may be partially eligible for a Green Home Grant`; ineligible `You are not eligible for a Green Home Grant`. Eligible body contains `up to £10,000`; mid-income body `up to £5,000`.
- Error summary: heading `There is a problem`; link href `#<field>-1`; inline `.govuk-error-message`; `document.title` prefixed `Error: `. The `.govuk-error-summary` container auto-focuses on mount.
- Step indicator text: `Step 2 of 5` (owner) / `Step 2 of 4` (tenant). PDF filename: `green-home-grant-result.pdf`. localStorage key: `ghg:answers:v1`.
- A11y statement: H1 `Accessibility statement for the Green Home Grant eligibility checker`; H2 examples `How accessible this website is`, `Enforcement procedure`.

---

## Task 0: Harness — deps, config, helpers, smoke test (prove green)

**Files:**
- Modify: `wk03/starter/package.json` (devDeps + scripts)
- Create: `wk03/starter/playwright.config.js`
- Create: `wk03/starter/e2e/helpers.js`
- Create: `wk03/starter/e2e/smoke.spec.js`
- Modify: `wk03/starter/vite.config.js` (vitest `test.include` only)

- [ ] **Step 1: Install dev dependencies**

Run (cwd `wk03/starter`):
```bash
npm install -D @playwright/test@^1.60.0 @axe-core/playwright
npx playwright install chromium   # browsers mostly cached; this confirms the pinned revision
```
Expected: install succeeds; `node_modules/@playwright/test` and `node_modules/@axe-core/playwright` present.

- [ ] **Step 2: Add npm scripts to `package.json`**

In the `"scripts"` block add:
```json
    "test:e2e": "playwright test",
    "test:e2e:report": "playwright show-report"
```
(Leave `dev`/`build`/`preview`/`test`/`test:run` unchanged. `@playwright/test`/`@axe-core/playwright` go under `devDependencies`.)

- [ ] **Step 3: Create `playwright.config.js`**

```js
// @ts-check
import { defineConfig, devices } from '@playwright/test';
import os from 'node:os';

const PORT = Number(process.env.E2E_PORT) || 5050;
const HOST = process.env.E2E_HOST || os.hostname(); // lab hostname; per CLAUDE.md, not localhost
const BASE_URL = process.env.E2E_BASE_URL || `http://${HOST}:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    env: { VITE_PORT: String(PORT) },
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
```

- [ ] **Step 4: Create `e2e/helpers.js`**

```js
// Reusable, journey-readable step helpers + answer-set constants for the
// Green Home Grant E2E suite. Labels mirror the page sources verbatim.
import { expect } from '@playwright/test';

// Radio labels by internal value. Long labels use a regex so a substring is enough.
export const LABELS = {
  property: {
    detached: 'Detached house',
    'semi-detached': 'Semi-detached house',
    terraced: 'Terraced house',
    flat: 'Flat or apartment',
    bungalow: 'Bungalow',
  },
  ownership: {
    owner: 'I own my home',
    'private-renter': 'I rent from a private landlord',
    'housing-association': 'I rent from a housing association',
    council: 'I rent from a council or local authority',
  },
  consent: { yes: 'Yes', no: 'No', 'not-sure': 'Not sure' },
  income: { low: 'Under £31,000', mid: '£31,000 to £60,000', high: 'Over £60,000' },
  insulation: { none: 'No insulation', partial: /Some insulation/, full: /Full insulation/ },
  heating: {
    'gas-boiler': 'Gas boiler',
    'oil-boiler': 'Oil boiler',
    'electric-storage': 'Electric storage heaters',
    'heat-pump': /Heat pump/,
    other: 'Other',
  },
};

/** Select a radio by its visible label. Strings match exactly (so "No" != "Not sure"). */
export async function choose(page, label) {
  const opts = typeof label === 'string' ? { exact: true } : {};
  await page.getByLabel(label, opts).check();
}

export async function clickContinue(page) {
  await page.getByRole('button', { name: 'Continue' }).click();
}

export async function chooseAndContinue(page, label) {
  await choose(page, label);
  await clickContinue(page);
}

/** Start page -> first question. */
export async function startCheck(page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Start now' }).click();
  await expect(page).toHaveURL(/\/property-type/);
}

/** Owner path: property -> own -> income -> insulation -> heating. Ends at /check-answers. */
export async function answerOwner(
  page,
  { property = 'detached', income = 'low', insulation = 'none', heating = 'gas-boiler' } = {},
) {
  await chooseAndContinue(page, LABELS.property[property]);
  await chooseAndContinue(page, LABELS.ownership.owner);
  await chooseAndContinue(page, LABELS.income[income]);
  await chooseAndContinue(page, LABELS.insulation[insulation]);
  await chooseAndContinue(page, LABELS.heating[heating]);
  await expect(page).toHaveURL(/\/check-answers/);
}

/** Tenant path: property -> renter -> consent -> insulation. Ends at /check-answers. */
export async function answerTenant(
  page,
  { property = 'flat', ownership = 'private-renter', consent = 'yes', insulation = 'partial' } = {},
) {
  await chooseAndContinue(page, LABELS.property[property]);
  await chooseAndContinue(page, LABELS.ownership[ownership]);
  await chooseAndContinue(page, LABELS.consent[consent]);
  await chooseAndContinue(page, LABELS.insulation[insulation]);
  await expect(page).toHaveURL(/\/check-answers/);
}

export async function submit(page) {
  await page.getByRole('button', { name: 'Submit and see result' }).click();
  await expect(page).toHaveURL(/\/result/);
}
```

- [ ] **Step 5: Create `e2e/smoke.spec.js`**

```js
import { test, expect } from '@playwright/test';

test('app loads and renders the start page', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { level: 1, name: 'Check if you can get a Green Home Grant' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start now' })).toBeVisible();
  // App focuses <main> on route change (App.jsx) — proves the SPA hydrated.
  await expect(page.locator('#main-content')).toBeFocused();
});
```

- [ ] **Step 6: Run the smoke test (the harness gate)**

Run: `cd wk03/starter && npm run test:e2e -- smoke.spec.js`
Expected: **1 passed**. If the server starts on 5002 instead of 5050 (i.e. `webServer.env` ignored), change the config command to `'VITE_PORT=5050 npm run dev'` and drop the `env` key, then re-run.

- [ ] **Step 7: Narrow Vitest's include so it ignores e2e specs**

In `wk03/starter/vite.config.js`, inside the existing `test: { ... }` block, add:
```js
    include: ['src/**/*.{test,spec}.{js,jsx}'],
```
(No changes to `plugins` or `server`.) Then verify the two runners are disjoint:
Run: `npm run test:run`
Expected: **61 passed** (all existing unit/integration tests; **no** `e2e/*` files attempted).

---

## Task 1: Full-journey outcome tests — `e2e/journeys.spec.js`

**Files:** Create `wk03/starter/e2e/journeys.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';
import { startCheck, answerOwner, answerTenant, submit } from './helpers.js';

const panel = (page, name) => page.getByRole('heading', { level: 1, name, exact: true });

test.describe('owner journeys', () => {
  test('low income -> eligible', async ({ page }) => {
    await startCheck(page);
    await answerOwner(page, { income: 'low', insulation: 'none', heating: 'gas-boiler' });
    await submit(page);
    await expect(panel(page, 'You may be eligible for a Green Home Grant')).toBeVisible();
    await expect(page.getByText('up to £10,000')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'What to do next' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Find an approved installer' })).toBeVisible();
    // Eligible measures list (gas boiler + no insulation -> all three measures).
    await expect(page.getByRole('listitem').filter({ hasText: 'Air source heat pump installation' })).toBeVisible();
  });

  test('mid income -> partial', async ({ page }) => {
    await startCheck(page);
    await answerOwner(page, { income: 'mid' });
    await submit(page);
    await expect(panel(page, 'You may be partially eligible for a Green Home Grant')).toBeVisible();
    await expect(page.getByText('up to £5,000')).toBeVisible();
  });

  test('high income -> ineligible (income too high)', async ({ page }) => {
    await startCheck(page);
    await answerOwner(page, { income: 'high' });
    await submit(page);
    await expect(panel(page, 'You are not eligible for a Green Home Grant')).toBeVisible();
    await expect(page.getByText('above the threshold for this grant')).toBeVisible();
  });

  test('already fully fitted -> ineligible (no measures needed)', async ({ page }) => {
    await startCheck(page);
    await answerOwner(page, { income: 'low', insulation: 'full', heating: 'heat-pump' });
    await submit(page);
    await expect(panel(page, 'You are not eligible for a Green Home Grant')).toBeVisible();
    await expect(page.getByText('already has the insulation and heating measures')).toBeVisible();
  });
});

test.describe('tenant journeys', () => {
  test('private renter with consent -> partial (renter)', async ({ page }) => {
    await startCheck(page);
    await answerTenant(page, { ownership: 'private-renter', consent: 'yes', insulation: 'partial' });
    await submit(page);
    await expect(panel(page, 'You may be partially eligible for a Green Home Grant')).toBeVisible();
    await expect(page.getByText('your landlord needs to apply for this grant on your behalf')).toBeVisible();
    await expect(page.getByText('the following measures may be available')).toBeVisible();
  });

  test('council tenant without consent -> ineligible (no landlord consent)', async ({ page }) => {
    await startCheck(page);
    await answerTenant(page, { ownership: 'council', consent: 'no', insulation: 'none' });
    await submit(page);
    await expect(panel(page, 'You are not eligible for a Green Home Grant')).toBeVisible();
    await expect(page.getByText("do not have your landlord's permission")).toBeVisible();
  });
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- journeys.spec.js` — Expected: **6 passed**. A RED here is a selector/copy mismatch (fix the test against the source) or a real defect (surface it).

---

## Task 2: Navigation & branching — `e2e/navigation.spec.js`

**Files:** Create `wk03/starter/e2e/navigation.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';
import { startCheck, choose, chooseAndContinue, clickContinue, LABELS } from './helpers.js';

test('start now navigates to the first question', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Start now' }).click();
  await expect(page).toHaveURL(/\/property-type/);
  await expect(page.getByRole('heading', { name: 'What type of property do you live in?' })).toBeVisible();
});

test('step indicator is path-aware (owner 5, tenant 4)', async ({ page }) => {
  await startCheck(page);
  await chooseAndContinue(page, LABELS.property.detached);
  // On /ownership now. Owner -> "of 5".
  await choose(page, LABELS.ownership.owner);
  await expect(page.getByText('Step 2 of 5')).toBeVisible();
  // Switch to a renter -> "of 4".
  await choose(page, LABELS.ownership['private-renter']);
  await expect(page.getByText('Step 2 of 4')).toBeVisible();
});

test('back link returns to the previous question with the answer preserved', async ({ page }) => {
  await startCheck(page);
  await chooseAndContinue(page, LABELS.property.terraced); // -> /ownership
  await choose(page, LABELS.ownership.owner);
  await clickContinue(page); // -> /income
  await expect(page).toHaveURL(/\/income/);
  await page.getByRole('link', { name: 'Back' }).click(); // -> /ownership
  await expect(page).toHaveURL(/\/ownership/);
  await expect(page.getByLabel(LABELS.ownership.owner, { exact: true })).toBeChecked();
});

test('renter branches to landlord-consent and skips heating', async ({ page }) => {
  await startCheck(page);
  await chooseAndContinue(page, LABELS.property.flat); // -> /ownership
  await chooseAndContinue(page, LABELS.ownership['private-renter']); // branch -> /landlord-consent
  await expect(page).toHaveURL(/\/landlord-consent/);
  await expect(page.getByRole('heading', { name: /Do you have your landlord's permission/ })).toBeVisible();
  await chooseAndContinue(page, LABELS.consent.yes); // -> /insulation
  await expect(page).toHaveURL(/\/insulation/);
  await chooseAndContinue(page, LABELS.insulation.partial); // tenant insulation -> /check-answers (skips heating)
  await expect(page).toHaveURL(/\/check-answers/);
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- navigation.spec.js` — Expected: **4 passed**.

---

## Task 3: Check-answers + Change round-trip — `e2e/check-answers.spec.js`

**Files:** Create `wk03/starter/e2e/check-answers.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';
import { startCheck, answerOwner, answerTenant, choose, clickContinue, LABELS } from './helpers.js';

const rowKeys = (page) => page.locator('.govuk-summary-list__key');

test('owner sees all five rows with correct values', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, { property: 'detached', income: 'low', insulation: 'none', heating: 'gas-boiler' });
  await expect(rowKeys(page)).toHaveText([
    'Property type', 'Ownership status', 'Annual household income', 'Current insulation', 'Current heating system',
  ]);
  const list = page.locator('.govuk-summary-list');
  await expect(list).toContainText('Detached house');
  await expect(list).toContainText('I own my home');
  await expect(list).toContainText('Under £31,000');
  await expect(list).toContainText('No insulation');
  await expect(list).toContainText('Gas boiler');
});

test('tenant sees four rows (no income/heating)', async ({ page }) => {
  await startCheck(page);
  await answerTenant(page, { ownership: 'private-renter', consent: 'yes', insulation: 'partial' });
  await expect(rowKeys(page)).toHaveText([
    'Property type', 'Ownership status', "Landlord's permission", 'Current insulation',
  ]);
  // Summary value uses the SHORT label.
  await expect(page.locator('.govuk-summary-list')).toContainText('Some insulation');
});

test('Change link round-trips and updates the summary', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, { income: 'low' });
  // Change income.
  await page.getByRole('link', { name: /Change.*annual household income/i }).click();
  await expect(page).toHaveURL(/\/income\?from=check-answers/);
  await expect(page.getByLabel(LABELS.income.low, { exact: true })).toBeChecked(); // pre-checked from context
  await choose(page, LABELS.income.mid);
  await clickContinue(page); // ?from=check-answers override -> back to check-answers
  await expect(page).toHaveURL(/\/check-answers/);
  await expect(page.locator('.govuk-summary-list')).toContainText('£31,000 to £60,000');
});

test('Submit goes to the result page', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, {});
  await page.getByRole('button', { name: 'Submit and see result' }).click();
  await expect(page).toHaveURL(/\/result/);
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- check-answers.spec.js` — Expected: **4 passed**. (The Change-link accessible name is `Change <hidden text>`, e.g. `Change annual household income` — the regex tolerates the visually-hidden suffix.)

---

## Task 4: Validation (GOV.UK error pattern) — `e2e/validation.spec.js`

**Files:** Create `wk03/starter/e2e/validation.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';

test('empty submission shows the GOV.UK error pattern', async ({ page }) => {
  await page.goto('/property-type');
  await page.getByRole('button', { name: 'Continue' }).click();

  const summary = page.locator('.govuk-error-summary');
  await expect(summary).toBeVisible();
  await expect(summary.getByRole('heading', { name: 'There is a problem' })).toBeVisible();
  await expect(summary).toBeFocused(); // ErrorSummary auto-focuses its container on mount

  const link = summary.getByRole('link', { name: 'Select the type of property you live in' });
  await expect(link).toHaveAttribute('href', '#propertyType-1');

  await expect(page.locator('.govuk-error-message')).toContainText('Select the type of property you live in');
  await expect(page).toHaveTitle(/^Error: /);

  // Activating the summary link moves the fragment to the first radio.
  await link.click();
  await expect(page).toHaveURL(/#propertyType-1$/);

  // Stays on the same question (no navigation past validation).
  await expect(page.getByRole('heading', { name: 'What type of property do you live in?' })).toBeVisible();
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- validation.spec.js` — Expected: **1 passed**.

---

## Task 5: Deep-link guards — `e2e/guards.spec.js`

**Files:** Create `wk03/starter/e2e/guards.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';

test('deep-linking check-answers with no answers redirects to the first question', async ({ page }) => {
  await page.goto('/check-answers');
  await expect(page).toHaveURL(/\/property-type/);
  await expect(page.getByRole('heading', { name: 'What type of property do you live in?' })).toBeVisible();
});

test('deep-linking the result with no answers redirects to the start page', async ({ page }) => {
  await page.goto('/result');
  await expect(page.getByRole('heading', { level: 1, name: 'Check if you can get a Green Home Grant' })).toBeVisible();
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- guards.spec.js` — Expected: **2 passed**. (Playwright gives each test a fresh context, so `localStorage` is empty here — the guards fire.)

---

## Task 6: Save-and-return across reload — `e2e/save-and-return.spec.js`

**Files:** Create `wk03/starter/e2e/save-and-return.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';
import { startCheck, chooseAndContinue, LABELS } from './helpers.js';

const STORAGE_KEY = 'ghg:answers:v1';
const readStore = (page) => page.evaluate((k) => window.localStorage.getItem(k), STORAGE_KEY);

test('answers persist across a full page reload and offer resume', async ({ page }) => {
  await startCheck(page);
  await chooseAndContinue(page, LABELS.property.detached); // saves propertyType, now on /ownership
  expect(await readStore(page)).toContain('detached');

  await page.reload(); // FormProvider re-initialises from localStorage — the jsdom tests cannot do this
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'You have a partially completed check' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Continue your check' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start again' })).toBeVisible();

  await page.getByRole('button', { name: 'Continue your check' }).click();
  await expect(page).toHaveURL(/\/property-type/);
});

test('Start again clears the saved answers', async ({ page }) => {
  await startCheck(page);
  await chooseAndContinue(page, LABELS.property.detached);
  await page.goto('/');

  await page.getByRole('button', { name: 'Start again' }).click();
  await expect(page.getByRole('heading', { name: 'You have a partially completed check' })).toBeHidden();

  // resetAnswers clears then re-writes the all-empty blob; assert no real answer remains.
  const parsed = JSON.parse(await readStore(page));
  expect(parsed.propertyType).toBe('');
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- save-and-return.spec.js` — Expected: **2 passed**.

---

## Task 7: PDF download — `e2e/pdf-download.spec.js`

**Files:** Create `wk03/starter/e2e/pdf-download.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';
import { statSync } from 'node:fs';
import { startCheck, answerOwner, submit } from './helpers.js';

test('downloads a non-empty PDF with the expected filename', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, { income: 'low' });
  await submit(page);
  await expect(page.getByRole('heading', { level: 1, name: 'You may be eligible for a Green Home Grant' })).toBeVisible();

  // Arm the download listener BEFORE the click (the handler lazy-imports jsPDF, so there is an async tick).
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download your result (PDF)' }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe('green-home-grant-result.pdf');
  const path = await download.path();
  expect(path).toBeTruthy();
  expect(statSync(path).size).toBeGreaterThan(0);
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- pdf-download.spec.js` — Expected: **1 passed**.

---

## Task 8: Accessibility — structural + axe-core — `e2e/accessibility.spec.js`

**Files:** Create `wk03/starter/e2e/accessibility.spec.js`

- [ ] **Step 1: Write the spec**

```js
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { startCheck, answerOwner } from './helpers.js';

const WCAG = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

async function expectNoAxe(page, scope) {
  const results = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  const ids = results.violations.map((v) => `${v.id}×${v.nodes.length}`).join(', ');
  expect(results.violations, `axe WCAG violations on ${scope}: ${ids}`).toEqual([]);
}

test.describe('structural accessibility', () => {
  test('skip link targets main and is focusable', async ({ page }) => {
    await page.goto('/');
    const skip = page.getByRole('link', { name: 'Skip to main content' });
    await skip.focus();
    await expect(skip).toBeFocused();
    await expect(skip).toHaveAttribute('href', '#main-content');
  });

  test('focus moves to <main> on load and on route change', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#main-content')).toBeFocused();
    await page.getByRole('button', { name: 'Start now' }).click();
    await expect(page).toHaveURL(/\/property-type/);
    await expect(page.locator('#main-content')).toBeFocused();
  });

  test('a question can be completed with the keyboard only', async ({ page }) => {
    await page.goto('/property-type');
    await expect(page.locator('#main-content')).toBeFocused();
    await page.keyboard.press('Tab'); // -> Back link
    await expect(page.getByRole('link', { name: 'Back' })).toBeFocused();
    await page.keyboard.press('Tab'); // -> first radio
    const detached = page.getByLabel('Detached house', { exact: true });
    await expect(detached).toBeFocused();
    await page.keyboard.press('Space');
    await expect(detached).toBeChecked();
    await page.keyboard.press('Tab'); // -> Continue (no details block on this page)
    await expect(page.getByRole('button', { name: 'Continue' })).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/ownership/);
  });

  test('layout reflows at 320px with no horizontal scroll', async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 800 });
    await page.goto('/property-type');
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
    );
    expect(overflow, 'horizontal scroll present at 320px').toBe(false);
  });

  test('accessibility statement is reachable from the footer', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('contentinfo').getByRole('link', { name: 'Accessibility statement' }).click();
    await expect(page).toHaveURL(/\/accessibility-statement/);
    await expect(
      page.getByRole('heading', { level: 1, name: /Accessibility statement for the Green Home Grant/ }),
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: 'How accessible this website is' })).toBeVisible();
  });
});

test.describe('axe WCAG 2.2 AA scans', () => {
  test('start page', async ({ page }) => { await page.goto('/'); await expectNoAxe(page, 'start'); });
  test('question page', async ({ page }) => { await page.goto('/property-type'); await expectNoAxe(page, 'property-type'); });
  test('validation error state', async ({ page }) => {
    await page.goto('/property-type');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.locator('.govuk-error-summary')).toBeVisible();
    await expectNoAxe(page, 'error-state');
  });
  test('check-answers', async ({ page }) => { await startCheck(page); await answerOwner(page, {}); await expectNoAxe(page, 'check-answers'); });
  test('eligible result', async ({ page }) => { await startCheck(page); await answerOwner(page, { income: 'low' }); await page.getByRole('button', { name: 'Submit and see result' }).click(); await expect(page).toHaveURL(/\/result/); await expectNoAxe(page, 'result-eligible'); });
  test('ineligible result', async ({ page }) => { await startCheck(page); await answerOwner(page, { income: 'high' }); await page.getByRole('button', { name: 'Submit and see result' }).click(); await expect(page).toHaveURL(/\/result/); await expectNoAxe(page, 'result-ineligible'); });
  test('accessibility statement', async ({ page }) => { await page.goto('/accessibility-statement'); await expectNoAxe(page, 'a11y-statement'); });
});
```

- [ ] **Step 2: Run** — `npm run test:e2e -- accessibility.spec.js` — Expected: **all passed**.

- [ ] **Step 3: Triage any axe failure per the spec's rule.** Likely candidates and the decision:
  - `aria-prohibited-attr` / `aria-allowed-attr` on the `<p class="app-step-indicator" aria-label="…">` (ProgressIndicator). The `aria-label` is redundant with the visible text. If it fires: **scope it narrowly** — `new AxeBuilder({ page }).withTags(WCAG).exclude('.app-step-indicator')` on the affected page(s) **with a comment** explaining it's a benign redundant label; surface to the user as a candidate 1-line app cleanup (remove the redundant `aria-label`) for a follow-up — do not change app source in this stretch.
  - `color-contrast` on `govuk-panel--not-eligible` (ineligible result). If it fires, it's a **genuine** WCAG finding: surface to the user with the measured ratio before deciding to fix vs scope.
  - Anything else: investigate; fix the test if it's a selector/timing issue, surface if it's a real defect.

---

## Task 9: e2e/README.md

**Files:** Create `wk03/starter/e2e/README.md`

- [ ] **Step 1: Write it**

````markdown
# End-to-end tests (Playwright)

Browser-driven E2E suite covering the full Green Home Grant user journey.

## Run

```bash
npm install            # if not already done
npx playwright install chromium   # one-time, if the browser is not cached
npm run test:e2e       # runs the suite (Playwright starts the dev server itself)
npm run test:e2e:report # open the last HTML report
```

Playwright starts `npm run dev` on port **5050** and points the browser at
`http://<hostname>:5050` (the lab hostname, per the project CLAUDE.md — not
`localhost`). Override with `E2E_BASE_URL`, `E2E_HOST`, or `E2E_PORT`.

## Layout

- `playwright.config.js` (project root) — chromium project, `webServer`, `baseURL`.
- `e2e/helpers.js` — reusable step helpers + answer-set label constants.
- `e2e/*.spec.js` — one file per concern (journeys, navigation, check-answers,
  validation, guards, save-and-return, PDF download, accessibility + axe).

`npm test` / `npm run test:run` remain the Vitest unit/integration entry points;
they do not run these e2e specs (Vitest `include` is scoped to `src/**`).
````

---

## Task 10: Full-suite run + verification gates

- [ ] **Step 1: Run the whole suite** — `cd wk03/starter && npm run test:e2e` — Expected: **all specs pass** (≈ 6 + 4 + 4 + 1 + 2 + 2 + 1 + (5 structural + 7 axe) + 1 smoke ≈ 33 tests). Fix any flake using web-first assertions (no `waitForTimeout`).
- [ ] **Step 2: Vitest unchanged** — `npm run test:run` — Expected: **61 passed**.
- [ ] **Step 3: Build clean** — `npm run build` — Expected: exit 0.
- [ ] **Step 4: Confirm artifact dirs are git-ignored** — `git status --short` shows **no** `test-results/`, `playwright-report/`, or `.playwright/` (the repo `.gitignore` already covers them). Confirm `e2e/`, `playwright.config.js`, and the `package.json`/`vite.config.js` edits ARE shown as changes to stage.

---

## Task 11: Adversarial review (Workflow), then commit + PR

- [ ] **Step 1: Adversarial review.** Run a Workflow that fans out reviewers over the staged suite + app sources: (a) coverage-completeness vs the design spec's matrix; (b) flakiness/anti-patterns (manual sleeps, race-prone assertions, over-broad locators, missing `await`); (c) selector/copy correctness vs the page sources; (d) acceptance-criterion mapping; (e) axe-scoping justification. Dedupe, verify each finding, fix, re-run the affected specs.
- [ ] **Step 2: Add the AI_LOG entry (`Prompt 19`)** to `wk03/starter/AI_LOG.md` documenting the implementation, the verification results (exact pass counts), and any axe triage decision.
- [ ] **Step 3: Stage only the relevant files** — `git add wk03/starter/playwright.config.js wk03/starter/e2e wk03/starter/package.json wk03/starter/package-lock.json wk03/starter/vite.config.js wk03/starter/AI_LOG.md` — review `git status` first.
- [ ] **Step 4: Commit** with the `[Agent-Jack]` format + body + `Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>`.
- [ ] **Step 5: `git pull --rebase` then push**; open a PR (`gh pr create`) with a summary, the verification evidence, and the body footer.

---

## Self-review (against the design spec)

- **Spec coverage:** §6.1 → Task 1; §6.2 → Task 2; §6.3 → Task 3; §6.4 → Task 4; §6.5 → Task 5; §6.6 → Task 6; §6.7 → Task 7; §6.8 (structural + axe) → Task 8; layout/scripts/README/config (§5) → Tasks 0 + 9; verification gates (§9) → Task 10; repo workflow → Task 11. No gaps.
- **Placeholder scan:** none — every test step contains runnable code and an exact run command + expected count.
- **Type/name consistency:** helper names (`startCheck`, `answerOwner`, `answerTenant`, `submit`, `choose`, `chooseAndContinue`, `clickContinue`, `LABELS`) defined in Task 0 are used identically in Tasks 1–8. Storage key `ghg:answers:v1`, PDF filename `green-home-grant-result.pdf`, and the short-vs-long label rule are applied consistently.
- **Known risks flagged inline:** `webServer.env` fallback (Task 0 Step 6); axe triage (Task 8 Step 3).

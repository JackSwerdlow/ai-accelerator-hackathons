import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { startCheck, answerOwner, answerTenant, submit, backLink } from './helpers.js';

const WCAG = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'];

async function expectNoAxe(page, scope) {
  // Under reducedMotion (config) the page-enter fade is already disabled, so axe
  // sees settled colours. This wait is a belt-and-suspenders guard for any other
  // in-flight animation so a scan never samples a mid-transition frame.
  await page.evaluate(() => Promise.all(document.getAnimations().map((a) => a.finished.catch(() => {}))));
  const results = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  const detail = results.violations
    .map((v) => `${v.id} [${v.impact}] (${v.nodes.length}): ${v.nodes.map((n) => n.target.join(' ')).join(' | ')}`)
    .join('\n');
  expect(results.violations, `axe WCAG violations on ${scope}:\n${detail}`).toEqual([]);
}

test.describe('structural accessibility', () => {
  test('skip link is keyboard-operable and moves focus to <main>', async ({ page }) => {
    await page.goto('/');
    // The app auto-focuses <main> on load, so focus the link directly to observe
    // its effect (this also moves focus OFF <main>, making the assertion below
    // meaningful rather than trivially true).
    const skip = page.getByRole('link', { name: 'Skip to main content' });
    await skip.focus();
    await expect(skip).toBeFocused();
    await expect(skip).toHaveAttribute('href', '#main-content');
    await skip.press('Enter'); // activate by keyboard
    await expect(page).toHaveURL(/#main-content$/);
    await expect(page.locator('#main-content')).toBeFocused(); // bypasses the chrome
  });

  test('focus moves to <main> on load and on route change', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('#main-content')).toBeFocused();
    await page.getByRole('button', { name: 'Start now' }).click();
    await expect(page).toHaveURL(/\/property-type/);
    await expect(page.locator('#main-content')).toBeFocused();
  });

  test('a question is operable with the keyboard only (Tab + arrow keys + Enter)', async ({ page }) => {
    await page.goto('/property-type');
    await expect(page.locator('#main-content')).toBeFocused();
    await page.keyboard.press('Tab'); // -> Back link
    await expect(backLink(page)).toBeFocused();
    await page.keyboard.press('Tab'); // -> into the radio group (first radio)
    await expect(page.getByLabel('Detached house', { exact: true })).toBeFocused();
    // Arrow key moves focus AND selection within the radio group.
    await page.keyboard.press('ArrowDown');
    await expect(page.getByLabel('Semi-detached house', { exact: true })).toBeChecked();
    await page.keyboard.press('Tab'); // -> Continue (no <details> on this page)
    await expect(page.getByRole('button', { name: 'Continue' })).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/ownership/);
  });

  test('help disclosure toggles open and closed with the keyboard', async ({ page }) => {
    await page.goto('/income'); // Income/Insulation/Heating/LandlordConsent carry a <details> help block
    const details = page.locator('.govuk-details');
    const summary = page.locator('.govuk-details__summary');
    await expect(details).toHaveJSProperty('open', false);
    await summary.focus();
    await expect(summary).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(details).toHaveJSProperty('open', true);
    await page.keyboard.press('Enter');
    await expect(details).toHaveJSProperty('open', false);
  });

  test('error-summary link is keyboard-operable and moves focus to the field', async ({ page }) => {
    await page.goto('/property-type');
    await page.getByRole('button', { name: 'Continue' }).click();
    const summary = page.locator('.govuk-error-summary');
    await expect(summary).toBeFocused(); // auto-focused on mount
    await page.keyboard.press('Tab'); // -> the single link inside the summary
    const link = summary.getByRole('link');
    await expect(link).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/#propertyType-1$/);
  });

  const REFLOW_PAGES = [
    ['property-type', async (page) => { await page.goto('/property-type'); }],
    ['check-answers', async (page) => { await startCheck(page); await answerOwner(page, {}); }],
    ['eligible result', async (page) => { await startCheck(page); await answerOwner(page, { income: 'low' }); await submit(page); }],
    ['accessibility statement', async (page) => { await page.goto('/accessibility-statement'); }],
  ];
  for (const [label, go] of REFLOW_PAGES) {
    test(`layout reflows at 320px with no horizontal scroll: ${label}`, async ({ page }) => {
      await page.setViewportSize({ width: 320, height: 800 });
      await go(page);
      await expect
        .poll(() =>
          page.evaluate(
            () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
          ),
        )
        .toBe(true);
    });
  }

  test('accessibility statement is reachable from the footer and Back returns', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('contentinfo').getByRole('link', { name: 'Accessibility statement' }).click();
    await expect(page).toHaveURL(/\/accessibility-statement/);
    await expect(
      page.getByRole('heading', { level: 1, name: /Accessibility statement for the Green Home Grant/ }),
    ).toBeVisible();
    await expect(page.getByRole('heading', { name: 'How accessible this website is' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Enforcement procedure' })).toBeVisible();
    // Back returns to the start page.
    await backLink(page).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(
      page.getByRole('heading', { level: 1, name: 'Check if you can get a Green Home Grant' }),
    ).toBeVisible();
  });
});

test.describe('axe WCAG 2.2 AA scans', () => {
  test('start page', async ({ page }) => {
    await page.goto('/');
    await expectNoAxe(page, 'start');
  });

  test('question page (no help disclosure)', async ({ page }) => {
    await page.goto('/property-type');
    await expectNoAxe(page, 'property-type');
  });

  test('question page with help disclosure (closed)', async ({ page }) => {
    await page.goto('/income'); // has hint + aria-describedby + <details> help
    await expectNoAxe(page, 'income (details closed)');
  });

  test('question page with help disclosure (open)', async ({ page }) => {
    await page.goto('/income');
    await page.locator('.govuk-details__summary').click();
    await expect(page.locator('.govuk-details')).toHaveJSProperty('open', true);
    await expectNoAxe(page, 'income (details open)');
  });

  test('tenant-only landlord-consent question', async ({ page }) => {
    await page.goto('/landlord-consent');
    await expectNoAxe(page, 'landlord-consent');
  });

  test('validation error state', async ({ page }) => {
    await page.goto('/property-type');
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.locator('.govuk-error-summary')).toBeVisible();
    await expectNoAxe(page, 'error-state');
  });

  test('check-answers (owner)', async ({ page }) => {
    await startCheck(page);
    await answerOwner(page, {});
    await expectNoAxe(page, 'check-answers (owner)');
  });

  test('check-answers (tenant)', async ({ page }) => {
    await startCheck(page);
    await answerTenant(page, {});
    await expectNoAxe(page, 'check-answers (tenant)');
  });

  // Every one of the six result variants renders distinct copy/links/panel.
  const RESULT_VARIANTS = [
    ['eligible (owner, low income)', (page) => answerOwner(page, { income: 'low' })],
    ['partial (owner, mid income)', (page) => answerOwner(page, { income: 'mid' })],
    ['ineligible (owner, high income)', (page) => answerOwner(page, { income: 'high' })],
    ['ineligible (owner, fully fitted)', (page) => answerOwner(page, { income: 'low', insulation: 'full', heating: 'heat-pump' })],
    ['partial (private renter, consent)', (page) => answerTenant(page, { consent: 'yes', insulation: 'partial' })],
    ['ineligible (council tenant, no consent)', (page) => answerTenant(page, { ownership: 'council', consent: 'no', insulation: 'none' })],
  ];
  for (const [label, fill] of RESULT_VARIANTS) {
    test(`result: ${label}`, async ({ page }) => {
      await startCheck(page);
      await fill(page);
      await submit(page);
      await expectNoAxe(page, `result: ${label}`);
    });
  }

  test('accessibility statement', async ({ page }) => {
    await page.goto('/accessibility-statement');
    await expectNoAxe(page, 'a11y-statement');
  });
});

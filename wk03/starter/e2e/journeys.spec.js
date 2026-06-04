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
    // Detached + no insulation + gas boiler -> all three measures listed.
    for (const measure of ['Loft insulation', 'Internal wall insulation', 'Air source heat pump installation']) {
      await expect(page.getByRole('listitem').filter({ hasText: measure })).toBeVisible();
    }
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
    await expect(
      page.getByText('your landlord needs to apply for this grant on your behalf'),
    ).toBeVisible();
    await expect(page.getByText('the following measures may be available')).toBeVisible();
    // Flat + partial insulation -> indicative list includes wall insulation (loft excluded for flats).
    await expect(
      page.getByRole('listitem').filter({ hasText: 'Internal wall insulation' }),
    ).toBeVisible();
  });

  test('council tenant without consent -> ineligible (no landlord consent)', async ({ page }) => {
    await startCheck(page);
    await answerTenant(page, { ownership: 'council', consent: 'no', insulation: 'none' });
    await submit(page);
    await expect(panel(page, 'You are not eligible for a Green Home Grant')).toBeVisible();
    await expect(page.getByText("do not have your landlord's permission")).toBeVisible();
  });
});

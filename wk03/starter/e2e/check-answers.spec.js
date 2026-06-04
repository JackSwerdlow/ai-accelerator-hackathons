import { test, expect } from '@playwright/test';
import { startCheck, answerOwner, answerTenant, choose, clickContinue, LABELS } from './helpers.js';

const rowKeys = (page) => page.locator('.govuk-summary-list__key');

test('owner sees all five rows with correct values', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, {
    property: 'detached',
    income: 'low',
    insulation: 'none',
    heating: 'gas-boiler',
  });
  await expect(rowKeys(page)).toHaveText([
    'Property type',
    'Ownership status',
    'Annual household income',
    'Current insulation',
    'Current heating system',
  ]);
  const list = page.locator('.govuk-summary-list');
  await expect(list).toContainText('Detached house');
  await expect(list).toContainText('I own my home');
  await expect(list).toContainText('Under £31,000');
  await expect(list).toContainText('No insulation');
  await expect(list).toContainText('Gas boiler');
  // Every row has its own Change link (README: "Each answer ... has a Change link").
  await expect(list.getByRole('link', { name: /^Change/ })).toHaveCount(5);
});

test('tenant sees four rows (no income/heating)', async ({ page }) => {
  await startCheck(page);
  await answerTenant(page, { ownership: 'private-renter', consent: 'yes', insulation: 'partial' });
  await expect(rowKeys(page)).toHaveText([
    'Property type',
    'Ownership status',
    "Landlord's permission",
    'Current insulation',
  ]);
  // Summary value uses the SHORT label.
  await expect(page.locator('.govuk-summary-list')).toContainText('Some insulation');
  await expect(page.locator('.govuk-summary-list').getByRole('link', { name: /^Change/ })).toHaveCount(4);
});

test('Change link round-trips and updates the summary', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, { income: 'low' });
  // Change income.
  await page.getByRole('link', { name: /Change.*annual household income/i }).click();
  await expect(page).toHaveURL(/\/income\?from=check-answers/);
  await expect(page.getByLabel(LABELS.income.low, { exact: true })).toBeChecked(); // pre-checked
  await choose(page, LABELS.income.mid);
  await clickContinue(page); // ?from=check-answers override -> back to check-answers
  await expect(page).toHaveURL(/\/check-answers/);
  await expect(page.locator('.govuk-summary-list')).toContainText('£31,000 to £60,000');

  // Round-trip a second, different question page to cover its ?from override too.
  await page.getByRole('link', { name: /Change.*property type/i }).click();
  await expect(page).toHaveURL(/\/property-type\?from=check-answers/);
  await expect(page.getByLabel(LABELS.property.detached, { exact: true })).toBeChecked();
  await choose(page, LABELS.property.terraced);
  await clickContinue(page);
  await expect(page).toHaveURL(/\/check-answers/);
  await expect(page.locator('.govuk-summary-list')).toContainText('Terraced house');
});

test('Submit goes to the result page', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, {});
  await page.getByRole('button', { name: 'Submit and see result' }).click();
  await expect(page).toHaveURL(/\/result/);
});

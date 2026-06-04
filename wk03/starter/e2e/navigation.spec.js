import { test, expect } from '@playwright/test';
import { startCheck, choose, chooseAndContinue, clickContinue, backLink, LABELS } from './helpers.js';

test('start now navigates to the first question', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Start now' }).click();
  await expect(page).toHaveURL(/\/property-type/);
  await expect(
    page.getByRole('heading', { name: 'What type of property do you live in?' }),
  ).toBeVisible();
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
  await backLink(page).click(); // -> /ownership
  await expect(page).toHaveURL(/\/ownership/);
  await expect(page.getByLabel(LABELS.ownership.owner, { exact: true })).toBeChecked();
});

test('renter branches to landlord-consent and skips heating', async ({ page }) => {
  await startCheck(page);
  await chooseAndContinue(page, LABELS.property.flat); // -> /ownership
  await chooseAndContinue(page, LABELS.ownership['private-renter']); // branch -> /landlord-consent
  await expect(page).toHaveURL(/\/landlord-consent/);
  await expect(
    page.getByRole('heading', { name: /Do you have your landlord's permission/ }),
  ).toBeVisible();
  await chooseAndContinue(page, LABELS.consent.yes); // -> /insulation
  await expect(page).toHaveURL(/\/insulation/);
  await chooseAndContinue(page, LABELS.insulation.partial); // tenant insulation -> /check-answers
  await expect(page).toHaveURL(/\/check-answers/);
});

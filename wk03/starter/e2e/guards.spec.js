import { test, expect } from '@playwright/test';

test('deep-linking check-answers with no answers redirects to the first question', async ({ page }) => {
  await page.goto('/check-answers');
  await expect(page).toHaveURL(/\/property-type/);
  await expect(
    page.getByRole('heading', { name: 'What type of property do you live in?' }),
  ).toBeVisible();
});

test('deep-linking the result with no answers redirects to the start page', async ({ page }) => {
  await page.goto('/result');
  await expect(
    page.getByRole('heading', { level: 1, name: 'Check if you can get a Green Home Grant' }),
  ).toBeVisible();
});

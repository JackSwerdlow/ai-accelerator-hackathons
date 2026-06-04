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

  await expect(page.locator('.govuk-error-message')).toContainText(
    'Select the type of property you live in',
  );
  await expect(page).toHaveTitle(/^Error: /);

  // Activating the summary link moves the fragment to the first radio.
  await link.click();
  await expect(page).toHaveURL(/#propertyType-1$/);

  // Stays on the same question (no navigation past validation).
  await expect(
    page.getByRole('heading', { name: 'What type of property do you live in?' }),
  ).toBeVisible();
});

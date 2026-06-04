import { test, expect } from '@playwright/test';

test('app loads and renders the start page', async ({ page }) => {
  await page.goto('/');
  await expect(
    page.getByRole('heading', { level: 1, name: 'Check if you can get a Green Home Grant' }),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: 'Start now' })).toBeVisible();
  // App focuses <main> on route change (App.jsx) — proves the SPA hydrated.
  await expect(page.locator('#main-content')).toBeFocused();
});

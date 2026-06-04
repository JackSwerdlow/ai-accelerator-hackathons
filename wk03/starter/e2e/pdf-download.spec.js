import { test, expect } from '@playwright/test';
import { statSync } from 'node:fs';
import { startCheck, answerOwner, submit } from './helpers.js';

test('downloads a non-empty PDF with the expected filename', async ({ page }) => {
  await startCheck(page);
  await answerOwner(page, { income: 'low' });
  await submit(page);
  await expect(
    page.getByRole('heading', { level: 1, name: 'You may be eligible for a Green Home Grant' }),
  ).toBeVisible();

  // Arm the download listener BEFORE the click (the handler lazy-imports jsPDF -> async tick).
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download your result (PDF)' }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe('green-home-grant-result.pdf');
  const path = await download.path();
  expect(path).toBeTruthy();
  expect(statSync(path).size).toBeGreaterThan(0);
});

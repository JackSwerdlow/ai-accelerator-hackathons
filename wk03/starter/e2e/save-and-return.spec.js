import { test, expect } from '@playwright/test';
import { startCheck, chooseAndContinue, LABELS } from './helpers.js';

const STORAGE_KEY = 'ghg:answers:v1';
const readStore = (page) => page.evaluate((k) => window.localStorage.getItem(k), STORAGE_KEY);

test('answers persist across a full page reload and offer resume', async ({ page }) => {
  await startCheck(page);
  await chooseAndContinue(page, LABELS.property.detached); // saves propertyType, now on /ownership
  // Poll: the write is a passive useEffect; don't race it with a one-shot read.
  await expect.poll(() => readStore(page)).toContain('detached');

  await page.reload(); // FormProvider re-initialises from localStorage — jsdom cannot do this
  await page.goto('/');

  await expect(
    page.getByRole('heading', { name: 'You have a partially completed check' }),
  ).toBeVisible();
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
  await expect(
    page.getByRole('heading', { name: 'You have a partially completed check' }),
  ).toBeHidden();

  // resetAnswers removes the key then re-writes the all-empty blob via a passive
  // effect. Poll so we don't read in the transient post-removeItem/pre-rewrite
  // window (where readStore is null and JSON.parse(null) would throw).
  await expect
    .poll(async () => {
      const raw = await readStore(page);
      return raw ? JSON.parse(raw).propertyType : undefined;
    })
    .toBe('');
});

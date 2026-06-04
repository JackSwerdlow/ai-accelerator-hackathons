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

/**
 * The GOV.UK "Back" link. Matched by class, not role+name: its accessible name
 * is "‹Back" (a CSS ::before chevron), and a name match for "Back" also catches
 * the phase-banner "feedback" link (substring). One back link renders per page.
 */
export function backLink(page) {
  return page.locator('.govuk-back-link');
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

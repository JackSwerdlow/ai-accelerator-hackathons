/**
 * Pure eligibility rules for the Green Home Grant checker.
 * Maps an answers object to an outcome, reason code, and recommended measures.
 * No side effects; safe to call with missing or unknown keys.
 */

const RENTER_OWNERSHIPS = new Set(['private-renter', 'housing-association', 'council']);

/**
 * Is this ownership value one of the renter/tenant tenures?
 * Shared by the eligibility rules and the question-flow routing so both
 * agree on who travels the tenant path (content plan §11).
 *
 * @param {string} [ownership] - The ownership answer.
 * @returns {boolean}
 */
export function isTenant(ownership) {
  return RENTER_OWNERSHIPS.has(ownership);
}

/**
 * Evaluate eligibility for a set of answers.
 *
 * Tenure is checked first: tenants cannot apply independently, so their
 * outcome turns on landlord consent, not the income means-test. That makes
 * the high-income exclusion an owner-only gate (content plan §11).
 *
 * Rules are applied in priority order (first match wins):
 *   1. Tenant + landlord consent "no"  -> ineligible / no-landlord-consent
 *   2. Tenant (consent "yes"/"not-sure") -> partial / renter
 *   3. Owner + income "high"           -> ineligible / income-too-high
 *   4. Owner + full insulation AND heat pump -> ineligible / no-measures-needed
 *   5. Owner + mid income              -> partial / owner-mid-income
 *   6. Owner + low income              -> eligible / owner-low-income
 *   Default -> ineligible / default
 *
 * Measures are computed independently of outcome.
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {{ outcome: string, reason: string, measures: string[] }}
 */
export function eligibility(answers) {
  const a = answers ?? {};
  const measures = computeMeasures(a);

  if (isTenant(a.ownership)) {
    if (a.landlordConsent === 'no') {
      return { outcome: 'ineligible', reason: 'no-landlord-consent', measures };
    }
    return { outcome: 'partial', reason: 'renter', measures };
  }

  if (a.incomeBand === 'high') {
    return { outcome: 'ineligible', reason: 'income-too-high', measures };
  }

  if (a.insulation === 'full' && a.heating === 'heat-pump') {
    return { outcome: 'ineligible', reason: 'no-measures-needed', measures };
  }

  if (a.ownership === 'owner' && a.incomeBand === 'mid') {
    return { outcome: 'partial', reason: 'owner-mid-income', measures };
  }

  if (a.ownership === 'owner' && a.incomeBand === 'low') {
    return { outcome: 'eligible', reason: 'owner-low-income', measures };
  }

  return { outcome: 'ineligible', reason: 'default', measures };
}

function computeMeasures(a) {
  const measures = [];
  if (a.insulation !== 'full' && a.propertyType !== 'flat') {
    measures.push('Loft insulation');
  }
  if (a.insulation !== 'full') {
    measures.push('Internal wall insulation');
  }
  if (a.heating !== 'heat-pump') {
    measures.push('Air source heat pump installation');
  }
  return measures;
}

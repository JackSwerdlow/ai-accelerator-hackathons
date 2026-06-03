/**
 * Pure eligibility rules for the Green Home Grant checker.
 * Maps an answers object to an outcome, reason code, and recommended measures.
 * No side effects; safe to call with missing or unknown keys.
 */

const RENTER_OWNERSHIPS = new Set(['private-renter', 'housing-association', 'council']);

/**
 * Evaluate eligibility for a set of answers.
 *
 * Rules are applied in priority order (first match wins):
 *   1. Income band "high" -> ineligible / income-too-high
 *   2. Full insulation AND heat pump -> ineligible / no-measures-needed
 *   3. Renter ownership -> partial / renter
 *   4. Owner + mid income -> partial / owner-mid-income
 *   5. Owner + low income -> eligible / owner-low-income
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

  if (a.incomeBand === 'high') {
    return { outcome: 'ineligible', reason: 'income-too-high', measures };
  }

  if (a.insulation === 'full' && a.heating === 'heat-pump') {
    return { outcome: 'ineligible', reason: 'no-measures-needed', measures };
  }

  if (RENTER_OWNERSHIPS.has(a.ownership)) {
    return { outcome: 'partial', reason: 'renter', measures };
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

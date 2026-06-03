/**
 * Display-label helpers for the Green Home Grant checker.
 * Maps internal answer values to user-facing British English strings,
 * and exposes the recommended-measures list for a set of answers.
 */
import { eligibility } from './eligibility';

const LABELS = {
  propertyType: {
    'detached': 'Detached house',
    'semi-detached': 'Semi-detached house',
    'terraced': 'Terraced house',
    'flat': 'Flat or apartment',
    'bungalow': 'Bungalow',
  },
  ownership: {
    'owner': 'I own my home',
    'private-renter': 'I rent from a private landlord',
    'housing-association': 'I rent from a housing association',
    'council': 'I rent from a council or local authority',
  },
  incomeBand: {
    'low': 'Under £31,000',
    'mid': '£31,000 to £60,000',
    'high': 'Over £60,000',
  },
  insulation: {
    'none': 'No insulation',
    'partial': 'Some insulation',
    'full': 'Full insulation',
  },
  heating: {
    'gas-boiler': 'Gas boiler',
    'oil-boiler': 'Oil boiler',
    'electric-storage': 'Electric storage heaters',
    'heat-pump': 'Heat pump',
    'other': 'Other',
  },
};

/**
 * Return the human-readable label for a (field, value) pair.
 * Returns "" for empty or unknown values so partially-filled UI
 * rows can render blank rather than crashing.
 *
 * @param {string} field - One of the answer fields (e.g. "propertyType").
 * @param {string} value - The internal answer value.
 * @returns {string} The display label, or "" if unknown.
 */
export function labelFor(field, value) {
  if (!value) return '';
  const fieldMap = LABELS[field];
  if (!fieldMap) return '';
  return fieldMap[value] ?? '';
}

/**
 * Return the recommended-measures list for a set of answers.
 * Delegates to eligibility() so the rules stay in a single source of truth.
 *
 * @param {object} answers - The current answers from the form.
 * @returns {string[]} Display labels for each recommended measure.
 */
export function measuresFor(answers) {
  return eligibility(answers).measures;
}

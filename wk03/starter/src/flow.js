/**
 * Question-flow definition for the two eligibility pathways (content plan §11).
 * Everyone answers a shared prefix (property type, ownership); after that the
 * journey branches by tenure — owners answer income/insulation/heating, tenants
 * answer landlord consent/insulation. Centralising the ordered field+route
 * lists here keeps the check-answers guard, the result guard, and the progress
 * indicator in agreement about which path the user is on and how long it is.
 */
import { isTenant } from './eligibility';

// Asked of everyone, in order.
const SHARED_PREFIX = [
  { field: 'propertyType', route: '/property-type' },
  { field: 'ownership', route: '/ownership' },
];

// Owner-only tail.
const OWNER_TAIL = [
  { field: 'incomeBand', route: '/income' },
  { field: 'insulation', route: '/insulation' },
  { field: 'heating', route: '/heating' },
];

// Tenant-only tail.
const TENANT_TAIL = [
  { field: 'landlordConsent', route: '/landlord-consent' },
  { field: 'insulation', route: '/insulation' },
];

/**
 * Ordered [{ field, route }] steps for the path implied by the answers.
 * Before ownership is chosen the owner path is assumed (the longer path), so
 * the shared prefix still renders a sensible step count.
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {{ field: string, route: string }[]}
 */
export function flowSteps(answers) {
  const a = answers ?? {};
  const tail = isTenant(a.ownership) ? TENANT_TAIL : OWNER_TAIL;
  return [...SHARED_PREFIX, ...tail];
}

/**
 * Field names the current path requires an answer for. Consumed by the
 * check-answers and result guards so a tenant is not blocked on owner-only
 * questions (and vice versa).
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {string[]}
 */
export function requiredFields(answers) {
  return flowSteps(answers).map((step) => step.field);
}

/**
 * Total number of question steps in the current path, for "Step X of N".
 * Returned as a function-friendly value so <QuestionPage> can resolve it
 * against live answers (the count drops from 5 to 4 when a tenant is chosen).
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {number}
 */
export function totalSteps(answers) {
  return flowSteps(answers).length;
}

/**
 * Where Continue goes from the Ownership question — the branch point.
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {string} The next route.
 */
export function ownershipNext(answers) {
  return isTenant(answers?.ownership) ? '/landlord-consent' : '/income';
}

/**
 * Where Continue goes from the Insulation question — the paths re-converge
 * here, so owners continue to heating while tenants go straight to the summary.
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {string} The next route.
 */
export function insulationNext(answers) {
  return isTenant(answers?.ownership) ? '/check-answers' : '/heating';
}

/**
 * Where the Back link on the Insulation question points — owners came from
 * income, tenants came from the landlord-consent question.
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {string} The previous route.
 */
export function insulationBack(answers) {
  return isTenant(answers?.ownership) ? '/landlord-consent' : '/income';
}

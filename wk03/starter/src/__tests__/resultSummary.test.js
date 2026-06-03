/**
 * Tests for buildResultSummary() — the pure content model behind the
 * downloadable result PDF. Covers every outcome/reason branch, the
 * path-aware answer rows (owner vs tenant), and the empty-value filter.
 */
import { buildResultSummary } from '../resultSummary';

const OWNER_ELIGIBLE = {
  propertyType: 'detached',
  ownership: 'owner',
  incomeBand: 'low',
  insulation: 'none',
  heating: 'gas-boiler',
};

const TENANT = {
  propertyType: 'flat',
  ownership: 'private-renter',
  landlordConsent: 'yes',
  insulation: 'partial',
};

/** Flatten every bullet across all sections. */
const allBullets = (s) => s.sections.flatMap((sec) => sec.bullets);
/** Flatten every paragraph across all sections. */
const allParagraphs = (s) => s.sections.flatMap((sec) => sec.paragraphs);

describe('buildResultSummary', () => {
  it('carries fixed document metadata regardless of outcome', () => {
    const s = buildResultSummary(OWNER_ELIGIBLE);
    expect(s.documentTitle).toBe('Your Green Home Grant result');
    expect(s.serviceName).toBe('Green Home Grant');
    expect(s.footnote).toMatch(/indicative result/i);
  });

  it('eligible: headline, £10,000 highlight, and measures as bullets', () => {
    const s = buildResultSummary(OWNER_ELIGIBLE);
    expect(s.outcome).toBe('eligible');
    expect(s.headline).toMatch(/may be eligible/i);
    expect(s.highlight).toContain('£10,000');
    expect(allBullets(s)).toContain('Air source heat pump installation');
    expect(s.sections.some((sec) => sec.heading === 'What to do next')).toBe(true);
  });

  it('partial/renter: tenant headline and "subject to a property assessment" measures', () => {
    const s = buildResultSummary(TENANT);
    expect(s.outcome).toBe('partial');
    expect(s.reason).toBe('renter');
    expect(s.headline).toMatch(/partially eligible/i);
    expect(allParagraphs(s).join(' ')).toMatch(/subject to a property assessment/i);
  });

  it('partial/owner-mid-income: £5,000 partial-grant copy', () => {
    const s = buildResultSummary({ ...OWNER_ELIGIBLE, incomeBand: 'mid' });
    expect(s.reason).toBe('owner-mid-income');
    expect(allParagraphs(s).join(' ')).toContain('£5,000');
  });

  it('ineligible/income-too-high: explains the income threshold', () => {
    const s = buildResultSummary({ ...OWNER_ELIGIBLE, incomeBand: 'high' });
    expect(s.outcome).toBe('ineligible');
    expect(s.headline).toMatch(/not eligible/i);
    expect(allParagraphs(s).join(' ')).toMatch(/above the threshold/i);
  });

  it('ineligible/no-landlord-consent: explains landlord permission', () => {
    const s = buildResultSummary({ ...TENANT, landlordConsent: 'no' });
    expect(s.reason).toBe('no-landlord-consent');
    expect(allParagraphs(s).join(' ')).toMatch(/landlord's permission/i);
  });

  it('owner answer rows include income/heating, in flow order', () => {
    const s = buildResultSummary(OWNER_ELIGIBLE);
    const labels = s.answers.map((r) => r.label);
    expect(labels).toEqual([
      'Property type',
      'Ownership status',
      'Annual household income',
      'Current insulation',
      'Current heating system',
    ]);
    expect(s.answers[0].value).toBe('Detached house');
  });

  it('tenant answer rows include landlord permission, exclude owner-only fields', () => {
    const s = buildResultSummary(TENANT);
    const labels = s.answers.map((r) => r.label);
    expect(labels).toContain("Landlord's permission");
    expect(labels).not.toContain('Annual household income');
    expect(labels).not.toContain('Current heating system');
  });

  it('drops answer rows whose value is empty or unknown', () => {
    const s = buildResultSummary({ ownership: 'owner', incomeBand: 'low' });
    // propertyType/insulation/heating are blank → no row emitted for them.
    expect(s.answers.every((r) => r.value !== '')).toBe(true);
    expect(s.answers.map((r) => r.label)).not.toContain('Property type');
  });

  it('is robust to undefined answers', () => {
    expect(() => buildResultSummary(undefined)).not.toThrow();
  });
});

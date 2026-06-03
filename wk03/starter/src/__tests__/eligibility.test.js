/**
 * Tests for the pure eligibility() function and the measures it returns.
 * Covers all rule branches, measures conditions, and robustness cases.
 */
import { eligibility, isTenant } from '../eligibility';

describe('eligibility', () => {
  it('1. returns ineligible/income-too-high when incomeBand is high (overrides others)', () => {
    const result = eligibility({
      propertyType: 'detached',
      ownership: 'owner',
      incomeBand: 'high',
      insulation: 'none',
      heating: 'gas-boiler',
    });
    expect(result.outcome).toBe('ineligible');
    expect(result.reason).toBe('income-too-high');
  });

  it('2. returns ineligible/no-measures-needed for full insulation + heat pump', () => {
    const result = eligibility({
      propertyType: 'detached',
      ownership: 'owner',
      incomeBand: 'mid',
      insulation: 'full',
      heating: 'heat-pump',
    });
    expect(result.outcome).toBe('ineligible');
    expect(result.reason).toBe('no-measures-needed');
  });

  it('3. returns partial/renter for private-renter ownership', () => {
    const result = eligibility({
      propertyType: 'flat',
      ownership: 'private-renter',
      incomeBand: 'low',
      insulation: 'partial',
      heating: 'gas-boiler',
    });
    expect(result.outcome).toBe('partial');
    expect(result.reason).toBe('renter');
  });

  it('4. returns partial/renter for housing-association ownership', () => {
    const result = eligibility({
      propertyType: 'flat',
      ownership: 'housing-association',
      incomeBand: 'low',
      insulation: 'partial',
      heating: 'gas-boiler',
    });
    expect(result.outcome).toBe('partial');
    expect(result.reason).toBe('renter');
  });

  it('5. returns partial/renter for council ownership', () => {
    const result = eligibility({
      propertyType: 'flat',
      ownership: 'council',
      incomeBand: 'low',
      insulation: 'partial',
      heating: 'gas-boiler',
    });
    expect(result.outcome).toBe('partial');
    expect(result.reason).toBe('renter');
  });

  it('6. returns partial/owner-mid-income for owner + mid income', () => {
    const result = eligibility({
      propertyType: 'detached',
      ownership: 'owner',
      incomeBand: 'mid',
      insulation: 'partial',
      heating: 'gas-boiler',
    });
    expect(result.outcome).toBe('partial');
    expect(result.reason).toBe('owner-mid-income');
  });

  it('7. returns eligible/owner-low-income for owner + low income', () => {
    const result = eligibility({
      propertyType: 'detached',
      ownership: 'owner',
      incomeBand: 'low',
      insulation: 'partial',
      heating: 'gas-boiler',
    });
    expect(result.outcome).toBe('eligible');
    expect(result.reason).toBe('owner-low-income');
  });

  it('8. returns ineligible/default for an empty object', () => {
    const result = eligibility({});
    expect(result.outcome).toBe('ineligible');
    expect(result.reason).toBe('default');
  });

  it('8a. rule 1 beats rule 2: high income + full insulation + heat pump returns income-too-high (not no-measures-needed)', () => {
    const result = eligibility({
      propertyType: 'detached',
      ownership: 'owner',
      incomeBand: 'high',
      insulation: 'full',
      heating: 'heat-pump',
    });
    expect(result.reason).toBe('income-too-high');
  });

  it('8b. rule 3 beats rule 5: renter + low income returns renter (not owner-low-income)', () => {
    const result = eligibility({
      propertyType: 'detached',
      ownership: 'private-renter',
      incomeBand: 'low',
      insulation: 'partial',
      heating: 'gas-boiler',
    });
    expect(result.reason).toBe('renter');
  });
});

describe('measures', () => {
  it('9. flat + partial insulation + gas boiler: excludes loft, includes internal wall and heat pump', () => {
    const { measures } = eligibility({
      propertyType: 'flat',
      ownership: 'owner',
      incomeBand: 'low',
      insulation: 'partial',
      heating: 'gas-boiler',
    });
    expect(measures).not.toContain('Loft insulation');
    expect(measures).toContain('Internal wall insulation');
    expect(measures).toContain('Air source heat pump installation');
  });

  it('10. full insulation excludes both insulation measures', () => {
    const { measures } = eligibility({
      propertyType: 'detached',
      ownership: 'owner',
      incomeBand: 'low',
      insulation: 'full',
      heating: 'gas-boiler',
    });
    expect(measures).not.toContain('Loft insulation');
    expect(measures).not.toContain('Internal wall insulation');
  });

  it('11. heat-pump heating excludes the heat pump measure', () => {
    const { measures } = eligibility({
      propertyType: 'detached',
      ownership: 'owner',
      incomeBand: 'low',
      insulation: 'partial',
      heating: 'heat-pump',
    });
    expect(measures).not.toContain('Air source heat pump installation');
  });
});

describe('second pathway (tenant vs owner) — content plan §11', () => {
  it('15. tenant + landlord consent "no" returns ineligible/no-landlord-consent', () => {
    const result = eligibility({
      propertyType: 'flat',
      ownership: 'private-renter',
      landlordConsent: 'no',
      insulation: 'none',
    });
    expect(result.outcome).toBe('ineligible');
    expect(result.reason).toBe('no-landlord-consent');
  });

  it('16. tenant + landlord consent "yes" returns partial/renter', () => {
    const result = eligibility({
      propertyType: 'flat',
      ownership: 'housing-association',
      landlordConsent: 'yes',
      insulation: 'partial',
    });
    expect(result.outcome).toBe('partial');
    expect(result.reason).toBe('renter');
  });

  it('17. tenant + landlord consent "not-sure" returns partial/renter', () => {
    const result = eligibility({
      propertyType: 'terraced',
      ownership: 'council',
      landlordConsent: 'not-sure',
      insulation: 'none',
    });
    expect(result.outcome).toBe('partial');
    expect(result.reason).toBe('renter');
  });

  it('18. high-income gate is owner-only: a high-income tenant is still partial/renter', () => {
    // Stale incomeBand can linger if a user starts as an owner then switches to
    // renting; tenure is checked first so the income gate does not fire.
    const result = eligibility({
      propertyType: 'flat',
      ownership: 'private-renter',
      incomeBand: 'high',
      landlordConsent: 'yes',
      insulation: 'partial',
    });
    expect(result.outcome).toBe('partial');
    expect(result.reason).toBe('renter');
  });

  it('19. isTenant is true for every renter tenure and false otherwise', () => {
    expect(isTenant('private-renter')).toBe(true);
    expect(isTenant('housing-association')).toBe(true);
    expect(isTenant('council')).toBe(true);
    expect(isTenant('owner')).toBe(false);
    expect(isTenant('')).toBe(false);
    expect(isTenant(undefined)).toBe(false);
  });
});

describe('robustness', () => {
  it('12. eligibility({}) does not throw and returns ineligible/default with all three measures', () => {
    let result;
    expect(() => { result = eligibility({}); }).not.toThrow();
    expect(result.outcome).toBe('ineligible');
    expect(result.reason).toBe('default');
    expect(Array.isArray(result.measures)).toBe(true);
    expect(result.measures).toEqual(
      expect.arrayContaining([
        'Loft insulation',
        'Internal wall insulation',
        'Air source heat pump installation',
      ])
    );
  });

  it('13. eligibility({ propertyType: "boat" }) does not throw and is ineligible/default', () => {
    let result;
    expect(() => { result = eligibility({ propertyType: 'boat' }); }).not.toThrow();
    expect(result.outcome).toBe('ineligible');
    expect(result.reason).toBe('default');
  });

  it('14. eligibility() called with no arg does not throw', () => {
    let result;
    expect(() => { result = eligibility(); }).not.toThrow();
    expect(result.outcome).toBe('ineligible');
    expect(result.reason).toBe('default');
  });
});

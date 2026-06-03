/**
 * Tests for the question-flow helpers that drive the two eligibility
 * pathways (content plan §11): which fields each path requires, how long
 * each path is, and where the branch points route.
 */
import {
  flowSteps,
  requiredFields,
  totalSteps,
  ownershipNext,
  insulationNext,
  insulationBack,
} from '../flow';

describe('flow — owner path', () => {
  const owner = { ownership: 'owner' };

  it('requires income and heating but not landlord consent', () => {
    const fields = requiredFields(owner);
    expect(fields).toEqual(['propertyType', 'ownership', 'incomeBand', 'insulation', 'heating']);
    expect(fields).not.toContain('landlordConsent');
  });

  it('is 5 steps long', () => {
    expect(totalSteps(owner)).toBe(5);
  });

  it('routes Continue from ownership to /income and insulation onward to /heating', () => {
    expect(ownershipNext(owner)).toBe('/income');
    expect(insulationNext(owner)).toBe('/heating');
    expect(insulationBack(owner)).toBe('/income');
  });
});

describe('flow — tenant path', () => {
  const tenant = { ownership: 'private-renter' };

  it('requires landlord consent but not income or heating', () => {
    const fields = requiredFields(tenant);
    expect(fields).toEqual(['propertyType', 'ownership', 'landlordConsent', 'insulation']);
    expect(fields).not.toContain('incomeBand');
    expect(fields).not.toContain('heating');
  });

  it('is 4 steps long', () => {
    expect(totalSteps(tenant)).toBe(4);
  });

  it('routes Continue from ownership to /landlord-consent and insulation onward to /check-answers', () => {
    expect(ownershipNext(tenant)).toBe('/landlord-consent');
    expect(insulationNext(tenant)).toBe('/check-answers');
    expect(insulationBack(tenant)).toBe('/landlord-consent');
  });
});

describe('flow — before the branch', () => {
  it('defaults to the owner path when ownership is not yet chosen', () => {
    expect(totalSteps({})).toBe(5);
    expect(flowSteps({})[0].field).toBe('propertyType');
    expect(ownershipNext({})).toBe('/income');
  });
});

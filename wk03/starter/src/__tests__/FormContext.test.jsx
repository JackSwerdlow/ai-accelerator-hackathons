/**
 * FormContext persistence tests.
 *
 * Covers the localStorage save-and-return behaviour added in the
 * "Save and return" feature: persist on every setAnswer, restore on
 * mount, discard malformed data, and fail safely when storage throws
 * (e.g. private-browsing mode).
 */
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  FormProvider,
  STORAGE_KEY,
  useFormContext,
} from '../contexts/FormContext';

function Harness() {
  const { answers, setAnswer, resetAnswers } = useFormContext();
  return (
    <>
      <div data-testid="property">{answers.propertyType}</div>
      <div data-testid="income">{answers.incomeBand}</div>
      <button onClick={() => setAnswer('propertyType', 'detached')}>set-property</button>
      <button onClick={() => setAnswer('incomeBand', 'low')}>set-income</button>
      <button onClick={() => resetAnswers()}>reset</button>
    </>
  );
}

beforeEach(() => {
  window.localStorage.clear();
});

describe('FormContext localStorage persistence', () => {
  it('writes to localStorage on every setAnswer call', async () => {
    const user = userEvent.setup();
    render(
      <FormProvider>
        <Harness />
      </FormProvider>,
    );

    await user.click(screen.getByText('set-property'));
    expect(screen.getByTestId('property').textContent).toBe('detached');

    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY));
    expect(stored.propertyType).toBe('detached');
    expect(stored.incomeBand).toBe('');
  });

  it('restores answers from localStorage on first mount', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        propertyType: 'flat',
        ownership: 'owner',
        incomeBand: 'low',
        landlordConsent: '',
        insulation: 'none',
        heating: 'gas-boiler',
      }),
    );

    render(
      <FormProvider>
        <Harness />
      </FormProvider>,
    );

    expect(screen.getByTestId('property').textContent).toBe('flat');
    expect(screen.getByTestId('income').textContent).toBe('low');
  });

  it('resetAnswers clears both in-memory state and localStorage', async () => {
    const user = userEvent.setup();
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        propertyType: 'flat',
        ownership: 'owner',
        incomeBand: 'low',
        landlordConsent: '',
        insulation: 'none',
        heating: 'gas-boiler',
      }),
    );

    render(
      <FormProvider>
        <Harness />
      </FormProvider>,
    );

    expect(screen.getByTestId('property').textContent).toBe('flat');
    await user.click(screen.getByText('reset'));
    expect(screen.getByTestId('property').textContent).toBe('');
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe(JSON.stringify({
      propertyType: '',
      ownership: '',
      incomeBand: '',
      landlordConsent: '',
      insulation: '',
      heating: '',
    }));
  });

  it('discards malformed data with invalid field values', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        propertyType: 'spaceship', // not in allowed values
        ownership: 'owner',
        incomeBand: 'low',
        insulation: 'none',
        heating: 'gas-boiler',
      }),
    );

    render(
      <FormProvider>
        <Harness />
      </FormProvider>,
    );

    // Whole blob discarded — every field renders empty
    expect(screen.getByTestId('property').textContent).toBe('');
    expect(screen.getByTestId('income').textContent).toBe('');
  });

  it('discards non-JSON stored content', () => {
    window.localStorage.setItem(STORAGE_KEY, 'not-valid-json{{');

    render(
      <FormProvider>
        <Harness />
      </FormProvider>,
    );

    expect(screen.getByTestId('property').textContent).toBe('');
  });

  it('continues updating in-memory state even if localStorage.setItem throws', async () => {
    const originalSetItem = Storage.prototype.setItem;
    // Simulate private-browsing / quota-exceeded throw.
    Storage.prototype.setItem = () => {
      throw new Error('QuotaExceededError');
    };

    try {
      const user = userEvent.setup();
      render(
        <FormProvider>
          <Harness />
        </FormProvider>,
      );

      await user.click(screen.getByText('set-property'));
      expect(screen.getByTestId('property').textContent).toBe('detached');
    } finally {
      Storage.prototype.setItem = originalSetItem;
    }
  });
});

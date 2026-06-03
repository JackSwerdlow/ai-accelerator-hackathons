/**
 * Form state context for the Green Home Grant checker.
 *
 * Holds the five question answers and persists them to localStorage
 * (key "ghg:answers:v1") so users can resume a partially completed form.
 * Reads/writes are wrapped in try/catch so private-browsing and quota
 * errors fail silently — the in-memory state still works.
 *
 * Wrap the app in <FormProvider> and read state via useFormContext().
 */
import { createContext, useCallback, useContext, useEffect, useState } from 'react';

const INITIAL_ANSWERS = {
  propertyType: '',
  ownership: '',
  incomeBand: '',
  insulation: '',
  heating: '',
};

const STORAGE_KEY = 'ghg:answers:v1';

/**
 * Allowed values per field. Used to validate restored data — if a stored
 * value isn't in its allow-list we discard the whole blob and start fresh.
 * Keeps stale data from a prior schema version out of the running state.
 */
const ALLOWED_VALUES = {
  propertyType: ['', 'detached', 'semi-detached', 'terraced', 'flat', 'bungalow'],
  ownership: ['', 'owner', 'private-renter', 'housing-association', 'council'],
  incomeBand: ['', 'low', 'mid', 'high'],
  insulation: ['', 'none', 'partial', 'full'],
  heating: ['', 'gas-boiler', 'oil-boiler', 'electric-storage', 'heat-pump', 'other'],
};

function readPersistedAnswers() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    const result = {};
    for (const field of Object.keys(INITIAL_ANSWERS)) {
      const value = parsed[field];
      if (typeof value !== 'string' || !ALLOWED_VALUES[field].includes(value)) {
        return null;
      }
      result[field] = value;
    }
    return result;
  } catch {
    return null;
  }
}

function writePersistedAnswers(answers) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(answers));
  } catch {
    // Quota exceeded or storage disabled (private mode) — ignore.
  }
}

function clearPersistedAnswers() {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

const FormContext = createContext(null);

/**
 * Provider that owns the answers state and exposes it to descendants.
 *
 * Reads any previously persisted answers on first render and mirrors every
 * subsequent change back to localStorage so a refresh or return visit picks
 * up where the user left off.
 *
 * @param {{ children: React.ReactNode }} props
 * @returns {JSX.Element}
 */
export function FormProvider({ children }) {
  const [answers, setAnswers] = useState(
    () => readPersistedAnswers() ?? INITIAL_ANSWERS,
  );

  useEffect(() => {
    writePersistedAnswers(answers);
  }, [answers]);

  const setAnswer = useCallback((field, value) => {
    setAnswers((prev) => ({ ...prev, [field]: value }));
  }, []);

  const resetAnswers = useCallback(() => {
    clearPersistedAnswers();
    setAnswers(INITIAL_ANSWERS);
  }, []);

  return (
    <FormContext.Provider value={{ answers, setAnswer, resetAnswers }}>
      {children}
    </FormContext.Provider>
  );
}

/**
 * Hook to read and mutate the shared answers state.
 * Throws if called outside a <FormProvider>.
 *
 * @returns {{ answers: object, setAnswer: (field: string, value: string) => void, resetAnswers: () => void }}
 */
export function useFormContext() {
  const ctx = useContext(FormContext);
  if (!ctx) throw new Error('useFormContext must be used inside <FormProvider>');
  return ctx;
}

export { INITIAL_ANSWERS, STORAGE_KEY };

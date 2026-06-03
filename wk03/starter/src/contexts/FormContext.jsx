/**
 * Form state context for the Green Home Grant checker.
 * Holds the five question answers and exposes setters / reset.
 * Wrap the app in <FormProvider> and read state via useFormContext().
 */
import { createContext, useContext, useState } from 'react';

const INITIAL_ANSWERS = {
  propertyType: '',
  ownership: '',
  incomeBand: '',     // owner path only
  landlordConsent: '', // tenant path only (content plan §11)
  insulation: '',
  heating: '',        // owner path only
};

const FormContext = createContext(null);

/**
 * Provider that owns the answers state and exposes it to descendants.
 *
 * @param {{ children: React.ReactNode }} props
 * @returns {JSX.Element}
 */
export function FormProvider({ children }) {
  const [answers, setAnswers] = useState(INITIAL_ANSWERS);
  const setAnswer = (field, value) =>
    setAnswers((prev) => ({ ...prev, [field]: value }));
  const resetAnswers = () => setAnswers(INITIAL_ANSWERS);
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

export { INITIAL_ANSWERS };

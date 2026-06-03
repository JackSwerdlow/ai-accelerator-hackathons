import QuestionPage from '../components/QuestionPage';

/**
 * Question 1: Property type.
 * Thin wrapper around QuestionPage; copy and options come from the
 * content plan (`docs/plans/2026-06-03-content-plan.md` §3).
 */
export default function PropertyTypePage() {
  return (
    <QuestionPage
      pageTitle="What type of property do you live in?"
      fieldName="propertyType"
      step={1}
      totalSteps={5}
      options={[
        { value: 'detached', label: 'Detached house' },
        { value: 'semi-detached', label: 'Semi-detached house' },
        { value: 'terraced', label: 'Terraced house' },
        { value: 'flat', label: 'Flat or apartment' },
        { value: 'bungalow', label: 'Bungalow' },
      ]}
      errorMessage="Select the type of property you live in"
      backHref="/"
      onContinueNavigateTo="/ownership"
    />
  );
}

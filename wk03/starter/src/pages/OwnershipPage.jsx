import QuestionPage from '../components/QuestionPage';

/**
 * Question 2: Ownership status.
 * Thin wrapper around QuestionPage; copy and options come from the
 * content plan (`docs/plans/2026-06-03-content-plan.md` §3).
 */
export default function OwnershipPage() {
  return (
    <QuestionPage
      pageTitle="What is your ownership status?"
      fieldName="ownership"
      step={2}
      totalSteps={5}
      options={[
        { value: 'owner', label: 'I own my home' },
        { value: 'private-renter', label: 'I rent from a private landlord' },
        { value: 'housing-association', label: 'I rent from a housing association' },
        { value: 'council', label: 'I rent from a council or local authority' },
      ]}
      hint='If you own your home with a mortgage, select "I own my home".'
      errorMessage="Select your ownership status"
      backHref="/property-type"
      onContinueNavigateTo="/income"
    />
  );
}

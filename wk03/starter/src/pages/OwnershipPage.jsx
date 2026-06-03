/**
 * Question 2: ownership status. Thin wrapper around <QuestionPage>
 * per PLAN.md §6.1 / content plan §3 Q2.
 */
import QuestionPage from "../components/QuestionPage";

const OPTIONS = [
  { value: "owner", label: "I own my home" },
  { value: "private-renter", label: "I rent from a private landlord" },
  { value: "housing-association", label: "I rent from a housing association" },
  { value: "council", label: "I rent from a council or local authority" },
];

/**
 * Renders the "What is your ownership status?" question (step 2 of 5),
 * with a hint clarifying that mortgaged owners pick "I own my home".
 *
 * @returns {JSX.Element}
 */
export default function OwnershipPage() {
  return (
    <QuestionPage
      pageTitle="What is your ownership status?"
      fieldName="ownership"
      step={2}
      totalSteps={5}
      options={OPTIONS}
      hint='If you own your home with a mortgage, select "I own my home".'
      errorMessage="Select your ownership status"
      backHref="/property-type"
      onContinueNavigateTo="/income"
    />
  );
}

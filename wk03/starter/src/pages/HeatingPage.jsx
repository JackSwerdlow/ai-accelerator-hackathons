/**
 * Question 5: current main heating system. Thin wrapper around
 * <QuestionPage> per PLAN.md §6.1 / content plan §3 Q5, with a
 * help-details disclosure explaining the "Other" option.
 */
import QuestionPage from "../components/QuestionPage";
import { totalSteps } from "../flow";

const OPTIONS = [
  { value: "gas-boiler", label: "Gas boiler" },
  { value: "oil-boiler", label: "Oil boiler" },
  { value: "electric-storage", label: "Electric storage heaters" },
  { value: "heat-pump", label: "Heat pump (air source or ground source)" },
  { value: "other", label: "Other" },
];

/**
 * Renders the "What is your current main heating system?" question
 * (step 5, owner path only), with hint and contextual help details.
 *
 * @returns {JSX.Element}
 */
export default function HeatingPage() {
  return (
    <QuestionPage
      pageTitle="What is your current main heating system?"
      fieldName="heating"
      step={5}
      totalSteps={totalSteps}
      options={OPTIONS}
      hint="Select the system that heats most of your home."
      helpDetails={{
        summaryText: 'What does "Other" mean?',
        bodyText:
          'Select "Other" if your main heating system is not on the list — for example, solid fuel, wood burner, or community heating. An installer can advise during a property assessment.',
      }}
      errorMessage="Select your current main heating system"
      backHref="/insulation"
      onContinueNavigateTo="/check-answers"
    />
  );
}

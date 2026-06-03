/**
 * Question 3: annual household income band. Thin wrapper around
 * <QuestionPage> per PLAN.md §6.1 / content plan §3 Q3, with a
 * help-details disclosure.
 */
import QuestionPage from "../components/QuestionPage";
import { totalSteps } from "../flow";

const OPTIONS = [
  { value: "low", label: "Under £31,000" },
  { value: "mid", label: "£31,000 to £60,000" },
  { value: "high", label: "Over £60,000" },
];

/**
 * Renders the "What is your total annual household income?" question
 * (step 3, owner path only), with hint and contextual help details.
 *
 * @returns {JSX.Element}
 */
export default function IncomePage() {
  return (
    <QuestionPage
      pageTitle="What is your total annual household income?"
      fieldName="incomeBand"
      step={3}
      totalSteps={totalSteps}
      options={OPTIONS}
      hint="Include the income of all adults living in your home, before tax and other deductions."
      helpDetails={{
        summaryText: "Help with annual household income",
        bodyText:
          "Include earnings from employment, self-employment, pensions, rental income, and benefits. Do not include one-off payments like inheritance or lottery winnings.",
      }}
      errorMessage="Select your annual household income"
      backHref="/ownership"
      onContinueNavigateTo="/insulation"
    />
  );
}

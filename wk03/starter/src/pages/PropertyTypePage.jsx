/**
 * Question 1: property type. Thin wrapper around <QuestionPage>
 * per PLAN.md §6.1 / content plan §3 Q1.
 */
import QuestionPage from "../components/QuestionPage";
import { totalSteps } from "../flow";

const OPTIONS = [
  { value: "detached", label: "Detached house" },
  { value: "semi-detached", label: "Semi-detached house" },
  { value: "terraced", label: "Terraced house" },
  { value: "flat", label: "Flat or apartment" },
  { value: "bungalow", label: "Bungalow" },
];

/**
 * Renders the "What type of property do you live in?" question (step 1).
 * The total step count is path-aware (5 for owners, 4 for tenants — see
 * content plan §11).
 *
 * @returns {JSX.Element}
 */
export default function PropertyTypePage() {
  return (
    <QuestionPage
      pageTitle="What type of property do you live in?"
      fieldName="propertyType"
      step={1}
      totalSteps={totalSteps}
      options={OPTIONS}
      errorMessage="Select the type of property you live in"
      backHref="/"
      onContinueNavigateTo="/ownership"
    />
  );
}

/**
 * Question 4: current insulation level. Thin wrapper around
 * <QuestionPage> per PLAN.md §6.1 / content plan §3 Q4, with a
 * help-details disclosure pointing users to their EPC.
 */
import QuestionPage from "../components/QuestionPage";

const OPTIONS = [
  { value: "none", label: "No insulation" },
  { value: "partial", label: "Some insulation (for example, loft only or walls only)" },
  { value: "full", label: "Full insulation (loft and walls)" },
];

/**
 * Renders the "What insulation does your home currently have?" question
 * (step 4 of 5), with hint and contextual help details.
 *
 * @returns {JSX.Element}
 */
export default function InsulationPage() {
  return (
    <QuestionPage
      pageTitle="What insulation does your home currently have?"
      fieldName="insulation"
      step={4}
      totalSteps={5}
      options={OPTIONS}
      hint="If you are not sure, check your Energy Performance Certificate (EPC). Your landlord or mortgage provider may have a copy."
      helpDetails={{
        summaryText: "Help with finding your insulation level",
        bodyText:
          "An EPC is a one-page summary of how energy-efficient your home is. If you do not have one to hand, an installer can confirm during a property assessment.",
      }}
      errorMessage="Select the insulation your home currently has"
      backHref="/income"
      onContinueNavigateTo="/heating"
    />
  );
}

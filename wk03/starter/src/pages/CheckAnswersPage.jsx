/**
 * Check-your-answers page (route "/check-answers"). Lists the answers for the
 * user's path (owner or tenant) in a GOV.UK summary list, with per-row
 * "Change" links that preserve the return-to-check-answers flow. Guards
 * against deep links with missing answers per PLAN.md §6 / content plan §4 +
 * §11. The summary is path-aware so a tenant is not shown — or blocked on —
 * owner-only questions, and vice versa.
 */
import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useFormContext } from "../contexts/FormContext";
import { flowSteps } from "../flow";
import { labelFor } from "../displayLabels";
import SummaryList from "../components/SummaryList";
import GovukButton from "../components/GovukButton";

const ROW_LABELS = {
  propertyType:    { label: "Property type",            hidden: "property type" },
  ownership:       { label: "Ownership status",         hidden: "ownership status" },
  incomeBand:      { label: "Annual household income",  hidden: "annual household income" },
  landlordConsent: { label: "Landlord's permission",    hidden: "whether you have your landlord's permission" },
  insulation:      { label: "Current insulation",       hidden: "current insulation" },
  heating:         { label: "Current heating system",   hidden: "current heating system" },
};

/**
 * Renders the summary list of answers and the submit button. If any answer
 * required by the current path is empty, redirects to the first unanswered
 * question on that path.
 *
 * @returns {JSX.Element}
 */
export default function CheckAnswersPage() {
  const { answers } = useFormContext();
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Check your answers - Green Home Grant - GOV.UK";
  }, []);

  const steps = flowSteps(answers);

  useEffect(() => {
    const firstMissing = steps.find(({ field }) => !answers[field]);
    if (firstMissing) navigate(firstMissing.route, { replace: true });
  }, [answers, navigate, steps]);

  const rows = steps.map(({ field, route }) => ({
    key: ROW_LABELS[field].label,
    value: labelFor(field, answers[field]),
    changeHref: `${route}?from=check-answers`,
    changeHiddenText: ROW_LABELS[field].hidden,
  }));

  // Back goes to the last question of whichever path the user travelled.
  const backHref = steps[steps.length - 1].route;

  return (
    <>
      <Link to={backHref} className="govuk-back-link">Back</Link>

      <h1 className="govuk-heading-xl">Check your answers</h1>
      <p className="govuk-body">Check your answers before you find out if you are eligible.</p>

      <SummaryList rows={rows} />

      <GovukButton onClick={() => navigate("/result")}>Submit and see result</GovukButton>
    </>
  );
}

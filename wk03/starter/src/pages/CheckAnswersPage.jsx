/**
 * Check-your-answers page (route "/check-answers"). Lists the five
 * answers in a GOV.UK summary list, with per-row "Change" links that
 * preserve the return-to-check-answers flow. Guards against deep links
 * with missing answers per PLAN.md §6 / content plan §4.
 */
import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useFormContext } from "../contexts/FormContext";
import { labelFor } from "../displayLabels";
import SummaryList from "../components/SummaryList";
import GovukButton from "../components/GovukButton";

const FIELD_ORDER = [
  { field: "propertyType", route: "/property-type" },
  { field: "ownership",    route: "/ownership" },
  { field: "incomeBand",   route: "/income" },
  { field: "insulation",   route: "/insulation" },
  { field: "heating",      route: "/heating" },
];

const ROW_LABELS = {
  propertyType: { label: "Property type",            hidden: "property type" },
  ownership:    { label: "Ownership status",         hidden: "ownership status" },
  incomeBand:   { label: "Annual household income",  hidden: "annual household income" },
  insulation:   { label: "Current insulation",       hidden: "current insulation" },
  heating:      { label: "Current heating system",   hidden: "current heating system" },
};

/**
 * Renders the summary list of answers and the submit button. If any
 * answer is empty, redirects to the first unanswered question.
 *
 * @returns {JSX.Element}
 */
export default function CheckAnswersPage() {
  const { answers } = useFormContext();
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Check your answers - Green Home Grant - GOV.UK";
  }, []);

  useEffect(() => {
    const firstMissing = FIELD_ORDER.find(({ field }) => !answers[field]);
    if (firstMissing) navigate(firstMissing.route, { replace: true });
  }, [answers, navigate]);

  const rows = FIELD_ORDER.map(({ field, route }) => ({
    key: ROW_LABELS[field].label,
    value: labelFor(field, answers[field]),
    changeHref: `${route}?from=check-answers`,
    changeHiddenText: ROW_LABELS[field].hidden,
  }));

  return (
    <>
      <Link to="/heating" className="govuk-back-link">Back</Link>

      <h1 className="govuk-heading-xl">Check your answers</h1>
      <p className="govuk-body">Check your answers before you find out if you are eligible.</p>

      <SummaryList rows={rows} />

      <GovukButton onClick={() => navigate("/result")}>Submit and see result</GovukButton>
    </>
  );
}

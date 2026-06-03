/**
 * Result page (route "/result"). Renders the eligibility outcome panel
 * and outcome-specific next-step copy, switching body content by
 * (outcome, reason) per PLAN.md §6 / content plan §7. Guards against
 * deep links with missing answers by redirecting to "/".
 */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useFormContext } from "../contexts/FormContext";
import { eligibility } from "../eligibility";
import Panel from "../components/Panel";

const FIELDS = ["propertyType", "ownership", "incomeBand", "insulation", "heating"];

/**
 * Renders the panel, recommended measures, and outcome-specific
 * next-step copy for the user's eligibility result.
 *
 * @returns {JSX.Element}
 */
export default function ResultPage() {
  const { answers } = useFormContext();
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Your result - Green Home Grant - GOV.UK";
  }, []);

  useEffect(() => {
    if (FIELDS.some((f) => !answers[f])) navigate("/", { replace: true });
  }, [answers, navigate]);

  const { outcome, reason, measures } = eligibility(answers);

  let panelTitle;
  let panelBody;
  if (outcome === "eligible") {
    panelTitle = "You may be eligible for a Green Home Grant";
    panelBody = "You may qualify for a grant of up to £10,000";
  } else if (outcome === "partial") {
    panelTitle = "You may be partially eligible for a Green Home Grant";
  } else {
    panelTitle = "You are not eligible for a Green Home Grant";
  }

  return (
    <>
      <Panel outcome={outcome} title={panelTitle} body={panelBody} />

      {outcome === "eligible" && (
        <>
          <p className="govuk-body">Based on your answers, your home could qualify for the following measures:</p>
          <ul className="govuk-list govuk-list--bullet">
            {measures.map((m) => <li key={m}>{m}</li>)}
          </ul>
          <p className="govuk-body">
            The grant covers up to two-thirds of the cost of each measure, up to the maximum grant amount.
          </p>
          <h2 className="govuk-heading-m">What to do next</h2>
          <p className="govuk-body">
            Contact an approved Green Home Grant installer to assess your property.
            They will confirm which measures are suitable and apply for the grant on your behalf.
          </p>
          <p className="govuk-body">
            You do not need to pay anything upfront. The installer will claim the grant directly from the
            scheme administrator.
          </p>
          <p className="govuk-body">
            <a className="govuk-link" href="#">Find an approved installer</a>
          </p>
        </>
      )}

      {outcome === "partial" && reason === "renter" && (
        <>
          <p className="govuk-body">As a tenant, your landlord needs to apply for this grant on your behalf.</p>
          <p className="govuk-body">
            We can send you an information pack to share with your landlord. It explains the grant, the
            installation process, and how to apply.
          </p>
          <h2 className="govuk-heading-m">What to do next</h2>
          <p className="govuk-body">
            Ask your landlord to contact an approved installer for a property assessment.
            Landlords can apply directly through the Green Home Grant scheme.
          </p>
          <p className="govuk-body">
            <a className="govuk-link" href="#">Find an approved installer</a>
          </p>
        </>
      )}

      {outcome === "partial" && reason === "owner-mid-income" && (
        <>
          <p className="govuk-body">Based on your income band, you may qualify for a partial grant of up to £5,000.</p>
          <p className="govuk-body">Your home could qualify for the following measures:</p>
          <ul className="govuk-list govuk-list--bullet">
            {measures.map((m) => <li key={m}>{m}</li>)}
          </ul>
          <h2 className="govuk-heading-m">What to do next</h2>
          <p className="govuk-body">
            Contact an approved Green Home Grant installer to assess your property.
            The installer will apply for the grant on your behalf.
          </p>
          <p className="govuk-body">
            <a className="govuk-link" href="#">Find an approved installer</a>
          </p>
        </>
      )}

      {outcome === "ineligible" && (
        <>
          {reason === "income-too-high" && (
            <p className="govuk-body">Your household income is above the threshold for this grant.</p>
          )}
          {reason === "no-measures-needed" && (
            <p className="govuk-body">
              Your home already has the insulation and heating measures this grant covers. No further measures
              are available under this scheme.
            </p>
          )}
          <p className="govuk-body">
            You may still be able to improve your home's energy efficiency through other government schemes.
          </p>
          <p className="govuk-body">
            <a className="govuk-link" href="#">Find other energy efficiency schemes</a>
          </p>
        </>
      )}
    </>
  );
}

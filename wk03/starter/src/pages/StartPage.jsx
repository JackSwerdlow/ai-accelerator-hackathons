/**
 * Start page (route "/") for the Green Home Grant eligibility checker.
 * Renders the service summary and a "Start now" button per PLAN.md §6
 * and content plan §2.
 */
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import GovukButton from "../components/GovukButton";

/**
 * Renders the public start page with a description of the service and
 * a chevron "Start now" button that routes to the first question.
 *
 * @returns {JSX.Element}
 */
export default function StartPage() {
  const navigate = useNavigate();
  useEffect(() => {
    document.title = "Check if you can get a Green Home Grant - Green Home Grant - GOV.UK";
  }, []);

  return (
    <>
      <h1 className="govuk-heading-xl">Check if you can get a Green Home Grant</h1>

      <p className="govuk-body-l">
        Use this service to find out whether you qualify for a Green Home Grant.
      </p>

      <p className="govuk-body">
        The grant helps homeowners and tenants get funding toward home insulation
        and heat pump installation to reduce energy bills and carbon emissions.
      </p>

      <p className="govuk-body">The check takes around 2 minutes. You will need to know:</p>

      <ul className="govuk-list govuk-list--bullet">
        <li>the type of property you live in</li>
        <li>whether you own or rent</li>
        <li>your total annual household income</li>
        <li>whether your home currently has insulation</li>
        <li>your current main heating system</li>
      </ul>

      <GovukButton variant="start" onClick={() => navigate("/property-type")}>
        Start now
      </GovukButton>
    </>
  );
}

/**
 * Start page (route "/") for the Green Home Grant eligibility checker.
 *
 * Renders the service summary and a "Start now" button per PLAN.md §6 /
 * content plan §2. When the user has previously answered any question
 * (read from FormContext, which is persisted to localStorage), a GOV.UK
 * notification banner is shown above the H1 offering "Continue your check"
 * or "Start again".
 */
import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import GovukButton from "../components/GovukButton";
import { useFormContext } from "../contexts/FormContext";

/**
 * Renders the public start page. Includes an in-progress resume banner
 * when the persisted form state contains any non-empty answer.
 *
 * @returns {JSX.Element}
 */
export default function StartPage() {
  const navigate = useNavigate();
  const { answers, resetAnswers } = useFormContext();
  const hasInProgressAnswers = Object.values(answers).some((value) => value !== "");

  useEffect(() => {
    document.title = "Check if you can get a Green Home Grant - Green Home Grant - GOV.UK";
  }, []);

  return (
    <>
      {hasInProgressAnswers && (
        <div
          className="govuk-notification-banner"
          role="region"
          aria-labelledby="resume-banner-title"
        >
          <div className="govuk-notification-banner__header">
            <h2 id="resume-banner-title" className="govuk-notification-banner__title">
              You have a partially completed check
            </h2>
          </div>
          <div className="govuk-notification-banner__content">
            <p className="govuk-body">
              Your previous answers are saved on this device. You can continue
              your check or start again with a blank form.
            </p>
            <div className="govuk-button-group">
              <GovukButton onClick={() => navigate("/property-type")}>
                Continue your check
              </GovukButton>
              <button
                type="button"
                className="govuk-button govuk-button--secondary"
                onClick={resetAnswers}
              >
                Start again
              </button>
            </div>
          </div>
        </div>
      )}

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

      <p className="govuk-body">
        <Link className="govuk-link" to="/help">
          Not sure? Describe your situation in your own words
        </Link>
      </p>
    </>
  );
}

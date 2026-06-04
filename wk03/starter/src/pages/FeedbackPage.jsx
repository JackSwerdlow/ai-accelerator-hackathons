/**
 * GOV.UK feedback form at /feedback. No backend: on submit it shows a
 * thank-you confirmation and intentionally stores/sends nothing.
 */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import GovukButton from "../components/GovukButton";

// Satisfaction scale options (value used in code, label shown to the user).
const SATISFACTION_OPTIONS = [
  { value: "very-satisfied", label: "Very satisfied" },
  { value: "satisfied", label: "Satisfied" },
  { value: "neither", label: "Neither satisfied nor dissatisfied" },
  { value: "dissatisfied", label: "Dissatisfied" },
  { value: "very-dissatisfied", label: "Very dissatisfied" },
];

/**
 * Renders the give-feedback page. Before submit it shows the satisfaction
 * radio group and a free-text comments box; after submit it swaps to a
 * GOV.UK confirmation panel. Nothing is persisted or transmitted.
 *
 * @returns {JSX.Element}
 */
export default function FeedbackPage() {
  const [submitted, setSubmitted] = useState(false);
  const [satisfaction, setSatisfaction] = useState("");
  const [comments, setComments] = useState("");

  // Keep the document title in sync with the form vs confirmation state.
  useEffect(() => {
    document.title = submitted
      ? "Feedback sent - Green Home Grant - GOV.UK"
      : "Give feedback - Green Home Grant - GOV.UK";
  }, [submitted]);

  /**
   * Handles form submission: shows the confirmation. Nothing is sent or
   * persisted — this is intentional (no backend).
   *
   * @param {React.FormEvent<HTMLFormElement>} e - The submit event.
   * @returns {void}
   */
  function handleSubmit(e) {
    e.preventDefault();
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <>
        <div className="govuk-panel govuk-panel--confirmation">
          <h1 className="govuk-panel__title">Thank you for your feedback</h1>
        </div>
        <p className="govuk-body">Your feedback helps us improve the service.</p>
        <p className="govuk-body">
          <Link className="govuk-link" to="/">
            Return to the start page
          </Link>
        </p>
      </>
    );
  }

  return (
    <>
      <Link to="/" className="govuk-back-link">
        Back
      </Link>
      <h1 className="govuk-heading-xl">Give feedback on this service</h1>
      <p className="govuk-body">
        Your feedback is anonymous and helps us improve this service.
      </p>
      <form onSubmit={handleSubmit}>
        <fieldset className="govuk-fieldset">
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--m">
            Overall, how did you feel about the service you received today?
          </legend>
          <div className="govuk-radios">
            {SATISFACTION_OPTIONS.map(({ value, label }) => (
              <div className="govuk-radios__item" key={value}>
                <input
                  className="govuk-radios__input"
                  id={`satisfaction-${value}`}
                  name="satisfaction"
                  type="radio"
                  value={value}
                  checked={satisfaction === value}
                  onChange={() => setSatisfaction(value)}
                />
                <label
                  className="govuk-label govuk-radios__label"
                  htmlFor={`satisfaction-${value}`}
                >
                  {label}
                </label>
              </div>
            ))}
          </div>
        </fieldset>
        <label className="govuk-label" htmlFor="feedback-comments">
          How could we improve this service?
        </label>
        <div id="feedback-comments-hint" className="govuk-hint">
          Do not include personal or financial information.
        </div>
        <textarea
          id="feedback-comments"
          className="govuk-textarea"
          rows={5}
          aria-describedby="feedback-comments-hint"
          value={comments}
          onChange={(e) => setComments(e.target.value)}
        />
        <GovukButton type="submit">Send feedback</GovukButton>
      </form>
    </>
  );
}

/**
 * GOV.UK phase banner. Renders the alpha/beta tag plus the standard
 * "this is a new service" feedback line. The dash before "your" is a
 * U+2013 en dash (not a hyphen-minus) to match GOV.UK Design System.
 */

/**
 * Renders the GOV.UK phase banner with a coloured phase tag and a
 * feedback link.
 *
 * @param {{ phase?: string, feedbackHref?: string }} props
 * @returns {JSX.Element}
 */
export default function PhaseBanner({ phase = "alpha", feedbackHref = "#" }) {
  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">{phase}</strong>
        <span className="govuk-phase-banner__text">
          This is a new service – your <a className="govuk-link" href={feedbackHref}>feedback</a> will help us to improve it.
        </span>
      </p>
    </div>
  );
}

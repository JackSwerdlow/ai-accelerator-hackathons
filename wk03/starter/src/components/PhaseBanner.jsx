/**
 * GOV.UK phase banner. Renders the alpha/beta tag plus the standard
 * "this is a new service" feedback line. The dash before "your" is a
 * U+2013 en dash (not a hyphen-minus) to match GOV.UK Design System.
 */
import { Link } from "react-router-dom";

/**
 * Renders the GOV.UK phase banner with a coloured phase tag and a
 * feedback link. Internal feedback targets use react-router so the
 * client-side FormContext survives the navigation; external/default
 * targets fall back to a plain anchor.
 *
 * @param {{ phase?: string, feedbackHref?: string }} props
 * @returns {JSX.Element}
 */
export default function PhaseBanner({ phase = "alpha", feedbackHref = "#" }) {
  // In-app paths start with "/"; route them through <Link> to avoid a
  // full page reload that would wipe FormContext.
  const isInternal = feedbackHref.startsWith("/");
  const feedbackLink = isInternal ? (
    <Link className="govuk-link" to={feedbackHref}>feedback</Link>
  ) : (
    <a className="govuk-link" href={feedbackHref}>feedback</a>
  );

  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">{phase}</strong>
        <span className="govuk-phase-banner__text">
          This is a new service – your {feedbackLink} will help us to improve it.
        </span>
      </p>
    </div>
  );
}

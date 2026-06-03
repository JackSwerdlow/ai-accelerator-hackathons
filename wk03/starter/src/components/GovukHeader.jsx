/**
 * GOV.UK header chrome: the cross-government GOV.UK wordmark plus the
 * service-name link to the journey start. Wordmark is a plain <a>
 * because gov.uk is a separate site; the service name uses
 * react-router <Link> so it preserves FormContext.
 */
import { Link } from "react-router-dom";

/**
 * Renders the persistent GOV.UK header banner.
 *
 * @returns {JSX.Element}
 */
export default function GovukHeader() {
  return (
    <header className="govuk-header" role="banner">
      <div className="govuk-header__container">
        <a href="https://www.gov.uk/" className="govuk-header__link govuk-header__link--homepage">
          <svg
            className="govuk-header__logotype-crown"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 36 32"
            width="36"
            height="32"
            aria-hidden="true"
            focusable="false"
          >
            <path d="M2 26 L34 26 L31 12 L24 18 L18 6 L12 18 L5 12 Z" />
            <circle cx="5" cy="9" r="2" />
            <circle cx="18" cy="3" r="2" />
            <circle cx="31" cy="9" r="2" />
          </svg>
          GOV.UK
        </a>
        <Link to="/" className="govuk-header__link govuk-header__link--service-name">
          Green Home Grant
        </Link>
      </div>
    </header>
  );
}

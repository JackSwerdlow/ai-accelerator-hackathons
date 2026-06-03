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
          GOV.UK
        </a>
        <Link to="/" className="govuk-header__link govuk-header__link--service-name">
          Green Home Grant
        </Link>
      </div>
    </header>
  );
}

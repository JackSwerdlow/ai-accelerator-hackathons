/**
 * GOV.UK footer chrome. Lists the in-app accessibility statement (via
 * react-router <Link>) plus meta links that point to the relevant gov.uk
 * pages (Help, Privacy, Cookies, Contact, Terms and conditions).
 */
import { Link } from "react-router-dom";

/**
 * Renders the persistent GOV.UK footer with meta links.
 *
 * @returns {JSX.Element}
 */
export default function GovukFooter() {
  return (
    <footer className="govuk-footer" role="contentinfo">
      <div className="govuk-width-container">
        <div className="govuk-footer__meta">
          <div className="govuk-footer__meta-item">
            <ul className="govuk-footer__inline-list">
              <li className="govuk-footer__inline-list-item">
                <a className="govuk-footer__link" href="https://www.gov.uk/help">Help</a>
              </li>
              <li className="govuk-footer__inline-list-item">
                <a
                  className="govuk-footer__link"
                  href="https://www.gov.uk/help/privacy-notice"
                >
                  Privacy
                </a>
              </li>
              <li className="govuk-footer__inline-list-item">
                <a
                  className="govuk-footer__link"
                  href="https://www.gov.uk/help/cookie-details"
                >
                  Cookies
                </a>
              </li>
              <li className="govuk-footer__inline-list-item">
                <a className="govuk-footer__link" href="https://www.gov.uk/contact">
                  Contact
                </a>
              </li>
              <li className="govuk-footer__inline-list-item">
                <a
                  className="govuk-footer__link"
                  href="https://www.gov.uk/help/terms-conditions"
                >
                  Terms and conditions
                </a>
              </li>
              <li className="govuk-footer__inline-list-item">
                <Link className="govuk-footer__link" to="/accessibility-statement">
                  Accessibility statement
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
}

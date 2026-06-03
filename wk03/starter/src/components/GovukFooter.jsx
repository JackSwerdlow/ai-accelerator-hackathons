/**
 * GOV.UK footer chrome. Lists the in-app accessibility statement (via
 * react-router <Link>) and a placeholder cookies anchor per PLAN.md
 * §10 / content plan §10.
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
                <Link className="govuk-footer__link" to="/accessibility-statement">
                  Accessibility statement
                </Link>
              </li>
              <li className="govuk-footer__inline-list-item">
                <a className="govuk-footer__link" href="#">Cookies</a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
}

/**
 * Accessibility statement page (route "/accessibility-statement").
 * Covers the 8 PSBAR sections from research §7 with values from
 * content plan §9.
 */
import { useEffect } from "react";
import { Link } from "react-router-dom";

/**
 * Renders the eight PSBAR-required accessibility statement sections
 * plus an optional improvement-plan section.
 *
 * @returns {JSX.Element}
 */
export default function AccessibilityStatementPage() {
  useEffect(() => {
    document.title = "Accessibility statement - Green Home Grant - GOV.UK";
  }, []);

  return (
    <>
      <Link to="/" className="govuk-back-link">Back</Link>

      <h1 className="govuk-heading-xl">Accessibility statement for the Green Home Grant eligibility checker</h1>

      {/* 1. Intro */}
      <p className="govuk-body">
        This statement applies to the Green Home Grant eligibility checker. It is run by the Green Home Grant
        scheme administrator. We want as many people as possible to be able to use this service.
      </p>

      {/* 2. How accessible this website is */}
      <h2 className="govuk-heading-l">How accessible this website is</h2>
      <p className="govuk-body">
        We are not aware of any accessibility issues with this service at the time of writing. This statement
        will be updated after the first independent accessibility audit.
      </p>

      {/* 3. Feedback and contact information */}
      <h2 className="govuk-heading-l">Feedback and contact information</h2>
      <p className="govuk-body">
        If you find any accessibility problems, or need information on this service in a different format such
        as accessible PDF, large print, easy read, audio recording, or braille:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>email <a className="govuk-link" href="mailto:accessibility@greengrant.gov.uk">accessibility@greengrant.gov.uk</a></li>
        <li>we will consider your request and respond within 10 working days</li>
      </ul>

      {/* 4. Reporting accessibility problems */}
      <h2 className="govuk-heading-l">Reporting accessibility problems with this website</h2>
      <p className="govuk-body">
        We are always looking to improve the accessibility of this service. If you find any problems that are
        not listed on this page, or think we are not meeting accessibility requirements, please contact us at
        the email above.
      </p>

      {/* 5. Enforcement procedure */}
      <h2 className="govuk-heading-l">Enforcement procedure</h2>
      <p className="govuk-body">
        The Equality and Human Rights Commission (EHRC) is responsible for enforcing the Public Sector
        Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018 (the "accessibility
        regulations"). If you are not happy with how we respond to your complaint,{" "}
        <a className="govuk-link" href="https://www.equalityadvisoryservice.com/">contact the Equality Advisory and Support Service (EASS)</a>.
      </p>

      {/* 6. Technical information */}
      <h2 className="govuk-heading-l">Technical information about this website's accessibility</h2>
      <p className="govuk-body">
        The Green Home Grant scheme administrator is committed to making this service accessible, in
        accordance with the Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility
        Regulations 2018.
      </p>
      <p className="govuk-body">
        This service is partially compliant with the{" "}
        <a className="govuk-link" href="https://www.w3.org/TR/WCAG22/">Web Content Accessibility Guidelines version 2.2 AA standard</a>,
        because compliance has not yet been independently audited.
      </p>

      {/* 7. Non-accessible content */}
      <h2 className="govuk-heading-l">Non-accessible content</h2>
      <p className="govuk-body">
        We are not aware of any non-accessible content at this time. The list will be updated after the first
        independent accessibility audit.
      </p>

      {/* 8. Preparation of this statement */}
      <h2 className="govuk-heading-l">Preparation of this accessibility statement</h2>
      <p className="govuk-body">This statement was prepared on 3 June 2026. It was last reviewed on 3 June 2026.</p>
      <p className="govuk-body">
        This service was last tested in June 2026 against the WCAG 2.2 AA standard. The test was carried out
        internally. The next test is due after the first independent accessibility audit.
      </p>

      {/* Optional: What we are doing to improve */}
      <h2 className="govuk-heading-l">What we are doing to improve accessibility</h2>
      <p className="govuk-body">
        We will commission an independent accessibility audit before the service moves to public beta. Any
        issues identified will be tracked and prioritised based on user impact.
      </p>
    </>
  );
}

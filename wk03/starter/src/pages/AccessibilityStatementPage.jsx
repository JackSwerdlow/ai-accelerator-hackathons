import { useEffect } from 'react';
import { Link } from 'react-router-dom';

/**
 * GOV.UK accessibility statement page for the Green Home Grant
 * eligibility checker. Structured to the eight sections of the
 * GOV.UK model accessibility statement (PSBAR 2018), populated with
 * the values from the content plan.
 *
 * Reachable from the footer; no back link (the user may have arrived
 * from any page).
 */
export default function AccessibilityStatementPage() {
  useEffect(() => {
    document.title = 'Accessibility statement - Green Home Grant - GOV.UK';
  }, []);

  return (
    <>
      <h1 className="govuk-heading-xl">Accessibility statement for the Green Home Grant eligibility checker</h1>

      <p className="govuk-body">
        This accessibility statement applies to the Green Home Grant
        eligibility checker. This is a prototype service and the content
        below uses placeholder details.
      </p>

      <h2 className="govuk-heading-l">How accessible this website is</h2>
      <p className="govuk-body">
        We are working to make this service fully accessible. At the
        time of writing, no specific accessibility issues have been
        identified, but the service has not yet been independently
        audited.
      </p>

      <h2 className="govuk-heading-l">Feedback and contact information</h2>
      <p className="govuk-body">
        If you find any accessibility problems with this service, or
        you need information on this website in a different format
        such as accessible PDF, large print, easy read, audio
        recording or braille, contact us at{' '}
        <a className="govuk-link" href="mailto:accessibility@greengrant.gov.uk">accessibility@greengrant.gov.uk</a>.
      </p>
      <p className="govuk-body">We will consider your request and reply within 5 working days.</p>

      <h2 className="govuk-heading-l">Reporting accessibility problems with this website</h2>
      <p className="govuk-body">
        We are always looking to improve the accessibility of this
        service. If you find any problems not listed on this page, or
        you think we are not meeting accessibility requirements,
        contact us using the email above.
      </p>

      <h2 className="govuk-heading-l">Enforcement procedure</h2>
      <p className="govuk-body">
        The Equality and Human Rights Commission (EHRC) is responsible
        for enforcing the Public Sector Bodies (Websites and Mobile
        Applications) (No. 2) Accessibility Regulations 2018 (the
        "accessibility regulations"). If you are not happy with how we
        respond to your complaint, contact the{' '}
        <a className="govuk-link" href="https://www.equalityadvisoryservice.com/">Equality Advisory and Support Service (EASS)</a>.
      </p>

      <h2 className="govuk-heading-l">Technical information about this website's accessibility</h2>
      <p className="govuk-body">
        We are committed to making this website accessible, in
        accordance with the accessibility regulations.
      </p>
      <p className="govuk-body">
        This website is partially compliant with the{' '}
        <a className="govuk-link" href="https://www.w3.org/TR/WCAG22/">Web Content Accessibility Guidelines version 2.2</a>{' '}
        AA standard, due to the non-compliances and exemptions listed below.
      </p>

      <h2 className="govuk-heading-l">Non-accessible content</h2>
      <p className="govuk-body">
        The content listed below is non-accessible for the following
        reasons. None have been identified at the time of writing —
        this section will be updated after an accessibility audit.
      </p>

      <h2 className="govuk-heading-l">Preparation of this accessibility statement</h2>
      <p className="govuk-body">
        This statement was prepared on 3 June 2026. It was last
        reviewed on 3 June 2026. This website was last tested on 3
        June 2026 against the WCAG 2.2 AA standard. The test was
        carried out by the project team.
      </p>

      <p className="govuk-body">
        <Link className="govuk-link" to="/">Return to the start of the service</Link>
      </p>
    </>
  );
}

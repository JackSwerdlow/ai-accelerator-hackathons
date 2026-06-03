export default function AccessibilityStatementPage() {
  return (
    <main className="govuk-main-wrapper" id="main-content">
      <h1 className="govuk-heading-xl">Accessibility statement</h1>
      {/* TODO: Service name and scope */}
      <h2 className="govuk-heading-l">How accessible this service is</h2>
      {/* TODO: Known non-compliances */}
      <h2 className="govuk-heading-l">Feedback and contact information</h2>
      {/* TODO: Reasonable adjustment contact */}
      <h2 className="govuk-heading-l">Technical information</h2>
      <p className="govuk-body">This service is partially compliant with WCAG 2.2 AA.</p>
      {/* TODO: Non-compliance list */}
      <h2 className="govuk-heading-l">How we tested this service</h2>
      {/* TODO: Testing methodology */}
      <h2 className="govuk-heading-l">What we are doing to improve</h2>
      {/* TODO: Improvement plan */}
    </main>
  );
}

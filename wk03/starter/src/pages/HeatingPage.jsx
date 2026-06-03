// TODO: Import useNavigate from react-router-dom

function HeatingPage() {
  // TODO: Read current value from form state
  // TODO: Add validation and error handling
  // TODO: On "Continue", save answer and navigate to /check-answers

  return (
    <>
      <a href="/insulation" className="govuk-back-link">Back</a>
      <h1 className="govuk-heading-l">What is your main heating system?</h1>
      {/* TODO: Add radio buttons for: Gas boiler, Oil boiler, Electric heating, Heat pump, Other */}
      {/* TODO: Add a Continue button */}
    </>
  );
}

export default HeatingPage;

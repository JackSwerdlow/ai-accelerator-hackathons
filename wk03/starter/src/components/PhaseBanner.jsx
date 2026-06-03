export default function PhaseBanner({ phase = 'alpha', feedbackHref = '#' }) {
  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">{phase}</strong>
        <span className="govuk-phase-banner__text">
          This is a new service – your <a className="govuk-link" href={feedbackHref}>feedback</a> will help us improve it.
        </span>
      </p>
    </div>
  );
}

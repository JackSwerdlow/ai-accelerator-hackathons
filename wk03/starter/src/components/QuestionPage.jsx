import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useFormContext } from '../contexts/FormContext';
import ErrorSummary from './ErrorSummary';
import ProgressIndicator from './ProgressIndicator';
import GovukButton from './GovukButton';

/**
 * Generic GOV.UK-styled single-question page used by all five question
 * routes in the Green Home Grant checker flow. Renders a back link, step
 * indicator, an optional error summary, a fieldset of radio options, an
 * optional Tier-2 collapsible help block, and a Continue button.
 *
 * Must be rendered inside a <FormProvider> (for answers state) and inside
 * a react-router <Router> (for <Link>, useNavigate, and useSearchParams).
 *
 * @param {object} props
 * @param {string} props.pageTitle - Question heading; also drives document.title.
 * @param {('propertyType'|'ownership'|'incomeBand'|'insulation'|'heating')} props.fieldName - Key in FormContext.answers.
 * @param {number} props.step - Current step number (1-5).
 * @param {number} props.totalSteps - Total steps (always 5 for this flow).
 * @param {Array<{ value: string, label: string }>} props.options - Radio options.
 * @param {string} [props.hint] - Optional plain-text hint under the legend.
 * @param {{ summaryText: string, bodyText: string }} [props.helpDetails] - Optional Tier-2 help block.
 * @param {string} props.errorMessage - Message shown in summary + inline on validation failure.
 * @param {string} props.backHref - react-router path for the back link.
 * @param {string} props.onContinueNavigateTo - react-router path for the next question.
 * @returns {JSX.Element}
 */
export default function QuestionPage({
  pageTitle,
  fieldName,
  step,
  totalSteps,
  options,
  hint,
  helpDetails,
  errorMessage,
  backHref,
  onContinueNavigateTo,
}) {
  const { answers, setAnswer } = useFormContext();
  const [hasError, setHasError] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const base = `${pageTitle} - Green Home Grant - GOV.UK`;
    document.title = hasError ? `Error: ${base}` : base;
  }, [pageTitle, hasError]);

  const describedByIds = [];
  if (hint) describedByIds.push(`${fieldName}-hint`);
  if (hasError) describedByIds.push(`${fieldName}-error`);
  const describedBy = describedByIds.join(' ');

  const handleContinue = () => {
    if (answers[fieldName] === '') {
      setHasError(true);
      return;
    }
    if (searchParams.get('from') === 'check-answers') {
      navigate('/check-answers');
    } else {
      navigate(onContinueNavigateTo);
    }
  };

  return (
    <>
      <Link to={backHref} className="govuk-back-link">Back</Link>

      <ProgressIndicator current={step} total={totalSteps} />

      {hasError && (
        <ErrorSummary firstFieldId={`${fieldName}-1`} message={errorMessage} />
      )}

      <div className={`govuk-form-group${hasError ? ' govuk-form-group--error' : ''}`}>
        <fieldset className="govuk-fieldset" aria-describedby={describedBy || undefined}>
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
            <h1 className="govuk-fieldset__heading">{pageTitle}</h1>
          </legend>

          {hint && (
            <div id={`${fieldName}-hint`} className="govuk-hint">{hint}</div>
          )}

          {hasError && (
            <p id={`${fieldName}-error`} className="govuk-error-message">
              <span className="govuk-visually-hidden">Error:</span> {errorMessage}
            </p>
          )}

          <div className="govuk-radios">
            {options.map((opt, i) => (
              <div className="govuk-radios__item" key={opt.value}>
                <input
                  className="govuk-radios__input"
                  id={`${fieldName}-${i + 1}`}
                  name={fieldName}
                  type="radio"
                  value={opt.value}
                  checked={answers[fieldName] === opt.value}
                  onChange={() => {
                    setAnswer(fieldName, opt.value);
                    if (hasError) setHasError(false);
                  }}
                />
                <label className="govuk-radios__label" htmlFor={`${fieldName}-${i + 1}`}>
                  {opt.label}
                </label>
              </div>
            ))}
          </div>
        </fieldset>
      </div>

      {helpDetails && (
        <details className="govuk-details">
          <summary className="govuk-details__summary">
            <span className="govuk-details__summary-text">{helpDetails.summaryText}</span>
          </summary>
          <div className="govuk-details__text">{helpDetails.bodyText}</div>
        </details>
      )}

      <GovukButton onClick={handleContinue}>Continue</GovukButton>
    </>
  );
}

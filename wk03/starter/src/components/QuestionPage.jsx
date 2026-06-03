/**
 * Reusable GOV.UK question page. Renders the back link, progress
 * indicator, optional error summary, fieldset with radios, optional
 * help-details block, and a Continue button. Five page wrappers
 * (PropertyType / Ownership / Income / Insulation / Heating) feed
 * it props per PLAN.md §4.4 + §6.1.
 */
import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useFormContext } from '../contexts/FormContext';
import ProgressIndicator from './ProgressIndicator';
import ErrorSummary from './ErrorSummary';
import GovukButton from './GovukButton';

/**
 * Render a single GOV.UK radio-group question page.
 *
 * `backHref`, `totalSteps`, and `onContinueNavigateTo` accept either a plain
 * value or a function of the current answers. The function form is used at the
 * tenure branch points so the same generic page can route owners and tenants
 * differently (content plan §11).
 *
 * @param {{
 *   pageTitle: string,
 *   fieldName: string,
 *   step: number,
 *   totalSteps: number | ((answers: object) => number),
 *   options: { value: string, label: string }[],
 *   hint?: string,
 *   helpDetails?: { summaryText: string, bodyText: string },
 *   errorMessage: string,
 *   backHref: string | ((answers: object) => string),
 *   onContinueNavigateTo: string | ((answers: object) => string),
 * }} props
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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [hasError, setHasError] = useState(false);

  // Resolve a value-or-function prop against the live answers (used by the
  // tenure branch points — see component JSDoc / content plan §11).
  const resolve = (value) => (typeof value === 'function' ? value(answers) : value);

  useEffect(() => {
    const base = `${pageTitle} - Green Home Grant - GOV.UK`;
    document.title = hasError ? `Error: ${base}` : base;
  }, [pageTitle, hasError]);

  const describedByIds = [
    hint ? `${fieldName}-hint` : null,
    hasError ? `${fieldName}-error` : null,
  ]
    .filter(Boolean)
    .join(' ');

  const handleContinue = () => {
    if (!answers[fieldName]) {
      setHasError(true);
      return;
    }
    const fromCheckAnswers = searchParams.get('from') === 'check-answers';
    navigate(fromCheckAnswers ? '/check-answers' : resolve(onContinueNavigateTo));
  };

  const fieldsetProps = describedByIds ? { 'aria-describedby': describedByIds } : {};

  return (
    <>
      <Link to={resolve(backHref)} className="govuk-back-link">
        Back
      </Link>

      <ProgressIndicator current={step} total={resolve(totalSteps)} />

      {hasError && (
        <ErrorSummary firstFieldId={`${fieldName}-1`} message={errorMessage} />
      )}

      <div className={`govuk-form-group${hasError ? ' govuk-form-group--error' : ''}`}>
        <fieldset className="govuk-fieldset" {...fieldsetProps}>
          <legend className="govuk-fieldset__legend govuk-fieldset__legend--l">
            <h1 className="govuk-fieldset__heading">{pageTitle}</h1>
          </legend>

          {hint && (
            <div id={`${fieldName}-hint`} className="govuk-hint">
              {hint}
            </div>
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
                  onChange={() => setAnswer(fieldName, opt.value)}
                />
                <label
                  className="govuk-radios__label"
                  htmlFor={`${fieldName}-${i + 1}`}
                >
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

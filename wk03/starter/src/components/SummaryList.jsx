/**
 * GOV.UK summary list for the check-your-answers page.
 * Each "Change" link is a react-router <Link> so that navigation
 * back to a question preserves FormContext state.
 */
import { Link } from 'react-router-dom';

/**
 * Render a GOV.UK summary list from a rows array.
 *
 * @param {{ rows: { key: string, value: string, changeHref: string, changeHiddenText: string }[] }} props
 * @returns {JSX.Element}
 */
export default function SummaryList({ rows }) {
  return (
    <dl className="govuk-summary-list">
      {rows.map((row) => (
        <div key={row.key} className="govuk-summary-list__row">
          <dt className="govuk-summary-list__key">{row.key}</dt>
          <dd className="govuk-summary-list__value">{row.value}</dd>
          <dd className="govuk-summary-list__actions">
            <Link className="govuk-link" to={row.changeHref}>
              Change<span className="govuk-visually-hidden"> {row.changeHiddenText}</span>
            </Link>
          </dd>
        </div>
      ))}
    </dl>
  );
}

import { Link } from "react-router-dom";

/**
 * GOV.UK summary list. Used on the check-your-answers page.
 * Each row has a key/value pair and a Change link that returns to the
 * relevant question with `?from=check-answers` appended.
 *
 * @param {{ rows: Array<{ key: string, value: string, changeHref: string, changeHiddenText: string }> }} props
 */
export default function SummaryList({ rows }) {
  return (
    <dl className="govuk-summary-list">
      {rows.map((row) => (
        <div className="govuk-summary-list__row" key={row.key}>
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

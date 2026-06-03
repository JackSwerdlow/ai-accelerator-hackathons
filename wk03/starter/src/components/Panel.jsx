/**
 * GOV.UK result panel. Thin wrapper that picks the right modifier
 * class based on the outcome. No interactive elements live inside —
 * buttons and links go below the panel per PLAN.md §8.1.
 */

/**
 * Render the GOV.UK panel for an eligibility outcome.
 *
 * @param {{ outcome: 'eligible' | 'partial' | 'ineligible', title: string, body?: string }} props
 * @returns {JSX.Element}
 */
export default function Panel({ outcome, title, body }) {
  const modifier =
    outcome === 'ineligible' ? 'govuk-panel--not-eligible' : 'govuk-panel--confirmation';
  return (
    <div className={`govuk-panel ${modifier}`}>
      <h1 className="govuk-panel__title">{title}</h1>
      {body && <div className="govuk-panel__body">{body}</div>}
    </div>
  );
}

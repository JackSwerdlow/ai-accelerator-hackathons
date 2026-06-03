/**
 * GOV.UK result-page panel. Shown at the top of an outcome page to
 * communicate the result of a check (eligible, partially eligible, or
 * ineligible). Renders the confirmation variant for eligible/partial
 * outcomes and a "not eligible" variant for ineligible outcomes.
 *
 * No interactive elements (buttons, links) belong inside the panel —
 * follow-on actions should appear below it.
 *
 * @param {{ outcome: ("eligible" | "partial" | "ineligible"), title: string, body?: string }} props
 */
export default function Panel({ outcome, title, body }) {
  const isNotEligible = outcome === "ineligible";
  const className = `govuk-panel ${isNotEligible ? "govuk-panel--not-eligible" : "govuk-panel--confirmation"}`;
  return (
    <div className={className}>
      <h1 className="govuk-panel__title">{title}</h1>
      {body && <div className="govuk-panel__body">{body}</div>}
    </div>
  );
}

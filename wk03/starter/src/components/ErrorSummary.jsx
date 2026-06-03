import { useEffect, useRef } from "react";

/**
 * GOV.UK error summary. Focuses itself on mount so the keyboard user
 * lands at the top of the page and screen readers announce the heading
 * + error link. Uses focus rather than role="alert" — focusing a live
 * region can cause double-announcement in NVDA/JAWS.
 *
 * @param {{ firstFieldId: string, message: string }} props
 */
export default function ErrorSummary({ firstFieldId, message }) {
  const ref = useRef(null);
  useEffect(() => { ref.current?.focus(); }, []);
  return (
    <div
      ref={ref}
      className="govuk-error-summary"
      tabIndex={-1}
      aria-labelledby="error-summary-title"
    >
      <h2 id="error-summary-title" className="govuk-error-summary__title">
        There is a problem
      </h2>
      <div className="govuk-error-summary__body">
        <ul className="govuk-error-summary__list">
          <li><a href={`#${firstFieldId}`}>{message}</a></li>
        </ul>
      </div>
    </div>
  );
}

/**
 * Presentational pill showing how closely a suggested service matched the
 * user's query. The colour band signals confidence so people can judge a
 * match at a glance. Thresholds are shared with HelpEntryPage (PLAN.md §16).
 */

// Shared confidence thresholds — MUST match HelpEntryPage (PLAN.md §16).
const HIGH_CONFIDENCE = 0.55;
const MEDIUM_CONFIDENCE = 0.4;

/**
 * Render a similarity badge for a match score.
 *
 * @param {{ score: number }} props - score is a number in [0, 1].
 * @returns {JSX.Element} A span pill with the rounded percentage and a band modifier.
 */
export default function SimilarityBadge({ score }) {
  const modifier =
    score >= HIGH_CONFIDENCE ? "high" : score >= MEDIUM_CONFIDENCE ? "medium" : "low";
  const className = `app-similarity-badge app-similarity-badge--${modifier}`;
  return <span className={className}>{Math.round(score * 100)}% match</span>;
}

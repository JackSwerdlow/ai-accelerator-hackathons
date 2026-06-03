/**
 * Step-of-N progress indicator for the question journey.
 * Custom component (not a GOV.UK Design System pattern) — the
 * app-step-indicator class is deliberately app-prefixed.
 */

/**
 * Render a plain "Step X of Y" indicator above each question H1.
 *
 * @param {{ current: number, total: number }} props
 * @returns {JSX.Element}
 */
export default function ProgressIndicator({ current, total }) {
  return (
    <p className="app-step-indicator" aria-label={`Step ${current} of ${total}`}>
      Step {current} of {total}
    </p>
  );
}

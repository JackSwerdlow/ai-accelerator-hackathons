/**
 * Plain-text step indicator for multi-step flows ("Step 2 of 5").
 *
 * Note: this is a CUSTOM app component, not a GOV.UK Design System
 * pattern. The GOV.UK service manual recommends against numbered
 * progress bars for linear journeys, so this is a minimal text-only
 * alternative with an accessible label.
 *
 * @param {{ current: number, total: number }} props
 */
export default function ProgressIndicator({ current, total }) {
  return (
    <p className="app-step-indicator" aria-label={`Step ${current} of ${total}`}>
      Step {current} of {total}
    </p>
  );
}

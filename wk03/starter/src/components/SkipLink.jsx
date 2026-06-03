/**
 * GOV.UK skip link. Renders a same-page anchor that lets keyboard
 * and screen reader users jump straight to the main content,
 * bypassing the header/navigation.
 *
 * This is intentionally a plain <a> rather than a react-router Link
 * because it is an in-page anchor, not a route change.
 */
export default function SkipLink() {
  return (
    <a href="#main-content" className="govuk-skip-link">
      Skip to main content
    </a>
  );
}

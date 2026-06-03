/**
 * GOV.UK skip link. Same-page anchor to #main-content so keyboard
 * users can bypass the header and phase banner. Plain <a>, not a
 * react-router <Link>, because the href is a hash not a route.
 */

/**
 * Renders the GOV.UK skip-to-main-content link.
 *
 * @returns {JSX.Element}
 */
export default function SkipLink() {
  return (
    <a href="#main-content" className="govuk-skip-link">
      Skip to main content
    </a>
  );
}

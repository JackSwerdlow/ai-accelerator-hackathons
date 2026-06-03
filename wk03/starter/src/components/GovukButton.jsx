/**
 * GOV.UK button. Supports a "start" variant that adds the start-button
 * chevron SVG per PLAN.md §8.2. The SVG is aria-hidden + focusable=false
 * so assistive tech ignores the icon and keyboard tab order skips it.
 */

/**
 * Renders a GOV.UK button with optional start-variant chevron.
 *
 * @param {{
 *   children: React.ReactNode,
 *   onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void,
 *   type?: 'button' | 'submit' | 'reset',
 *   variant?: '' | 'start'
 * }} props
 * @returns {JSX.Element}
 */
export default function GovukButton({ children, onClick, type = "button", variant = "" }) {
  const className = `govuk-button${variant === "start" ? " govuk-button--start" : ""}`;
  return (
    <button type={type} className={className} onClick={onClick}>
      {children}
      {variant === "start" && (
        <svg
          className="govuk-button__start-icon"
          xmlns="http://www.w3.org/2000/svg"
          width="17.5"
          height="19"
          viewBox="0 0 33 40"
          aria-hidden="true"
          focusable="false"
        >
          <path fill="currentColor" d="M0 0h13l20 20-20 20H0l20-20z" />
        </svg>
      )}
    </button>
  );
}

function GovukButton({ children, onClick, type = 'button', variant = '' }) {
  const className = `govuk-button ${variant === 'start' ? 'govuk-button--start' : ''}`.trim();

  return (
    <button type={type} className={className} onClick={onClick}>
      {children}
    </button>
  );
}

export default GovukButton;

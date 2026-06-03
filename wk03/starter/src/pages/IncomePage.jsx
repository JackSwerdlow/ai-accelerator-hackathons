import QuestionPage from '../components/QuestionPage';

/**
 * Question 3: Annual household income band.
 * Thin wrapper around QuestionPage; copy and options come from the
 * content plan (`docs/plans/2026-06-03-content-plan.md` §3).
 */
export default function IncomePage() {
  return (
    <QuestionPage
      pageTitle="What is your total annual household income?"
      fieldName="incomeBand"
      step={3}
      totalSteps={5}
      options={[
        { value: 'low', label: 'Under £31,000' },
        { value: 'mid', label: '£31,000 to £60,000' },
        { value: 'high', label: 'Over £60,000' },
      ]}
      hint="Include the income of all adults living in your home, before tax and other deductions."
      helpDetails={{
        summaryText: 'Help with annual household income',
        bodyText:
          'Include earnings from employment, self-employment, pensions, rental income, and benefits. Do not include one-off payments like inheritance or lottery winnings.',
      }}
      errorMessage="Select your annual household income"
      backHref="/ownership"
      onContinueNavigateTo="/insulation"
    />
  );
}

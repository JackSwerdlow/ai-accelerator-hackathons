import QuestionPage from '../components/QuestionPage';

/**
 * Question 5: Current main heating system.
 * Thin wrapper around QuestionPage; copy and options come from the
 * content plan (`docs/plans/2026-06-03-content-plan.md` §3).
 */
export default function HeatingPage() {
  return (
    <QuestionPage
      pageTitle="What is your current main heating system?"
      fieldName="heating"
      step={5}
      totalSteps={5}
      options={[
        { value: 'gas-boiler', label: 'Gas boiler' },
        { value: 'oil-boiler', label: 'Oil boiler' },
        { value: 'electric-storage', label: 'Electric storage heaters' },
        { value: 'heat-pump', label: 'Heat pump (air source or ground source)' },
        { value: 'other', label: 'Other' },
      ]}
      hint="Select the system that heats most of your home."
      helpDetails={{
        summaryText: "What counts as 'Other'?",
        bodyText:
          "Choose 'Other' if your home uses a heating system not listed above, such as a biomass boiler, district heating, solid-fuel stove, or LPG. The check will not change the grant you qualify for, but our installer will follow up to assess what is suitable.",
      }}
      errorMessage="Select your current main heating system"
      backHref="/insulation"
      onContinueNavigateTo="/check-answers"
    />
  );
}

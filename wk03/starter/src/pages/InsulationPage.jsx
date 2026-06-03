import QuestionPage from '../components/QuestionPage';

/**
 * Question 4: Current home insulation.
 * Thin wrapper around QuestionPage; copy and options come from the
 * content plan (`docs/plans/2026-06-03-content-plan.md` §3).
 */
export default function InsulationPage() {
  return (
    <QuestionPage
      pageTitle="What insulation does your home currently have?"
      fieldName="insulation"
      step={4}
      totalSteps={5}
      options={[
        { value: 'none', label: 'No insulation' },
        { value: 'partial', label: 'Some insulation (for example, loft only or walls only)' },
        { value: 'full', label: 'Full insulation (loft and walls)' },
      ]}
      hint="If you are not sure, check your Energy Performance Certificate (EPC). Your landlord or mortgage provider may have a copy."
      helpDetails={{
        summaryText: 'Help with checking your insulation',
        bodyText:
          'Loft insulation usually sits between the joists in your loft and is at least 100mm thick. Wall insulation may be inside the cavity (for homes built after 1920) or fitted to the inside or outside of solid walls. If you have an Energy Performance Certificate (EPC), it lists what insulation has been recorded for your home.',
      }}
      errorMessage="Select the insulation your home currently has"
      backHref="/income"
      onContinueNavigateTo="/heating"
    />
  );
}

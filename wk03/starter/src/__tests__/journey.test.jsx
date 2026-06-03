/**
 * End-to-end journey tests through the real router, pages, context, and
 * guards (jsdom). These drive the tenure branch the way a user would —
 * clicking radios and Continue — to verify the wiring the unit tests cannot:
 * function-valued routing at the branch points, the path-aware check-answers
 * summary, and the tenant-specific result copy (content plan §11).
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { FormProvider } from '../contexts/FormContext';
import AppRoutes from '../router';

function renderJourney(initialEntries = ['/property-type']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <FormProvider>
        <AppRoutes />
      </FormProvider>
    </MemoryRouter>
  );
}

const continueBtn = () => screen.getByRole('button', { name: 'Continue' });

describe('tenant journey', () => {
  it('routes a private renter through landlord consent and insulation to a partial/renter result', async () => {
    const user = userEvent.setup();
    renderJourney();

    // Q1 property type
    await user.click(screen.getByLabelText('Flat or apartment'));
    await user.click(continueBtn());

    // Q2 ownership — choosing a renter switches the step counter to "of 4"
    await user.click(screen.getByLabelText('I rent from a private landlord'));
    expect(screen.getByText('Step 2 of 4')).toBeInTheDocument();
    await user.click(continueBtn());

    // Tenant-only question appears (proves the branch routed to /landlord-consent)
    expect(
      screen.getByRole('heading', {
        name: /Do you have your landlord's permission/i,
      })
    ).toBeInTheDocument();
    await user.click(screen.getByLabelText('Yes'));
    await user.click(continueBtn());

    // Insulation — tenant path; Continue should jump straight to check-answers
    await user.click(screen.getByLabelText(/Some insulation/));
    await user.click(continueBtn());

    // Check-answers: tenant rows only, no income/heating
    expect(screen.getByRole('heading', { name: 'Check your answers' })).toBeInTheDocument();
    const summary = document.querySelector('.govuk-summary-list');
    const keys = Array.from(summary.querySelectorAll('.govuk-summary-list__key')).map((n) => n.textContent);
    expect(keys).toEqual([
      'Property type',
      'Ownership status',
      "Landlord's permission",
      'Current insulation',
    ]);
    expect(keys).not.toContain('Annual household income');
    expect(keys).not.toContain('Current heating system');

    // Submit → result
    await user.click(screen.getByRole('button', { name: 'Submit and see result' }));
    expect(
      screen.getByText('You may be partially eligible for a Green Home Grant')
    ).toBeInTheDocument();
    expect(
      screen.getByText(/your landlord needs to apply for this grant on your behalf/i)
    ).toBeInTheDocument();
    // insulation question fed the indicative measures list
    expect(screen.getByText(/the following measures may be available/i)).toBeInTheDocument();
  });

  it('shows the no-landlord-consent ineligible result when permission is "No"', async () => {
    const user = userEvent.setup();
    renderJourney();

    await user.click(screen.getByLabelText('Terraced house'));
    await user.click(continueBtn());
    await user.click(screen.getByLabelText('I rent from a council or local authority'));
    await user.click(continueBtn());
    await user.click(screen.getByLabelText('No'));
    await user.click(continueBtn());
    await user.click(screen.getByLabelText('No insulation'));
    await user.click(continueBtn());
    await user.click(screen.getByRole('button', { name: 'Submit and see result' }));

    expect(
      screen.getByText('You are not eligible for a Green Home Grant')
    ).toBeInTheDocument();
    expect(
      screen.getByText(/do not have your landlord's permission/i)
    ).toBeInTheDocument();
  });
});

describe('owner journey still works', () => {
  it('routes an owner through income/insulation/heating to an eligible result', async () => {
    const user = userEvent.setup();
    renderJourney();

    await user.click(screen.getByLabelText('Detached house'));
    await user.click(continueBtn());
    await user.click(screen.getByLabelText('I own my home'));
    expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();
    await user.click(continueBtn());

    // Owner-only income question
    await user.click(screen.getByLabelText('Under £31,000'));
    await user.click(continueBtn());
    await user.click(screen.getByLabelText(/No insulation/));
    await user.click(continueBtn());
    // Owner reaches the heating question (tenant would have skipped it)
    expect(
      screen.getByRole('heading', { name: /current main heating system/i })
    ).toBeInTheDocument();
    await user.click(screen.getByLabelText('Gas boiler'));
    await user.click(continueBtn());

    await user.click(screen.getByRole('button', { name: 'Submit and see result' }));
    expect(
      screen.getByText('You may be eligible for a Green Home Grant')
    ).toBeInTheDocument();
  });
});

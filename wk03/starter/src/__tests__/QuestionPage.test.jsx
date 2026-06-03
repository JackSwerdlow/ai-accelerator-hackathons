/**
 * Tests for <QuestionPage>: rendering, validation, focus, pre-check,
 * and the ?from=check-answers navigation override.
 */
import { useEffect } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { FormProvider, useFormContext } from '../contexts/FormContext';
import QuestionPage from '../components/QuestionPage';

const OPTIONS = [
  { value: 'detached', label: 'Detached house' },
  { value: 'flat', label: 'Flat or apartment' },
];

const BASE_PROPS = {
  pageTitle: 'What type of property do you live in?',
  fieldName: 'propertyType',
  step: 1,
  totalSteps: 5,
  options: OPTIONS,
  errorMessage: 'Select the type of property you live in',
  backHref: '/',
  onContinueNavigateTo: '/ownership',
};

function LocationProbe() {
  const loc = useLocation();
  return <div data-testid="location">{loc.pathname}</div>;
}

function renderWithProviders(ui, { initialEntries = ['/property-type'] } = {}) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <FormProvider>
        {ui}
        <LocationProbe />
      </FormProvider>
    </MemoryRouter>
  );
}

describe('QuestionPage', () => {
  it('1. renders all radio options from the options prop', () => {
    renderWithProviders(<QuestionPage {...BASE_PROPS} />);
    const radios = screen.getAllByRole('radio');
    expect(radios).toHaveLength(2);
    expect(screen.getByLabelText('Detached house')).toBeInTheDocument();
    expect(screen.getByLabelText('Flat or apartment')).toBeInTheDocument();
  });

  it('2. clicking Continue with no selection shows the error summary and inline error', async () => {
    const user = userEvent.setup();
    renderWithProviders(<QuestionPage {...BASE_PROPS} />);
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    expect(screen.getByText('There is a problem')).toBeInTheDocument();
    const inlineErrors = screen.getAllByText(/Select the type of property you live in/);
    // One in the error summary <a>, one in the inline <p>
    expect(inlineErrors.length).toBeGreaterThanOrEqual(2);
  });

  it('3. after error appears, the error summary is the focused element', async () => {
    const user = userEvent.setup();
    renderWithProviders(<QuestionPage {...BASE_PROPS} />);
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    const summary = screen.getByText('There is a problem').closest('.govuk-error-summary');
    expect(summary).not.toBeNull();
    expect(document.activeElement).toBe(summary);
  });

  it('4. when answers[fieldName] is non-empty, the matching radio is pre-checked on mount', () => {
    function Seed({ field, value }) {
      const { setAnswer } = useFormContext();
      // Run once on mount only. setAnswer is not memoised so listing it as a
      // dep would cause an infinite re-render loop in tests.
      useEffect(() => { setAnswer(field, value); }, []);
      return null;
    }
    render(
      <MemoryRouter initialEntries={['/property-type']}>
        <FormProvider>
          <Seed field="propertyType" value="flat" />
          <QuestionPage {...BASE_PROPS} />
        </FormProvider>
      </MemoryRouter>
    );
    expect(screen.getByLabelText('Flat or apartment')).toBeChecked();
    expect(screen.getByLabelText('Detached house')).not.toBeChecked();
  });

  it('5. when URL has ?from=check-answers, Continue navigates to /check-answers', async () => {
    const user = userEvent.setup();
    renderWithProviders(<QuestionPage {...BASE_PROPS} />, {
      initialEntries: ['/property-type?from=check-answers'],
    });
    await user.click(screen.getByLabelText('Detached house'));
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    expect(screen.getByTestId('location')).toHaveTextContent('/check-answers');
  });
});

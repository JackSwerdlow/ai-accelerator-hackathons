import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { FormProvider } from '../contexts/FormContext';
import QuestionPage from '../components/QuestionPage';

const sampleProps = {
  pageTitle: 'What type of property do you live in?',
  fieldName: 'propertyType',
  step: 1,
  totalSteps: 5,
  options: [
    { value: 'detached', label: 'Detached house' },
    { value: 'flat', label: 'Flat or apartment' },
  ],
  errorMessage: 'Select the type of property you live in',
  backHref: '/',
  onContinueNavigateTo: '/ownership',
};

function renderWithProviders(ui, { initialEntries = ['/property-type'] } = {}) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <FormProvider>
        <Routes>
          <Route path="/property-type" element={ui} />
          <Route path="/ownership" element={<div>NEXT_PAGE</div>} />
          <Route path="/check-answers" element={<div>CHECK_ANSWERS_PAGE</div>} />
        </Routes>
      </FormProvider>
    </MemoryRouter>
  );
}

describe('QuestionPage', () => {
  it('renders all radio options', () => {
    renderWithProviders(<QuestionPage {...sampleProps} />);
    expect(screen.getByLabelText('Detached house')).toBeInTheDocument();
    expect(screen.getByLabelText('Flat or apartment')).toBeInTheDocument();
  });

  it('shows the error summary and inline error when Continue is clicked with no selection', async () => {
    const user = userEvent.setup();
    renderWithProviders(<QuestionPage {...sampleProps} />);
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    expect(screen.getByText('There is a problem')).toBeInTheDocument();
    const inlineErrors = screen.getAllByText(/Select the type of property you live in/);
    expect(inlineErrors.length).toBeGreaterThanOrEqual(2);
  });

  it('focuses the error summary after it appears', async () => {
    const user = userEvent.setup();
    renderWithProviders(<QuestionPage {...sampleProps} />);
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    const summary = screen.getByLabelText('There is a problem');
    expect(document.activeElement).toBe(summary);
  });

  it('reflects the selected radio in the DOM after clicking it', async () => {
    const user = userEvent.setup();
    renderWithProviders(<QuestionPage {...sampleProps} />);
    const flatRadio = screen.getByLabelText('Flat or apartment');
    await user.click(flatRadio);
    expect(flatRadio.checked).toBe(true);
  });

  it('routes Continue to /check-answers when ?from=check-answers is present', async () => {
    const user = userEvent.setup();
    renderWithProviders(<QuestionPage {...sampleProps} />, {
      initialEntries: ['/property-type?from=check-answers'],
    });
    await user.click(screen.getByLabelText('Flat or apartment'));
    await user.click(screen.getByRole('button', { name: 'Continue' }));
    expect(screen.getByText('CHECK_ANSWERS_PAGE')).toBeInTheDocument();
  });
});

/**
 * Tests for <FeedbackPage>: the form renders its radios/textarea/button,
 * submitting with input shows the thank-you confirmation (form gone), and
 * submitting with no input still confirms (no validation required).
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import FeedbackPage from '../pages/FeedbackPage';

/**
 * Render <FeedbackPage> wrapped in a router so its <Link>s resolve.
 *
 * @returns {import('@testing-library/react').RenderResult} The render result.
 */
function renderPage() {
  return render(
    <MemoryRouter>
      <FeedbackPage />
    </MemoryRouter>
  );
}

describe('FeedbackPage', () => {
  it('1. renders the feedback form with heading, 5 radios, textarea and button', () => {
    renderPage();
    expect(
      screen.getByRole('heading', { level: 1, name: 'Give feedback on this service' })
    ).toBeInTheDocument();
    expect(screen.getAllByRole('radio')).toHaveLength(5);
    expect(
      screen.getByLabelText('How could we improve this service?')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Send feedback' })).toBeInTheDocument();
  });

  it('2. selecting a rating, typing a comment and submitting shows confirmation', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByLabelText('Very satisfied'));
    await user.type(
      screen.getByLabelText('How could we improve this service?'),
      'Make it faster'
    );
    await user.click(screen.getByRole('button', { name: 'Send feedback' }));

    expect(screen.getByText('Thank you for your feedback')).toBeInTheDocument();
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
  });

  it('3. submitting with no input still shows the thank-you confirmation', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: 'Send feedback' }));

    expect(screen.getByText('Thank you for your feedback')).toBeInTheDocument();
  });
});

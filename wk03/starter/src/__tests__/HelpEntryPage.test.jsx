/**
 * Tests for <HelpEntryPage>: mount-time matcher init, the not-ready loading
 * state, the search/results flow, empty-input guarding, the init-failure
 * fallback, and the below-threshold catalogue fallback. The intent matcher is
 * mocked so no embeddings run during tests.
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import HelpEntryPage from '../pages/HelpEntryPage';
import { SERVICE_CATALOGUE } from '../intent/catalogue';
import { initMatcher, isMatcherReady, rankIntents } from '../intent/matcher';

// Mock the matcher so no embeddings/model download happens in tests.
vi.mock('../intent/matcher', () => ({
  initMatcher: vi.fn(),
  isMatcherReady: vi.fn(),
  rankIntents: vi.fn(),
}));

/**
 * Render <HelpEntryPage> wrapped in a router so its <Link>s resolve.
 *
 * @returns {import('@testing-library/react').RenderResult} The render result.
 */
function renderPage() {
  return render(
    <MemoryRouter>
      <HelpEntryPage />
    </MemoryRouter>
  );
}

/**
 * Build a fake RankedIntent from a real catalogue id so result rendering uses
 * genuine titles/descriptions/routes.
 *
 * @param {string} id - The catalogue entry id to wrap.
 * @param {number} score - The similarity score in [0,1].
 * @returns {{ entry: import('../intent/catalogue').ServiceEntry, score: number }}
 */
function rankedFor(id, score) {
  const entry = SERVICE_CATALOGUE.find((e) => e.id === id);
  return { entry, score };
}

describe('HelpEntryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. calls initMatcher exactly once on mount', async () => {
    initMatcher.mockResolvedValue({ mode: 'embeddings' });
    renderPage();
    await waitFor(() => {
      expect(initMatcher).toHaveBeenCalledTimes(1);
    });
  });

  it('2. while not ready, shows the loading banner and a disabled submit', () => {
    // A never-resolving promise keeps the component in its not-ready state.
    initMatcher.mockReturnValue(new Promise(() => {}));
    renderPage();

    expect(screen.getByText('Preparing the assistant')).toBeInTheDocument();
    const submit = screen.getByRole('button', { name: 'Show services' });
    expect(submit).toHaveAttribute('aria-disabled', 'true');
  });

  it('3. after ready, submitting a query ranks intents and renders result cards with badges', async () => {
    initMatcher.mockResolvedValue({ mode: 'embeddings' });
    rankIntents.mockResolvedValue([
      rankedFor('green-home-grant', 0.82),
      rankedFor('apply-universal-credit', 0.61),
      rankedFor('council-tax-reduction', 0.57),
    ]);

    const user = userEvent.setup();
    renderPage();

    // Wait until init resolves so the submit handler is no longer inert.
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Show services' }))
        .toHaveAttribute('aria-disabled', 'false');
    });

    await user.type(screen.getByLabelText('Describe your situation'), 'my boiler is broken');
    await user.click(screen.getByRole('button', { name: 'Show services' }));

    await waitFor(() => {
      expect(rankIntents).toHaveBeenCalledWith('my boiler is broken', 3);
    });

    const cards = await screen.findAllByRole('listitem');
    const resultCards = cards.filter((li) => li.classList.contains('app-intent-card'));
    expect(resultCards).toHaveLength(3);

    const badges = screen.getAllByText(/% match/);
    expect(badges).toHaveLength(3);
  });

  it('4. ready with empty input does not call rankIntents', async () => {
    initMatcher.mockResolvedValue({ mode: 'embeddings' });

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Show services' }))
        .toHaveAttribute('aria-disabled', 'false');
    });

    await user.click(screen.getByRole('button', { name: 'Show services' }));
    expect(rankIntents).not.toHaveBeenCalled();
  });

  it('5. when initMatcher rejects, still renders the full Browse all services fallback', async () => {
    initMatcher.mockRejectedValue(new Error('x'));
    renderPage();

    expect(await screen.findByText('Browse all services')).toBeInTheDocument();
    // The full catalogue should be browsable even though init failed.
    expect(screen.getByRole('link', { name: 'Green Home Grant' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Renew or replace your passport' }))
      .toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Register to vote' })).toBeInTheDocument();
  });

  it('6. a below-threshold match hides result cards and shows the catalogue fallback', async () => {
    initMatcher.mockResolvedValue({ mode: 'embeddings' });
    rankIntents.mockResolvedValue([rankedFor('green-home-grant', 0.1)]);

    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Show services' }))
        .toHaveAttribute('aria-disabled', 'false');
    });

    await user.type(screen.getByLabelText('Describe your situation'), 'something vague');
    await user.click(screen.getByRole('button', { name: 'Show services' }));

    await waitFor(() => {
      expect(rankIntents).toHaveBeenCalledWith('something vague', 3);
    });

    // No result cards should render for a sub-threshold score.
    await waitFor(() => {
      expect(document.querySelector('.app-intent-card')).toBeNull();
    });
    expect(screen.getByText('Browse all services')).toBeInTheDocument();
  });
});

// Referenced only to satisfy the spec's mock shape; the component imports
// initMatcher and rankIntents directly.
void isMatcherReady;

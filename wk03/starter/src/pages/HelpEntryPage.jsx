// Free-text "what do you need help with?" page (route "/help"). It lets people
// describe their situation in plain English and uses the semantic intent matcher
// (PLAN.md §16) to suggest GOV.UK services, degrading to a browsable catalogue.

/**
 * SMOKE CHECKLIST — typing these and pressing "Show services" should surface a
 * sensible top suggestion (Green Home Grant ranks first for the heating ones):
 *   - "boiler broken"
 *   - "my house is cold"
 *   - "I can't pay my rent"
 *   - "lost my passport"
 *   - "register to vote"
 */

import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import SimilarityBadge from "../components/SimilarityBadge";
import { SERVICE_CATALOGUE } from "../intent/catalogue";
import { initMatcher, rankIntents } from "../intent/matcher";

// Shared confidence thresholds — MUST match SimilarityBadge (PLAN.md §16).
const HIGH_CONFIDENCE = 0.55;
const MEDIUM_CONFIDENCE = 0.4;
// Results scoring below this are dropped, falling back to the full catalogue.
const MIN_CONFIDENCE = 0.3;

/**
 * @typedef {{ entry: import('../intent/catalogue').ServiceEntry, score: number }} RankedIntent
 */

/**
 * Render the help-entry page: a free-text intent search backed by the semantic
 * matcher, with a full-catalogue fallback for cold loads, weak matches, or when
 * the embeddings backend is unavailable.
 *
 * @returns {JSX.Element} The help-entry page.
 */
export default function HelpEntryPage() {
  const [query, setQuery] = useState("");
  /** @type {[RankedIntent[]|null, Function]} */
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [ready, setReady] = useState(false);
  const [mode, setMode] = useState(null);
  const [showAll, setShowAll] = useState(false);

  // Guards the mount effect so it runs once even under StrictMode double-invoke.
  const didInitRef = useRef(false);

  useEffect(() => {
    if (didInitRef.current) {
      return;
    }
    didInitRef.current = true;

    document.title = "What do you need help with? - Green Home Grant - GOV.UK";

    initMatcher()
      .then((result) => {
        setMode(result.mode);
        setReady(true);
      })
      .catch(() => {
        // Treat init failure as ready in keyword-fallback so the page stays usable.
        setMode("keyword-fallback");
        setReady(true);
      });
  }, []);

  /**
   * Update the query as the user types.
   *
   * @param {React.ChangeEvent<HTMLTextAreaElement>} e - The change event.
   * @returns {void}
   */
  function handleChange(e) {
    setQuery(e.target.value);
  }

  /**
   * Run a search for the current query. No-ops until the matcher is ready and
   * does not call the matcher for an empty query (empty means "no query yet").
   *
   * @param {React.FormEvent<HTMLFormElement>} e - The submit event.
   * @returns {Promise<void>}
   */
  async function handleSubmit(e) {
    e.preventDefault();
    if (!ready) {
      return;
    }

    const q = query.trim();
    if (!q) {
      setHasSearched(false);
      setResults(null);
      setStatus("");
      return;
    }

    setStatus("Searching…");
    const r = await rankIntents(q, 3);
    setResults(r);
    setHasSearched(true);
    setShowAll(false);

    const visibleCount = r.filter((item) => item.score >= MIN_CONFIDENCE).length;
    if (visibleCount === 0) {
      setStatus("No strong matches — browse all services below.");
    } else {
      setStatus(`${visibleCount} services matched`);
    }
  }

  /**
   * Skip the assistant and show the full catalogue immediately.
   *
   * @returns {void}
   */
  function handleSkip() {
    setShowAll(true);
  }

  const visibleResults = (results || []).filter((item) => item.score >= MIN_CONFIDENCE);
  const hasStrongMatch = visibleResults.length > 0;
  const showResults = hasSearched && hasStrongMatch && !showAll;
  const isWeakMatch = hasSearched && !hasStrongMatch && !showAll;

  return (
    <>
      <Link to="/" className="govuk-back-link">
        Back
      </Link>

      <h1 className="govuk-heading-xl">What do you need help with?</h1>

      <p className="govuk-body">
        Describe your situation in your own words and we&rsquo;ll suggest services
        that might help.
      </p>

      {!ready && (
        <>
          <div
            className="govuk-notification-banner"
            role="region"
            aria-labelledby="assistant-loading-title"
          >
            <div className="govuk-notification-banner__header">
              <h2
                id="assistant-loading-title"
                className="govuk-notification-banner__title"
              >
                Preparing the assistant
              </h2>
            </div>
            <div className="govuk-notification-banner__content">
              <p className="govuk-body">
                This only happens once. It downloads around 25 MB to your device.
              </p>
            </div>
          </div>
          <p className="govuk-body">
            <button
              type="button"
              className="govuk-link app-link-button"
              onClick={handleSkip}
            >
              Skip and browse all services
            </button>
          </p>
        </>
      )}

      {ready && mode === "keyword-fallback" && (
        <div className="govuk-warning-text">
          <span className="govuk-warning-text__icon" aria-hidden="true">
            !
          </span>
          <strong className="govuk-warning-text__text">
            Using a basic keyword search &mdash; your browser couldn&rsquo;t load
            the assistant.
          </strong>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <label className="govuk-label" htmlFor="intent-query">
          Describe your situation
        </label>
        <div id="intent-query-hint" className="govuk-hint">
          For example, &lsquo;my boiler is broken&rsquo; or &lsquo;I want to
          register to vote&rsquo;.
        </div>
        <textarea
          id="intent-query"
          className="govuk-textarea"
          rows={3}
          aria-describedby="intent-query-hint"
          value={query}
          onChange={handleChange}
        />
        <button type="submit" className="govuk-button" aria-disabled={!ready}>
          Show services
        </button>
      </form>

      <p className="govuk-body" aria-live="polite" role="status">
        {status}
      </p>

      {showResults && (
        <ol className="govuk-list app-intent-results">
          {visibleResults.map(({ entry, score }) => (
            <li key={entry.id} className="app-intent-card">
              <h2 className="govuk-heading-m">
                <Link className="govuk-link" to={entry.route}>
                  {entry.title}
                </Link>
              </h2>
              <p className="govuk-body">{entry.description}</p>
              <SimilarityBadge score={score} />
            </li>
          ))}
        </ol>
      )}

      {!showResults && (
        <>
          {isWeakMatch && (
            <p className="govuk-body">
              We couldn&rsquo;t find a strong match for that description. Browse all
              services below.
            </p>
          )}
          <h2 className="govuk-heading-m">Browse all services</h2>
          <ul className="govuk-list">
            {SERVICE_CATALOGUE.map((entry) => (
              <li key={entry.id}>
                <Link className="govuk-link" to={entry.route}>
                  {entry.title}
                </Link>
                <p className="govuk-body">{entry.description}</p>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

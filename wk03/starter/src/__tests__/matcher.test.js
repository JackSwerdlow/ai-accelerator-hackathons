/**
 * Tests for the semantic intent matcher: keyword-fallback ranking, embeddings
 * cold/warm/stale cache behaviour, import/model-load degradation, and top-k.
 * The embeddings library is mocked, so no real model is ever downloaded or run.
 */
import { SERVICE_CATALOGUE, CATALOGUE_VERSION } from '../intent/catalogue.js';

const MODEL_NAME = 'Xenova/all-MiniLM-L6-v2';
const CACHE_KEY = 'ghg:intent-cache:v1';

// Mock the embeddings library; each test configures `pipeline` per scenario.
vi.mock('@xenova/transformers', () => ({ pipeline: vi.fn() }));

// matcher.js holds module-level singleton state, so reset the module registry
// and storage between tests to guarantee a clean init each time. Re-importing
// after resetModules() yields a fresh `pipeline` mock with no implementation.
beforeEach(() => {
  vi.resetModules();
  vi.clearAllMocks();
  localStorage.clear();
});

/**
 * Deterministic pseudo-embedding for a string: a fixed-length vector whose
 * dimensions are driven by a hash of each lowercase word. Texts that share
 * words get similar vectors, so cosine ranking is meaningful and repeatable.
 *
 * @param {string} text - The text to embed.
 * @returns {number[]} A deterministic vector.
 */
function vectorForText(text) {
  const dims = 24;
  const vector = new Array(dims).fill(0);
  const words = text.toLowerCase().split(/\W+/).filter((w) => w.length > 1);
  for (const word of words) {
    let hash = 0;
    for (let i = 0; i < word.length; i += 1) {
      hash = (hash * 31 + word.charCodeAt(i)) >>> 0;
    }
    vector[hash % dims] += 1;
  }
  return vector;
}

/**
 * Build a fresh fake extractor that returns deterministic embeddings.
 *
 * @returns {Function} A vi.fn() extractor returning { data: Float32Array }.
 */
function makeFakeExtractor() {
  return vi.fn((text) => ({ data: Float32Array.from(vectorForText(text)) }));
}

/**
 * Pre-seed localStorage with a valid embedding cache covering every catalogue
 * id, so initMatcher takes the warm-start path.
 *
 * @param {number} [version] - Catalogue version to stamp on the cache.
 * @returns {void}
 */
function seedCache(version = CATALOGUE_VERSION) {
  const embeddings = SERVICE_CATALOGUE.map((entry) => ({
    id: entry.id,
    vector: vectorForText(`${entry.title}. ${entry.description}. ${entry.phrases.join('. ')}`),
  }));
  localStorage.setItem(
    CACHE_KEY,
    JSON.stringify({ catalogueVersion: version, modelName: MODEL_NAME, embeddings })
  );
}

/**
 * Load the matcher with the embeddings pipeline forced to reject, so initMatcher
 * degrades to keyword-fallback mode. Rejecting (rather than a throwing mock
 * factory) keeps the failure scoped to this test and never leaks to others.
 *
 * @returns {Promise<object>} The initialised matcher module (fallback mode).
 */
async function loadFallbackMatcher() {
  const matcher = await import('../intent/matcher.js');
  const { pipeline } = await import('@xenova/transformers');
  pipeline.mockRejectedValue(new Error('no wasm'));
  await matcher.initMatcher();
  return matcher;
}

describe('matcher — keyword fallback', () => {
  it('F1. ranks green-home-grant top for "my boiler is broken"', async () => {
    const matcher = await loadFallbackMatcher();
    const results = await matcher.rankIntents('my boiler is broken');
    expect(results[0].entry.id).toBe('green-home-grant');
  });

  it('F2. ranks renew-passport top for "I want a new passport"', async () => {
    const matcher = await loadFallbackMatcher();
    const results = await matcher.rankIntents('I want a new passport');
    expect(results[0].entry.id).toBe('renew-passport');
  });

  it('F3. returns [] for an empty query', async () => {
    const matcher = await loadFallbackMatcher();
    const results = await matcher.rankIntents('');
    expect(results).toEqual([]);
  });

  it('F4. sorts by descending score with a stable id tiebreak', async () => {
    const matcher = await loadFallbackMatcher();
    const results = await matcher.rankIntents('help with my heating and council tax', 5);
    for (let i = 1; i < results.length; i += 1) {
      const prev = results[i - 1];
      const curr = results[i];
      expect(prev.score).toBeGreaterThanOrEqual(curr.score);
      if (prev.score === curr.score) {
        // Equal scores must be ordered by id ascending (localeCompare).
        expect(prev.entry.id.localeCompare(curr.entry.id)).toBeLessThanOrEqual(0);
      }
    }
  });
});

describe('matcher — embeddings mode', () => {
  it('E1. cold start embeds every entry once and writes a valid cache', async () => {
    const matcher = await import('../intent/matcher.js');
    const { pipeline } = await import('@xenova/transformers');
    const fakeExtractor = makeFakeExtractor();
    pipeline.mockResolvedValue(fakeExtractor);

    const result = await matcher.initMatcher();

    expect(result.mode).toBe('embeddings');
    expect(fakeExtractor).toHaveBeenCalledTimes(SERVICE_CATALOGUE.length);

    const cached = JSON.parse(localStorage.getItem(CACHE_KEY));
    expect(cached.catalogueVersion).toBe(CATALOGUE_VERSION);
    expect(cached.modelName).toBe(MODEL_NAME);
    const cachedIds = cached.embeddings.map((e) => e.id);
    for (const entry of SERVICE_CATALOGUE) {
      expect(cachedIds).toContain(entry.id);
    }
  });

  it('E2. warm start skips embedding during init; one call per query', async () => {
    seedCache();
    const matcher = await import('../intent/matcher.js');
    const { pipeline } = await import('@xenova/transformers');
    const fakeExtractor = makeFakeExtractor();
    pipeline.mockResolvedValue(fakeExtractor);

    await matcher.initMatcher();
    expect(fakeExtractor).toHaveBeenCalledTimes(0);

    await matcher.rankIntents('anything');
    expect(fakeExtractor).toHaveBeenCalledTimes(1);
  });

  it('E3. stale cache (wrong version) recomputes and rewrites the cache', async () => {
    seedCache(999);
    const matcher = await import('../intent/matcher.js');
    const { pipeline } = await import('@xenova/transformers');
    const fakeExtractor = makeFakeExtractor();
    pipeline.mockResolvedValue(fakeExtractor);

    await matcher.initMatcher();

    expect(fakeExtractor).toHaveBeenCalledTimes(SERVICE_CATALOGUE.length);
    const cached = JSON.parse(localStorage.getItem(CACHE_KEY));
    expect(cached.catalogueVersion).toBe(CATALOGUE_VERSION);
  });

  it('E4. model-load failure degrades to keyword-fallback yet still ranks', async () => {
    const matcher = await import('../intent/matcher.js');
    const { pipeline } = await import('@xenova/transformers');
    // Reject the pipeline to simulate no WASM / failed model load (SI7).
    pipeline.mockRejectedValue(new Error('no wasm'));

    const result = await matcher.initMatcher();
    expect(result.mode).toBe('keyword-fallback');

    const results = await matcher.rankIntents('my boiler is broken');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].entry.id).toBe('green-home-grant');
  });

  it('E5. returns exactly k results sorted by descending score', async () => {
    const matcher = await import('../intent/matcher.js');
    const { pipeline } = await import('@xenova/transformers');
    const fakeExtractor = makeFakeExtractor();
    pipeline.mockResolvedValue(fakeExtractor);

    await matcher.initMatcher();
    const results = await matcher.rankIntents('my house is cold and the boiler is broken', 3);

    expect(results).toHaveLength(3);
    for (let i = 1; i < results.length; i += 1) {
      expect(results[i - 1].score).toBeGreaterThanOrEqual(results[i].score);
    }
  });
});

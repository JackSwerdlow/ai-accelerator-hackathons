// Semantic intent matcher: embeds the service catalogue once (cached) and ranks
// it against a user query, degrading to a keyword scorer when the embeddings
// library cannot load (e.g. no WASM support, offline, or private browsing).

import { CATALOGUE_VERSION, SERVICE_CATALOGUE } from './catalogue.js';
import { cosineSimilarity, normalize } from './cosine.js';

/** Embedding model loaded via @xenova/transformers feature-extraction pipeline. */
const MODEL_NAME = 'Xenova/all-MiniLM-L6-v2';

/** localStorage key for the cached catalogue embeddings (versioned). */
const CACHE_KEY = 'ghg:intent-cache:v1';

// Module-level state: the matcher is a singleton initialised once per page load.
let mode = null;
let ready = false;
let catalogueVectors = [];
let extractor = null;
let pipelineRef = null;
let initPromise = null;

/**
 * Lazily create and memoise the feature-extraction extractor. The pipeline is
 * only constructed the first time an embedding is actually needed, so a warm
 * cache start never loads the (large) model.
 *
 * @returns {Promise<Function>} The memoised extractor function.
 */
async function getExtractor() {
  if (extractor === null) {
    extractor = await pipelineRef('feature-extraction', MODEL_NAME);
  }
  return extractor;
}

/**
 * Embed a piece of text into an L2-normalised vector using the model's
 * mean-pooled output.
 *
 * @param {string} text - The text to embed.
 * @returns {Promise<number[]>} The normalised embedding vector.
 */
async function embedText(text) {
  const out = await (await getExtractor())(text, { pooling: 'mean', normalize: true });
  return normalize(Array.from(out.data));
}

/**
 * Tokenise a string into a set of lowercase words longer than one character.
 *
 * @param {string} s - The string to tokenise.
 * @returns {Set<string>} The unique tokens.
 */
function tokenize(s) {
  return new Set(
    s
      .toLowerCase()
      .split(/\W+/)
      .filter((t) => t.length > 1)
  );
}

/**
 * Look up a catalogue entry by its stable id.
 *
 * @param {string} id - The catalogue entry id.
 * @returns {import('./catalogue.js').ServiceEntry|undefined} The matching entry.
 */
function entryById(id) {
  return SERVICE_CATALOGUE.find((e) => e.id === id);
}

/**
 * Sort ranked results by descending score with a stable tiebreak on entry id,
 * then keep the top `k`.
 *
 * @param {Array<{entry: object, score: number}>} ranked - Scored results.
 * @param {number} k - Maximum number of results to return.
 * @returns {Array<{entry: object, score: number}>} The top-k sorted results.
 */
function topK(ranked, k) {
  ranked.sort((a, b) => {
    if (b.score !== a.score) {
      return b.score - a.score;
    }
    // Stable tiebreak so equal-scoring results keep a deterministic order.
    return a.entry.id.localeCompare(b.entry.id);
  });
  return ranked.slice(0, k);
}

/**
 * Rank the catalogue against a query using token-overlap (no embeddings). Used
 * as the fallback when the embeddings library is unavailable.
 *
 * @param {string} query - The trimmed user query.
 * @param {number} k - Maximum number of results to return.
 * @returns {Array<{entry: object, score: number}>} The top-k keyword matches.
 */
function rankByKeyword(query, k) {
  const queryTokens = tokenize(query);
  const ranked = SERVICE_CATALOGUE.map((entry) => {
    const entryTokens = tokenize(
      `${entry.title} ${entry.description} ${entry.phrases.join(' ')}`
    );
    let overlap = 0;
    for (const token of queryTokens) {
      if (entryTokens.has(token)) {
        overlap += 1;
      }
    }
    const score = overlap / Math.max(queryTokens.size, 1);
    return { entry, score };
  });
  return topK(ranked, k);
}

/**
 * Read and validate the cached catalogue embeddings. Returns the restored
 * vectors only when the cache matches the current catalogue version, model, and
 * covers every catalogue id; otherwise returns null (cold/stale).
 *
 * @returns {Array<{id: string, vector: number[]}>|null} Cached vectors or null.
 */
function readCachedVectors() {
  try {
    // localStorage access is wrapped because it throws in private browsing.
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    const versionMatches = parsed.catalogueVersion === CATALOGUE_VERSION;
    const modelMatches = parsed.modelName === MODEL_NAME;
    if (!versionMatches || !modelMatches || !Array.isArray(parsed.embeddings)) {
      return null;
    }
    const cachedIds = new Set(parsed.embeddings.map((e) => e.id));
    const coversAll = SERVICE_CATALOGUE.every((entry) => cachedIds.has(entry.id));
    if (!coversAll) {
      return null;
    }
    return parsed.embeddings;
  } catch {
    // Treat any cache read/parse failure as a cold start.
    return null;
  }
}

/**
 * Persist the freshly computed catalogue embeddings to localStorage.
 *
 * @param {Array<{id: string, vector: number[]}>} vectors - Embeddings to cache.
 * @returns {void}
 */
function writeCachedVectors(vectors) {
  try {
    // localStorage access is wrapped because it throws in private browsing.
    localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({
        catalogueVersion: CATALOGUE_VERSION,
        modelName: MODEL_NAME,
        embeddings: vectors,
      })
    );
  } catch {
    // A failed write is non-fatal: the matcher still works this session.
  }
}

/**
 * Load the embeddings backend and populate the catalogue vectors (from cache or
 * by embedding). Any failure — a missing library, no WASM, or a model-load
 * error (SI7) — is caught by the caller to degrade to keyword-fallback mode.
 *
 * @returns {Promise<void>} Resolves once embeddings mode is ready.
 */
async function loadEmbeddings() {
  const mod = await import('@xenova/transformers');
  pipelineRef = mod.pipeline;

  // Load model files from the remote host, never the app's own origin.
  // Transformers.js defaults to allowLocalModels=true and probes a local
  // `/models/<model>/…` path first. Under any SPA history-fallback (the Vite
  // dev server, or a static SPA host in production) that path returns
  // index.html with HTTP 200, so the JSON parse of that HTML throws and we
  // silently degrade to keyword-fallback. Disabling the local probe sends the
  // request straight to the (reachable, cached-after-first-load) remote model.
  mod.env.allowLocalModels = false;

  const cached = readCachedVectors();
  if (cached) {
    // Warm start: reuse cached vectors without loading the model.
    catalogueVectors = cached.map((e) => ({ id: e.id, vector: e.vector }));
    return;
  }

  // Cold or stale start: embed every catalogue entry, then cache the result.
  // getExtractor() runs here, so a model-load failure surfaces as a throw and
  // is caught by runInit() — exactly the SI7 degradation path.
  catalogueVectors = [];
  for (const entry of SERVICE_CATALOGUE) {
    const vector = await embedText(
      `${entry.title}. ${entry.description}. ${entry.phrases.join('. ')}`
    );
    catalogueVectors.push({ id: entry.id, vector });
  }
  writeCachedVectors(catalogueVectors);
}

/**
 * Run a single initialisation: try the embeddings path and fall back to keyword
 * search if the library import or the model load fails (SI7).
 *
 * @returns {Promise<{mode: 'embeddings'|'keyword-fallback'}>} The chosen mode.
 */
async function runInit() {
  try {
    await loadEmbeddings();
    mode = 'embeddings';
  } catch {
    // No embeddings backend available (offline / no WASM / model load failed):
    // degrade to keyword search so the page never errors.
    mode = 'keyword-fallback';
  }
  ready = true;
  return { mode };
}

/**
 * Initialise the matcher. Safe to call multiple times — only the first call
 * does work; later callers share the same in-flight (or settled) promise.
 *
 * @returns {Promise<{mode: 'embeddings'|'keyword-fallback'}>} The chosen mode.
 */
export function initMatcher() {
  if (initPromise === null) {
    initPromise = runInit();
  }
  return initPromise;
}

/**
 * Report whether the matcher has finished initialising.
 *
 * @returns {boolean} True once initMatcher has resolved.
 */
export function isMatcherReady() {
  return ready;
}

/**
 * Rank the service catalogue against a natural-language query and return the
 * top `k` matches. Uses embeddings when available, otherwise keyword overlap.
 *
 * @param {string} query - The user's free-text query.
 * @param {number} [k=3] - Maximum number of results to return.
 * @returns {Promise<Array<{entry: object, score: number}>>} Ranked matches.
 */
export async function rankIntents(query, k = 3) {
  const trimmed = (query || '').trim();
  if (!trimmed) {
    return [];
  }

  if (mode === 'keyword-fallback') {
    return rankByKeyword(trimmed, k);
  }

  const queryVector = await embedText(trimmed);
  const ranked = catalogueVectors.map(({ id, vector }) => ({
    entry: entryById(id),
    score: cosineSimilarity(queryVector, vector),
  }));
  return topK(ranked, k);
}

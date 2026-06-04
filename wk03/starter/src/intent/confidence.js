// Shared confidence thresholds for the semantic intent matcher's similarity
// scores, used by HelpEntryPage (show/hide a match) and SimilarityBadge (colour
// band). Kept in one place so the two can never drift apart (PLAN.md §16).
//
// Calibrated for the max-pooled per-anchor scoring in matcher.js: scoring an
// entry by its single best-matching anchor (rather than one mean-pooled vector)
// shifts scores upward, so these sit higher than the original 0.30/0.40/0.55.
// Derived from a score matrix over recall, boundary and off-topic queries —
// unrelated queries topped out around 0.44 and the weakest genuine match was
// around 0.53, so MIN sits in that gap: admit real matches, reject the rest.

/** At or above this, a match is badged "high" confidence. */
export const HIGH_CONFIDENCE = 0.65;

/** At or above this (but below HIGH), a match is badged "medium". */
export const MEDIUM_CONFIDENCE = 0.40;

/** Below this, a match is dropped and the page falls back to the full catalogue. */
export const MIN_CONFIDENCE = 0.3;

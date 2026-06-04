/**
 * Pure vector maths for the semantic intent matcher: cosine similarity and
 * L2 normalisation, kept dependency-free so they can be unit-tested in isolation
 * and reused by both the embeddings and keyword-fallback code paths.
 */

/**
 * Compute the cosine similarity between two equal-length numeric vectors.
 *
 * @param {number[]} a - First vector.
 * @param {number[]} b - Second vector (must be the same length as `a`).
 * @returns {number} Similarity in the range [-1, 1]; 0 when either vector has
 *   zero magnitude (so the result is never NaN).
 * @throws {Error} If the two vectors have different lengths.
 */
export function cosineSimilarity(a, b) {
  if (a.length !== b.length) {
    throw new Error(
      `cosineSimilarity: vectors must be the same length (got ${a.length} and ${b.length})`
    );
  }

  let dot = 0;
  let magA = 0;
  let magB = 0;
  for (let i = 0; i < a.length; i += 1) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }

  // A zero-magnitude vector has no direction, so similarity is undefined; we
  // return 0 rather than dividing by zero and producing NaN.
  if (magA === 0 || magB === 0) {
    return 0;
  }

  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}

/**
 * Return an L2-normalised copy of a vector (unit length).
 *
 * @param {number[]} v - The vector to normalise.
 * @returns {number[]} A new array; the unit vector, or an unchanged copy when
 *   `v` has zero magnitude (avoids divide-by-zero).
 */
export function normalize(v) {
  let mag = 0;
  for (let i = 0; i < v.length; i += 1) {
    mag += v[i] * v[i];
  }

  // Zero-magnitude vectors cannot be scaled to unit length; copy as-is.
  if (mag === 0) {
    return v.slice();
  }

  const norm = Math.sqrt(mag);
  return v.map((value) => value / norm);
}

/**
 * Unit tests for the pure vector maths in cosine.js, covering the identity,
 * orthogonal, opposite, zero-magnitude, and length-mismatch behaviours.
 */
import { cosineSimilarity, normalize } from '../intent/cosine.js';

describe('cosineSimilarity', () => {
  it('1. returns 1 for identical vectors', () => {
    expect(cosineSimilarity([1, 2, 3], [1, 2, 3])).toBeCloseTo(1);
  });

  it('2. returns 0 for orthogonal vectors', () => {
    expect(cosineSimilarity([1, 0], [0, 1])).toBeCloseTo(0);
  });

  it('3. returns -1 for opposite vectors', () => {
    expect(cosineSimilarity([1, 0], [-1, 0])).toBeCloseTo(-1);
  });

  it('4. returns 0 (not NaN) when one vector has zero magnitude', () => {
    const result = cosineSimilarity([0, 0], [1, 2]);
    expect(result).toBe(0);
    expect(Number.isNaN(result)).toBe(false);
  });

  it('5. throws when the vectors have mismatched lengths', () => {
    expect(() => cosineSimilarity([1, 2], [1, 2, 3])).toThrow();
  });
});

describe('normalize', () => {
  it('returns a unit-length copy of a non-zero vector', () => {
    const result = normalize([3, 4]);
    expect(result).toEqual([0.6, 0.8]);
  });

  it('returns an unchanged copy for a zero-magnitude vector', () => {
    const input = [0, 0];
    const result = normalize(input);
    expect(result).toEqual([0, 0]);
    expect(result).not.toBe(input);
  });
});

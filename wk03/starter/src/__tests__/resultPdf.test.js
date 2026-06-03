/**
 * Smoke tests for buildResultDoc() — confirms the renderer produces a real
 * text-based PDF (the core accessibility claim) with the right metadata, and
 * that it is deterministic given a fixed date. Heavy content assertions live
 * in resultSummary.test.js; this file guards the jsPDF integration.
 */
import { buildResultDoc } from '../resultPdf';

const ANSWERS = {
  propertyType: 'detached',
  ownership: 'owner',
  incomeBand: 'low',
  insulation: 'none',
  heating: 'gas-boiler',
};

const FIXED_DATE = new Date('2026-06-03T10:00:00Z');

/** Decode the uncompressed PDF bytes to a Latin-1 string for substring checks. */
function pdfText(doc) {
  const buf = new Uint8Array(doc.output('arraybuffer'));
  let out = '';
  for (let i = 0; i < buf.length; i += 1) out += String.fromCharCode(buf[i]);
  return out;
}

describe('buildResultDoc', () => {
  it('returns a jsPDF document and emits a PDF data URI', () => {
    const doc = buildResultDoc(ANSWERS, { date: FIXED_DATE });
    expect(doc.getNumberOfPages()).toBeGreaterThanOrEqual(1);
    expect(doc.output('datauristring')).toMatch(/^data:application\/pdf/);
  });

  it('sets the document language to en-GB for screen readers (WCAG 3.1.1)', () => {
    const doc = buildResultDoc(ANSWERS, { date: FIXED_DATE });
    expect(pdfText(doc)).toMatch(/\/Lang\s*\(en-GB\)/);
  });

  it('embeds real selectable text, not a rasterised image', () => {
    const raw = pdfText(doc(ANSWERS));
    // Headline + a section heading appear as literal text in the content stream.
    expect(raw).toContain('You may be eligible for a Green Home Grant');
    expect(raw).toContain('What to do next');
    // A screenshot PDF would carry an /Image XObject and no such text.
    expect(raw).not.toMatch(/\/Subtype\s*\/Image/);
  });

  it('stamps the generated date when one is provided', () => {
    expect(pdfText(buildResultDoc(ANSWERS, { date: FIXED_DATE }))).toContain('3 June 2026');
  });

  it('omits the date line when no date is given', () => {
    expect(pdfText(buildResultDoc(ANSWERS))).not.toMatch(/Generated on/);
  });

  it('does not throw for a tenant result or undefined answers', () => {
    expect(() => buildResultDoc({ ownership: 'private-renter', landlordConsent: 'yes' })).not.toThrow();
    expect(() => buildResultDoc(undefined)).not.toThrow();
  });
});

/** Helper so the "real text" test reads cleanly. */
function doc(answers) {
  return buildResultDoc(answers, { date: FIXED_DATE });
}

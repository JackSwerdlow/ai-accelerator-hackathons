/**
 * Renders the result summary (resultSummary.js) to an accessible PDF using
 * jsPDF (PLAN.md §10 stretch: accessible PDF).
 *
 * Accessibility decisions:
 *  - Real, selectable text via doc.text() — NOT a rasterised screenshot of the
 *    DOM (html2canvas). A screenshot PDF has no text layer, is invisible to
 *    screen readers, and fails WCAG 1.4.5 (Images of Text). Building from text
 *    keeps the content machine-readable, selectable, and reflowable.
 *  - setLanguage('en-GB') writes /Lang into the catalog so screen readers use
 *    the correct pronunciation (WCAG 3.1.1 Language of Page).
 *  - DisplayDocTitle viewer preference makes the PDF reader announce the
 *    document title rather than the filename (WCAG 2.4.2 Page Titled).
 *  - Black text on white, body >= 11pt, headings larger — meets contrast
 *    (1.4.3) and does not rely on colour alone to convey the outcome (the
 *    outcome is stated in words as the headline).
 *  - Single-column, top-to-bottom reading order matches the visual order.
 *
 * Note: jsPDF does not emit a fully tagged PDF/UA structure tree, so this is
 * "accessible" in the practical, screen-reader-legible sense rather than
 * certified PDF/UA. The text-based approach is the prerequisite for either.
 */
import { jsPDF } from 'jspdf';
import { buildResultSummary } from './resultSummary';

// A4 page in millimetres (jsPDF unit: 'mm'). Font sizes stay in points.
const PAGE = { width: 210, height: 297 };
const MARGIN = 20;
const CONTENT_WIDTH = PAGE.width - MARGIN * 2;
const BOTTOM_LIMIT = PAGE.height - MARGIN;

const FONT = {
  title: 22,
  headline: 16,
  heading: 13,
  body: 11,
  meta: 10,
};
// Line height as a multiple of font size, converted pt -> mm (1pt = 0.3528mm).
const PT_TO_MM = 0.3528;
const LINE_FACTOR = 1.5;

/**
 * Format a date as a GOV.UK-style "3 June 2026" string.
 *
 * @param {Date} date
 * @returns {string}
 */
function formatDate(date) {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date);
}

/**
 * Build the jsPDF document for a set of answers. Pure given (answers, date):
 * does not touch the DOM or trigger a download, so it is unit-testable.
 *
 * @param {object} answers - The current answers from the form.
 * @param {{ date?: Date }} [options]
 * @returns {import('jspdf').jsPDF}
 */
export function buildResultDoc(answers, { date } = {}) {
  const summary = buildResultSummary(answers);
  const generatedOn = date instanceof Date ? date : null;

  const doc = new jsPDF({ unit: 'mm', format: 'a4', putOnlyUsedFonts: true });

  // --- Accessibility metadata ---
  doc.setLanguage('en-GB');
  doc.setProperties({
    title: summary.documentTitle,
    subject: 'Green Home Grant eligibility result',
    author: 'GOV.UK Green Home Grant service',
    creator: 'Green Home Grant eligibility checker',
  });
  // Show the document title (not the filename) in the PDF reader's title bar.
  if (typeof doc.viewerPreferences === 'function') {
    doc.viewerPreferences({ DisplayDocTitle: true });
  }

  const cursor = { y: MARGIN };

  // Service name (small) + document title.
  writeLine(doc, cursor, summary.serviceName, { size: FONT.meta, style: 'normal' });
  writeBlock(doc, cursor, summary.documentTitle, { size: FONT.title, style: 'bold' });
  if (generatedOn) {
    writeLine(doc, cursor, `Generated on ${formatDate(generatedOn)}`, {
      size: FONT.meta,
      style: 'normal',
    });
  }
  cursor.y += 4;

  // Outcome headline + highlight.
  writeBlock(doc, cursor, summary.headline, { size: FONT.headline, style: 'bold' });
  if (summary.highlight) {
    writeBlock(doc, cursor, summary.highlight, { size: FONT.body, style: 'normal' });
  }
  cursor.y += 2;

  // Outcome sections.
  for (const section of summary.sections) {
    writeBlock(doc, cursor, section.heading, { size: FONT.heading, style: 'bold' });
    for (const paragraph of section.paragraphs) {
      writeBlock(doc, cursor, paragraph, { size: FONT.body, style: 'normal' });
    }
    for (const bullet of section.bullets) {
      writeBlock(doc, cursor, bullet, { size: FONT.body, style: 'normal', bullet: true });
    }
    cursor.y += 2;
  }

  // Answer summary.
  if (summary.answers.length > 0) {
    writeBlock(doc, cursor, 'Your answers', { size: FONT.heading, style: 'bold' });
    for (const { label, value } of summary.answers) {
      writeBlock(doc, cursor, `${label}: ${value}`, { size: FONT.body, style: 'normal' });
    }
    cursor.y += 2;
  }

  // Footnote.
  writeBlock(doc, cursor, summary.footnote, { size: FONT.meta, style: 'italic' });

  return doc;
}

/**
 * Build the document and trigger a browser download with a descriptive
 * filename. Call from a click handler.
 *
 * @param {object} answers - The current answers from the form.
 * @param {{ date?: Date }} [options]
 */
export function downloadResultPdf(answers, { date } = {}) {
  const doc = buildResultDoc(answers, { date });
  doc.save('green-home-grant-result.pdf');
}

// --- layout helpers ---

/** Advance to a new page if the next `needed` mm would overflow. */
function ensureSpace(doc, cursor, needed) {
  if (cursor.y + needed > BOTTOM_LIMIT) {
    doc.addPage();
    cursor.y = MARGIN;
  }
}

/** Write a single (already short) line and advance the cursor. */
function writeLine(doc, cursor, text, { size, style }) {
  const lineHeight = size * PT_TO_MM * LINE_FACTOR;
  ensureSpace(doc, cursor, lineHeight);
  doc.setFont('helvetica', style);
  doc.setFontSize(size);
  doc.setTextColor(11, 12, 12); // GOV.UK near-black (#0b0c0c) on white
  doc.text(text, MARGIN, cursor.y, { baseline: 'top' });
  cursor.y += lineHeight;
}

/**
 * Write a wrapped block of text (paragraph, heading or bullet), splitting it
 * to the content width and paginating line-by-line so a block can break
 * across pages without clipping.
 */
function writeBlock(doc, cursor, text, { size, style, bullet = false }) {
  doc.setFont('helvetica', style);
  doc.setFontSize(size);
  doc.setTextColor(11, 12, 12);

  const indent = bullet ? 6 : 0;
  const lines = doc.splitTextToSize(text, CONTENT_WIDTH - indent);
  const lineHeight = size * PT_TO_MM * LINE_FACTOR;

  lines.forEach((line, i) => {
    ensureSpace(doc, cursor, lineHeight);
    const prefix = bullet && i === 0 ? '• ' : '';
    const x = MARGIN + indent;
    if (prefix) doc.text(prefix, MARGIN + 1, cursor.y, { baseline: 'top' });
    doc.text(line, x, cursor.y, { baseline: 'top' });
    cursor.y += lineHeight;
  });
}

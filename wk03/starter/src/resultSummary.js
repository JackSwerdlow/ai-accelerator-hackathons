/**
 * Pure content model for the downloadable result summary (PLAN.md §10 stretch:
 * accessible PDF). Turns an answers object into an ordered, plain-text
 * structure — headline, outcome sections, recommended measures, next steps,
 * and the answer summary — with no rendering concerns.
 *
 * Keeping this separate from the jsPDF rendering (resultPdf.js) means the
 * wording is unit-testable without a PDF engine, and the on-screen result
 * (ResultPage.jsx) and the PDF stay derivable from the same eligibility()
 * source of truth. The copy here mirrors ResultPage.jsx but as plain prose:
 * no links or icons, since a PDF cannot carry the on-screen "Find an approved
 * installer" hyperlinks.
 */
import { eligibility } from './eligibility';
import { flowSteps } from './flow';
import { labelFor } from './displayLabels';

// User-facing label for each answer field, in the same wording as the
// check-answers summary (CheckAnswersPage ROW_LABELS). Kept local so this
// module has no UI dependency; the lists are short and rarely change.
const FIELD_LABELS = {
  propertyType: 'Property type',
  ownership: 'Ownership status',
  incomeBand: 'Annual household income',
  landlordConsent: "Landlord's permission",
  insulation: 'Current insulation',
  heating: 'Current heating system',
};

const FOOTNOTE =
  'This is an indicative result based on the answers you gave. It is not a ' +
  'guarantee of funding. Your eligibility will be confirmed when an approved ' +
  'installer assesses your property.';

/**
 * Build the ordered content model for the result summary document.
 *
 * @param {object} [answers] - The current answers from the form.
 * @returns {{
 *   documentTitle: string,
 *   serviceName: string,
 *   outcome: string,
 *   reason: string,
 *   headline: string,
 *   highlight: string,
 *   sections: { heading: string, paragraphs: string[], bullets: string[] }[],
 *   answers: { label: string, value: string }[],
 *   footnote: string,
 * }}
 */
export function buildResultSummary(answers) {
  const a = answers ?? {};
  const { outcome, reason, measures } = eligibility(a);

  const answerRows = flowSteps(a)
    .map(({ field }) => ({ label: FIELD_LABELS[field], value: labelFor(field, a[field]) }))
    .filter((row) => row.label && row.value);

  return {
    documentTitle: 'Your Green Home Grant result',
    serviceName: 'Green Home Grant',
    outcome,
    reason,
    ...headlineFor(outcome),
    sections: sectionsFor(outcome, reason, measures),
    answers: answerRows,
    footnote: FOOTNOTE,
  };
}

/** Panel headline + highlight line, mirroring ResultPage.jsx. */
function headlineFor(outcome) {
  if (outcome === 'eligible') {
    return {
      headline: 'You may be eligible for a Green Home Grant',
      highlight: 'You may qualify for a grant of up to £10,000.',
    };
  }
  if (outcome === 'partial') {
    return { headline: 'You may be partially eligible for a Green Home Grant', highlight: '' };
  }
  return { headline: 'You are not eligible for a Green Home Grant', highlight: '' };
}

/** Outcome-specific body, as ordered { heading, paragraphs, bullets } sections. */
function sectionsFor(outcome, reason, measures) {
  if (outcome === 'eligible') {
    return [
      {
        heading: 'Recommended measures',
        paragraphs: ['Based on your answers, your home could qualify for the following measures:'],
        bullets: measures,
      },
      {
        heading: 'What to do next',
        paragraphs: [
          'The grant covers up to two-thirds of the cost of each measure, up to the maximum grant amount.',
          'Contact an approved Green Home Grant installer to assess your property. They will confirm which measures are suitable and apply for the grant on your behalf.',
          'You do not need to pay anything upfront. The installer will claim the grant directly from the scheme administrator.',
        ],
        bullets: [],
      },
    ];
  }

  if (outcome === 'partial' && reason === 'renter') {
    const sections = [
      {
        heading: 'What this means',
        paragraphs: [
          'As a tenant, your landlord needs to apply for this grant on your behalf.',
          'You can request an information pack to share with your landlord. It explains the grant, the installation process, and how to apply.',
        ],
        bullets: [],
      },
    ];
    if (measures.length > 0) {
      sections.push({
        heading: 'Measures that may be available',
        paragraphs: [
          'Based on your answers, the following measures may be available for your home, subject to a property assessment:',
        ],
        bullets: measures,
      });
    }
    sections.push({
      heading: 'What to do next',
      paragraphs: [
        'Ask your landlord to contact an approved installer for a property assessment. Landlords can apply directly through the Green Home Grant scheme.',
      ],
      bullets: [],
    });
    return sections;
  }

  if (outcome === 'partial' && reason === 'owner-mid-income') {
    return [
      {
        heading: 'Recommended measures',
        paragraphs: [
          'Based on your income band, you may qualify for a partial grant of up to £5,000.',
          'Your home could qualify for the following measures:',
        ],
        bullets: measures,
      },
      {
        heading: 'What to do next',
        paragraphs: [
          'Contact an approved Green Home Grant installer to assess your property. The installer will apply for the grant on your behalf.',
        ],
        bullets: [],
      },
    ];
  }

  // ineligible
  const paragraphs = [];
  if (reason === 'income-too-high') {
    paragraphs.push('Your household income is above the threshold for this grant.');
  } else if (reason === 'no-measures-needed') {
    paragraphs.push(
      'Your home already has the insulation and heating measures this grant covers. No further measures are available under this scheme.',
    );
  } else if (reason === 'no-landlord-consent') {
    paragraphs.push(
      "You told us you do not have your landlord's permission to make energy efficiency improvements. Your landlord needs to agree before you can apply for a Green Home Grant.",
      'If your landlord changes their decision, you can use this service again to check what your home could qualify for.',
    );
  }
  paragraphs.push(
    "You may still be able to improve your home's energy efficiency through other government schemes.",
  );
  return [{ heading: 'What this means', paragraphs, bullets: [] }];
}

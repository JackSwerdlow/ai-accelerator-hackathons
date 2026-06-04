// Static catalogue of GOV.UK services the intent matcher ranks against; kept as
// plain data (no runtime deps) so it can be embedded once and cached deterministically.

/**
 * @typedef {Object} ServiceEntry
 * @property {string} id - Stable identifier used as a cache key and tiebreak sort key.
 * @property {string} title - Human-readable service name shown in results.
 * @property {string} description - Short plain-English summary (15-25 words).
 * @property {string} route - In-app path ("/") or external gov.uk URL.
 * @property {string[]} phrases - Example natural-language queries (formal and informal).
 */

/**
 * Schema/content version. Bump when entries change so stale embedding caches are
 * recomputed rather than reused.
 * @type {number}
 */
export const CATALOGUE_VERSION = 1;

/**
 * The full set of services available to the semantic intent matcher. Order is not
 * significant; ranking is computed at query time.
 * @type {ServiceEntry[]}
 */
export const SERVICE_CATALOGUE = [
  {
    id: 'green-home-grant',
    title: 'Green Home Grant',
    description:
      'Get help paying to make your home warmer and cheaper to heat, including insulation and replacing an old or broken boiler.',
    route: '/',
    phrases: [
      'my boiler is broken',
      'my house is cold',
      'help with home insulation',
      "I can't afford my heating bill",
      'replace my gas boiler with a heat pump',
      'my home is freezing and the heating costs too much',
      'grant to insulate my loft and walls',
      'my old boiler keeps breaking down',
    ],
  },
  {
    id: 'apply-universal-credit',
    title: 'Apply for Universal Credit',
    description:
      'Claim a monthly payment to help with your living costs if you are on a low income, out of work, or unable to work.',
    route: 'https://www.gov.uk/universal-credit',
    phrases: [
      'I want to apply for Universal Credit',
      'I lost my job and need money to live on',
      'help with living costs because I am skint',
      'claim benefits while looking for work',
      "I can't afford food and rent",
      'low income support payment',
    ],
  },
  {
    id: 'renew-passport',
    title: 'Renew or replace your passport',
    description:
      'Apply online to renew an adult passport, replace a lost or stolen passport, or get your first adult passport.',
    route: 'https://www.gov.uk/renew-adult-passport',
    phrases: [
      'I want a new passport',
      'lost my passport',
      'renew my passport before I travel',
      'my passport has expired',
      'someone stole my passport',
      'get a replacement passport quickly',
    ],
  },
  {
    id: 'register-to-vote',
    title: 'Register to vote',
    description:
      'Add yourself to the electoral register so you can vote in elections and referendums in England, Scotland or Wales.',
    route: 'https://www.gov.uk/register-to-vote',
    phrases: [
      'I want to register to vote',
      'sign up to vote in the next election',
      'how do I get on the electoral roll',
      'I moved house and need to update my voting details',
      'can I vote, I just turned 18',
      'put my name down for elections',
    ],
  },
  {
    id: 'free-school-meals',
    title: 'Apply for free school meals',
    description:
      'Check if your child can get free meals at school and apply through your local council if you receive certain benefits.',
    route: 'https://www.gov.uk/apply-free-school-meals',
    phrases: [
      'apply for free school meals',
      'can my kids get free dinners at school',
      'help with school lunch costs',
      'free meals for my child because we are on benefits',
      'school dinner money support',
      'I want free school meals for my son',
    ],
  },
  {
    id: 'council-tax-reduction',
    title: 'Apply for Council Tax Reduction',
    description:
      'Get money off your council tax bill if you are on a low income or claim certain benefits, applied for through your council.',
    route: 'https://www.gov.uk/apply-council-tax-reduction',
    phrases: [
      'reduce my council tax bill',
      "I can't afford my council tax",
      'apply for council tax support',
      'discount on council tax because I am on a low income',
      'help paying council tax',
      'council tax is too expensive for me',
    ],
  },
  {
    id: 'replace-driving-licence',
    title: 'Replace your driving licence',
    description:
      'Apply for a replacement if your driving licence is lost, stolen, damaged or has changes to your name or address.',
    route: 'https://www.gov.uk/replace-a-driving-licence',
    phrases: [
      'replace my driving licence',
      'I lost my driving licence',
      'my licence was stolen',
      'get a new photocard licence after changing my name',
      'damaged driving licence needs replacing',
      'order a duplicate driving licence',
    ],
  },
  {
    id: 'report-benefit-fraud',
    title: 'Report benefit fraud',
    description:
      'Tell the government anonymously if you think someone is claiming benefits they are not entitled to.',
    route: 'https://www.gov.uk/report-benefit-fraud',
    phrases: [
      'report someone for benefit fraud',
      'I think my neighbour is cheating benefits',
      'tell the government about benefit fraud anonymously',
      'someone is claiming benefits they should not get',
      'report a person lying about their benefits',
      'grass up benefit cheats',
    ],
  },
  {
    id: 'apply-for-pension-credit',
    title: 'Apply for Pension Credit',
    description:
      'Claim extra money to help with living costs if you are over State Pension age and on a low income.',
    route: 'https://www.gov.uk/pension-credit',
    phrases: [
      'apply for Pension Credit',
      'extra money for pensioners on a low income',
      'I am a pensioner struggling to pay bills',
      'top up my pension because I have little income',
      'help with costs now I have retired',
      'pension top up for older people',
    ],
  },
  {
    id: 'claim-child-benefit',
    title: 'Claim Child Benefit',
    description:
      'Get a regular payment to help with the cost of raising a child if you are responsible for a child under 16.',
    route: 'https://www.gov.uk/child-benefit',
    phrases: [
      'claim Child Benefit',
      'I just had a baby and want child benefit',
      'money to help raise my children',
      'sign up for child benefit payments',
      'how do I get child benefit for my newborn',
      'financial help for looking after my kids',
    ],
  },
  {
    id: 'apply-for-a-blue-badge',
    title: 'Apply for a Blue Badge',
    description:
      'Apply for a parking permit that lets disabled or less mobile people park closer to where they need to go.',
    route: 'https://www.gov.uk/apply-blue-badge',
    phrases: [
      'apply for a Blue Badge',
      'disabled parking permit',
      'I struggle to walk and need to park closer',
      'blue badge for my elderly mum',
      'get a parking badge because of my disability',
      'permit to park in disabled bays',
    ],
  },
];

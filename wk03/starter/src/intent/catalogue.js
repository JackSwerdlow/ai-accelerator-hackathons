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
export const CATALOGUE_VERSION = 2;

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
      'help with home insulation',
      'replace my gas boiler with a heat pump',
      'grant to insulate my loft and walls',
      "I can't afford my heating bill",
      "brrr it's freezing in here",
      'draughty windows letting the cold in',
      'single glazing makes my flat freezing',
      'grant for cavity wall insulation',
      'my old boiler keeps breaking down',
      'make my home warmer and cheaper to heat',
      'my house costs a fortune to heat',
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
      'start a new Universal Credit claim',
      'how do I claim UC',
      'I lost my job and need money to live on',
      'claim benefits while looking for work',
      "I'm unemployed and broke",
      'just been made redundant and need help',
      "my hours got cut and I can't get by",
      'on a zero hours contract and skint',
      "I'm on the dole and need to sign on",
      'too ill to work and need benefits',
      "I can't afford food and rent",
      'low income and not working',
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
      'applying for my first adult passport',
      'my passport went through the wash',
      'passport expired and I fly next week',
      'need a passport for my holiday',
      'passport renewal',
      'update my passport after my name changed',
      'my dog chewed my passport',
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
      'I moved house and need to re-register to vote',
      'can I vote, I just turned 18',
      'put my name down for elections',
      'register to vote online',
      'am I registered to vote',
      'add me to the electoral register',
      'register before the election deadline',
      'just got citizenship and want to vote',
      'register for the referendum',
      'voter registration',
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
      'school dinner money support',
      'I want free school meals for my son',
      "free school meals, we're on benefits",
      'do my children qualify for free school dinners',
      'struggling to pay for school dinners',
      'kids need free food at school',
      "can't afford my child's school lunch",
      'are my kids entitled to free school meals',
      'free dinners for my child at school',
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
      'council tax discount for low income',
      'help paying council tax',
      'council tax too high',
      'can I get money off my council tax',
      "skint and can't pay my council tax",
      'council tax help while on benefits',
      'council tax rebate for people on a low income',
      'struggling to pay my council tax this month',
      'is there any help with my council tax',
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
      'update the address on my driving licence',
      'new licence after moving house',
      'my dog chewed my driving licence',
      'someone nicked my driving licence',
      'new driving licence after getting married',
      'apply to DVLA for a replacement licence',
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
      'report a person lying about their benefits',
      'grass up benefit cheats',
      'working cash in hand while claiming',
      'claiming single but living with a partner',
      'faking a disability to claim benefits',
      "claiming for kids who don't live with them",
      'report dole fraud',
      'someone fiddling their benefits',
      'sick of my neighbour milking benefits',
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
      "my state pension isn't enough to live on",
      "I'm 66 and on a low income",
      "I'm a skint pensioner",
      "money's tight since I retired",
      "can't manage on my state pension",
      'help for hard-up pensioners',
      'boost my income in retirement',
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
      'sign up for child benefit payments',
      'child benefit for my newborn',
      'child benefit to help raise my children',
      'child benefit for my second child',
      'claiming child benefit for my teenager',
      'do I still get child benefit at 16',
      'child benefit for looking after my kids',
      'child benefit when I have another sprog',
      'update my child benefit claim',
      'am I eligible for child benefit',
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
      'renew my blue badge',
      'I struggle to walk and need to park closer',
      'blue badge for my elderly mum',
      'blue badge for my disabled son',
      'permit to park in disabled bays',
      'parking badge for a hidden disability',
      "I can't manage the walk from the car park",
      "park closer when I'm out because of my mobility",
      'blue badge so I can park outside the hospital',
      'badge to park in disabled spaces',
    ],
  },
];

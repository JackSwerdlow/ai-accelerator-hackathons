# Standards Research — Green Home Grant Eligibility Checker

> **Author:** Agent-Research
> **Date:** 2026-06-03
> **Purpose:** Catalogue the standards, regulations, and design patterns that this service must conform to, with primary-source links and direction for follow-on requirements and solution-planning work. This is a research artefact only — it does not propose acceptance criteria or implementation.

---

## 1. How to read this document

The brief in [`wk03/README.md`](../README.md) names three concrete obligations:

1. GOV.UK design patterns
2. WCAG 2.2 AA accessibility
3. Working on both mobile and desktop browsers

The rubric adds a fourth: **Service Standard conformance signals** (accessibility statement, phase banner, footer, cookie notice). Together these point to a layered set of standards:

| Layer | What it tells us | Source of truth |
|-------|------------------|-----------------|
| Legal / regulatory | What the service must do to be lawful for a UK public-sector body | PSBAR 2018; Equality Act 2010 |
| Cross-government policy | What "good" looks like for a government service | GDS Service Standard (14 points) |
| Technical accessibility standard | The objective bar a service is measured against | WCAG 2.2 AA |
| Design conventions | How a GOV.UK service should look, sound and behave | GOV.UK Design System, GOV.UK Service Manual, GOV.UK Content Style Guide |

Each section below covers one of those layers, lists the primary sources, and ends with **"Implications for requirements"** — short prompts to feed into the requirements / solution-planning phase. No requirement IDs yet; that work belongs in a follow-up doc.

---

## 2. Legal and regulatory baseline

Three regulatory regimes apply alongside each other: PSBAR (accessibility), the Equality Act 2010 (anticipatory reasonable adjustments), UK GDPR / DPA 2018 (data protection), and PECR (cookies and electronic comms). Each is summarised below.

### 2.1 Public Sector Bodies Accessibility Regulations 2018 (PSBAR)

The Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018 make it a legal duty for public-sector bodies to:

- Meet WCAG 2.2 level AA (the current target standard cited in UK government guidance).
- Publish and maintain an **accessibility statement** that says how accessible the site is, lists known issues, says how to report problems, and gives the enforcement route.
- Enforced by the **Equality and Human Rights Commission (EHRC)** in England, Scotland, Wales; **Equality Commission for Northern Ireland (ECNI)** in NI. GDS monitors compliance through sampling.

Primary sources:
- Understand the regs — <https://www.gov.uk/guidance/understanding-accessibility-requirements-for-public-sector-bodies>
- Make your site accessible and publish a statement — <https://www.gov.uk/guidance/make-your-website-or-app-accessible-and-publish-an-accessibility-statement>
- Sample accessibility statement (model wording — some of which is legally required) — <https://www.gov.uk/government/publications/sample-accessibility-statement/sample-accessibility-statement-for-a-fictional-public-sector-website>

### 2.2 Equality Act 2010

The Equality Act sits underneath PSBAR. It places an anticipatory duty on service providers to make reasonable adjustments for disabled people. A service that demonstrably meets WCAG 2.2 AA, has a published statement, and supports common assistive tech is the GOV.UK-recommended way of evidencing that duty for digital services.

### 2.3 UK GDPR and Data Protection Act 2018

Even though this service does not store PII, UK GDPR principles still bear on the design:

- **Article 5 (data minimisation)** — only collect what is needed for the eligibility decision. The decision to ask income as a band rather than a salary is a data-minimisation choice; requirements should frame it that way.
- **Article 25 (data protection by design and by default)** — defaults must be privacy-protective.
- A **privacy notice** is typically required alongside the accessibility statement for any service that processes personal data. For a fictional scheme that holds answers only in browser memory, the notice may be a stub, but the obligation should be acknowledged.

References:
- ICO guide to UK GDPR — <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/>
- DPA 2018 — <https://www.legislation.gov.uk/ukpga/2018/12/contents>

### 2.4 PECR — cookies and electronic communications

The Privacy and Electronic Communications Regulations 2003 (PECR) cover the use of cookies and similar storage technologies. The rubric (README L116) grades a "cookie notice" as a Service-Standard signal — PECR is the regime under which that notice exists.

Key rule: **prior, informed consent** is required before setting any non-essential cookies (analytics included). A notice alone is insufficient — it must offer a consent choice.

For this service:
- The SPA may set no non-essential cookies (no analytics, no third-party embeds) — in which case a simple cookie statement that explains this suffices.
- If analytics (e.g., Google Analytics) were added, a PECR-compliant consent banner would be needed.

References:
- ICO guide to PECR — <https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/>
- GOV.UK cookie banner component — <https://design-system.service.gov.uk/components/cookie-banner/>

### 2.5 Implications for requirements

- An accessibility statement page is **mandatory**, not stretch. The starter already stubs `AccessibilityStatementPage.jsx` — requirements must specify the sections that page contains (see §7 below).
- A **cookie statement or banner** is also in scope. Requirements should decide whether the service sets any non-essential cookies — if not, a static cookie notice is sufficient.
- A **privacy notice** (or stub) should be linked from the footer.
- We must commit to a specific WCAG version + level — recommend **WCAG 2.2 AA** (the current standard referenced by GOV.UK guidance, and the standard named in this brief's acceptance criteria).
- The accessibility statement must include preparation date, last-reviewed date, testing method, and a route to report problems — even if those values are placeholders for a fictional scheme.

---

## 3. GDS Service Standard

The Service Standard is a 14-point cross-government rubric every public-facing transactional service is expected to be assessed against. It is not a code standard — it shapes scope, team, research and operations decisions.

Canonical index — <https://www.gov.uk/service-manual/service-standard>

| # | Point | Relevance to this service |
|---|-------|---------------------------|
| 1 | Understand users and their needs | High — eligibility criteria and question wording must reflect real user mental models |
| 2 | Solve a whole problem | Medium — service should hand the user off cleanly to "what next" (installer, alternative schemes) |
| 3 | Joined-up experience across channels | Medium — replaces a 35-minute phone wait; the digital path must be discoverable |
| 4 | Make the service simple to use | High — one-thing-per-page, plain English |
| **5** | **Make sure everyone can use the service** | **Critical — WCAG 2.2 AA, assisted-digital, inclusive research** |
| 6 | Multidisciplinary team | N/A for this exercise |
| 7 | Agile ways of working | N/A for this exercise |
| 8 | Iterate and improve frequently | Low — but phase banner ("alpha") signals this |
| 9 | Secure service / protects privacy | Medium — income band rather than salary; no PII stored |
| 10 | Define success / publish performance data | Low for this exercise |
| 11 | Choose the right tools and technology | Low — stack chosen by brief |
| 12 | Make new source code open | Low |
| 13 | Use common components and patterns | High — directly mandates GOV.UK Design System |
| 14 | Operate a reliable service | Low for this exercise |

Point 5 in detail — <https://www.gov.uk/service-manual/helping-people-to-use-your-service/making-your-service-accessible-an-introduction>

**Service Assessments.** Conformance to the Standard is *evidenced* through formal **service assessments** at alpha, beta and live stages. A service in alpha must show its phase banner; only after a live assessment can the banner be removed. This is the context that gives the phase banner its meaning. Reference — <https://www.gov.uk/service-manual/agile-delivery/how-the-service-standard-and-service-assessments-work>.

### 3.1 Implications for requirements

- The rubric in the README already calls out four discoverable Service-Standard signals: accessibility statement, phase banner, footer, cookie notice. Requirements must enumerate each as a page or component, not bundle them.
- Privacy framing (point 9) — three income bands rather than free-text salary is already in the content plan and matches Service-Standard expectations. Requirements should make this explicit.

---

## 4. WCAG 2.2 AA

WCAG 2.2 was published as a W3C Recommendation in October 2023 and is the version GOV.UK guidance now references for public-sector compliance. It is **additive** to WCAG 2.1 — anything that conforms to 2.2 also conforms to 2.1 / 2.0.

Primary sources:
- Standard — <https://www.w3.org/TR/WCAG22/>
- Quick reference (filter by level) — <https://www.w3.org/WAI/WCAG22/quickref/>
- Understanding docs — <https://www.w3.org/WAI/WCAG22/Understanding/>

### 4.1 Four POUR principles

| Principle | Plain meaning |
|-----------|---------------|
| Perceivable | Users can see/hear/read the content (alt text, contrast, captions, reflow) |
| Operable | Users can use the controls (keyboard, focus, timing, motion) |
| Understandable | Users can read the language and predict the behaviour (labels, errors, consistency) |
| Robust | The code is parseable and works with assistive tech (semantic HTML, valid ARIA, name/role/value) |

### 4.2 Level AA criteria most load-bearing for this service

| SC | Title | Why it matters here |
|----|-------|---------------------|
| 1.1.1 | Non-text content (A) | Any icons / images need text alternatives |
| 1.3.1 | Info and Relationships (A) | Use semantic `<fieldset>`/`<legend>`, label↔input pairing |
| 1.3.5 | Identify input purpose (AA) | Programmatic autocomplete on any prefillable fields |
| 1.4.3 | Contrast (Minimum) (AA) | 4.5:1 for normal text (3:1 for large) — already in README criteria |
| 1.4.4 | Resize Text (AA) | Layout must survive 200% text scale without loss of content or function |
| 1.4.10 | Reflow (AA) | 320px width without 2-D scroll — already in README criteria |
| 1.4.11 | Non-text contrast (AA) | 3:1 for focus indicators, form borders, panel chrome |
| 1.4.12 | Text spacing (AA) | Layout must survive user-applied line-height / letter-spacing |
| 2.1.1 | Keyboard (A) | Every control reachable / operable with keyboard only |
| 2.4.3 | Focus order (A) | Tab order matches visual order |
| 2.4.7 | Focus visible (AA) | Visible focus ring — GOV.UK yellow-on-black is the convention |
| 3.3.1 | Error identification (A) | Tell the user which field, what is wrong |
| 3.3.2 | Labels or instructions (A) | Every input has a `<label>` |
| 3.3.3 | Error suggestion (AA) | Suggest a correction where possible |
| 4.1.2 | Name, role, value (A) | Custom widgets expose their state to AT |

### 4.3 New in WCAG 2.2 that are likely to bite this service

| SC | Title | Why it matters here |
|----|-------|---------------------|
| 2.4.11 | Focus Not Obscured (Minimum) (AA) | A sticky cookie banner or header must not hide the focused element |
| 2.5.7 | Dragging Movements (AA) | N/A unless a drag interaction is added |
| 2.5.8 | Target Size (Minimum) (AA) | Tap targets ≥ 24×24 CSS px or with sufficient spacing — radios, "Change" links, back link |
| 3.2.6 | Consistent Help (A) | If a help/contact mechanism is present, it must appear in the same relative location on every page |
| 3.3.7 | Redundant Entry (A) | Do not ask for the same info twice in one journey — relevant for "Change" flow from check-answers |
| 3.3.8 | Accessible Authentication (Minimum) (AA) | N/A — no auth in this service |

*(Note: 3.2.6 and 3.3.7 are new in 2.2 but at Level A. They are still required at AA conformance because AA includes all of A. Listed here because they are new and easy to overlook.)*

Direct links for the new ones:
- Focus Not Obscured (Min) — <https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html>
- Target Size (Min) — <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html>
- Consistent Help — <https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html>
- Redundant Entry — <https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html>

### 4.4 Implications for requirements

- Requirements should reference success criteria by **number**, not just "WCAG AA", so test cases map back to specific SCs.
- A focus-not-obscured check needs to be in the test plan — relevant if a phase banner or footer ever becomes sticky.
- Target Size (Min) is a real risk for the "Change" links in the summary list — they sit inline and can be small. Solution planning should specify minimum hit area.
- Redundant Entry interacts with the "Change" link behaviour: when a user returns from a change, the answer must still be pre-populated, not re-asked.

---

## 5. GOV.UK Design System

The Design System is the primary source for styles, components and patterns. Its existence is *why* the rubric distinguishes "recognisably GOV.UK" from "generic styling".

Top level — <https://design-system.service.gov.uk/>

| Section | URL | What it gives us |
|---------|-----|------------------|
| Styles | <https://design-system.service.gov.uk/styles/> | Typography scale, colour, spacing, layout grid |
| Components | <https://design-system.service.gov.uk/components/> | Button, radios, error message, summary list, panel, etc. |
| Patterns | <https://design-system.service.gov.uk/patterns/> | Question pages, check answers, confirmation, validation |
| Get started | <https://design-system.service.gov.uk/get-started/> | Labels/legends/headings, page templates, form structure |
| Accessibility | <https://design-system.service.gov.uk/accessibility/> | Cross-cutting guidance and known issues |

**Important context for this brief.** The starter scaffold deliberately re-implements GOV.UK patterns from CSS variables instead of pulling in `govuk-frontend` or `govuk-react`. The Design System remains the *behavioural and visual specification* — even though we are writing the HTML/CSS ourselves, what we build must match what those packages would produce.

### 5.1 Patterns directly required by the brief

| Pattern | URL | Acceptance criteria it backs |
|---------|-----|-----------------------------|
| Start using a service | <https://design-system.service.gov.uk/patterns/start-using-a-service/> | Start page with title, description, "Start now" button |
| Check if a service is suitable / eligibility screening | <https://design-system.service.gov.uk/patterns/check-a-service-is-suitable/> | The whole shape of this service — eligibility-screening pattern |
| Question pages (one-thing-per-page) | <https://design-system.service.gov.uk/patterns/question-pages/> | 5+ question pages with single question each |
| Check answers | <https://design-system.service.gov.uk/patterns/check-answers/> | Summary list with per-row Change links |
| Confirmation pages | <https://design-system.service.gov.uk/patterns/confirmation-pages/> | Result page panel + next steps |
| Validation | <https://design-system.service.gov.uk/patterns/validation/> | Error summary + inline errors |

The **"Check if a service is suitable"** pattern is the most directly applicable pattern to this brief — it describes exactly this shape of service (a short question flow that ends in a yes/no/partial outcome). Requirements should treat it as the *spine* of the service and other patterns as the spine's components.

### 5.2 Components that the brief and starter directly reference

| Component | URL |
|-----------|-----|
| Back link | <https://design-system.service.gov.uk/components/back-link/> |
| Button | <https://design-system.service.gov.uk/components/button/> |
| Error message | <https://design-system.service.gov.uk/components/error-message/> |
| Error summary | <https://design-system.service.gov.uk/components/error-summary/> |
| Fieldset (radios in particular) | <https://design-system.service.gov.uk/components/radios/> |
| Header | <https://design-system.service.gov.uk/components/header/> |
| Footer | <https://design-system.service.gov.uk/components/footer/> |
| Phase banner | <https://design-system.service.gov.uk/components/phase-banner/> |
| Panel | <https://design-system.service.gov.uk/components/panel/> |
| Summary list | <https://design-system.service.gov.uk/components/summary-list/> |

### 5.3 Pattern-specific rules worth capturing now

**Question pages (one-thing-per-page).** Each question page must have a back link, a single H1 that is the question (use a `<label>` inside `<h1>` for one input, or `<legend>` inside `<h1>` for a radio group), a "Continue" button (not "Next"), and no asterisks on mandatory fields. Optional fields get "(optional)" appended to the label. Reference: <https://design-system.service.gov.uk/get-started/labels-legends-headings/>.

**Check answers.** The pattern's worked example uses the title "Check your answers before sending your application"; the guidance itself only requires that the title tells the user what they need to do. Each row's "Change" link must take the user back to the question with the prior answer pre-populated, and return them to check-answers — not loop through the rest of the journey. Each Change link needs visually-hidden text naming the field ("Change *property type*"). Reference: <https://design-system.service.gov.uk/patterns/check-answers/>.

**Confirmation (result) page.** Green panel + "what happens next" + a way for the user to keep a record (print / save). **Do not put interactive elements inside the green panel** — its contrast ratio fails for buttons/links unless restyled. Reference: <https://design-system.service.gov.uk/patterns/confirmation-pages/>.

**Validation.** Title prefixed with "Error: " when errors are present. Error summary at top with heading "There is a problem" and links that jump to and focus the offending field. Inline error placed after the label/hint and before the input, with a visually-hidden "Error:" prefix in the message. Summary message text must match inline message text exactly. Focus moves to the error summary on submit when errors exist. References: <https://design-system.service.gov.uk/components/error-summary/>, <https://design-system.service.gov.uk/components/error-message/>.

**Phase banner.** While in alpha/beta, every page must show the banner with a feedback link. Wording: *"This is a new service — your feedback will help us to improve it."* (The content plan already captures this.) Reference: <https://design-system.service.gov.uk/components/phase-banner/>.

### 5.4 Implications for requirements

- Requirements should pin each acceptance criterion to a specific pattern URL — that gives the implementer a single, unambiguous reference and the assessor a checklist.
- The starter implements patterns from CSS variables. Solution planning must include a "Design System fidelity" review step (compare each rendered page to the equivalent Design System example).
- Validation is a cross-cutting concern, not a per-page concern — plan for a shared error-summary component and a per-question error renderer.

---

## 6. Content design — GOV.UK Service Manual & Content Style Guide

Visual conformance is not enough; copy must also follow the GOV.UK content style. The rubric grades "Service-Standard conformance" partly on this.

Primary sources:
- A-to-Z style guide — <https://www.gov.uk/guidance/style-guide/a-to-z-of-gov-uk-style>
- Content design overview — <https://www.gov.uk/guidance/content-design>
- Writing for GOV.UK — <https://www.gov.uk/guidance/content-design/writing-for-gov-uk>
- Form structure (one-thing-per-page) — <https://www.gov.uk/service-manual/design/form-structure>
- Designing good questions — <https://www.gov.uk/service-manual/design/designing-good-questions>

### 6.1 Key rules to encode in copy requirements

- Plain English, target reading age ~9. Sentences ≤ 25 words; flag any that exceed.
- Sentence case for headings (not Title Case). Lower-case for "government", "minister".
- Address the user as "you". Avoid jargon ("leverage", "facilitate", "deliver").
- Currency without trailing zeros — "£75", "£10,000" — not "£75.00".
- Dates as "4 June 2026" — no leading zero, no comma.
- Time ranges use "to": "10am to 11am", not "10am – 11am".
- Acronyms expanded on first use; well-known ones (NHS, BBC) need not be expanded.

### 6.2 Implications for requirements

- A "content quality" acceptance criterion separate from "renders correctly". Reviewing copy must be in the test plan, not implicit.
- The content plan in `docs/plans/2026-06-03-content-plan.md` is the source of record — requirements should reference it rather than re-stating copy.

---

## 7. Accessibility statement — what it must contain

The model statement on GOV.UK has eight sections (some wording is legally mandated). For this service it should cover:

1. **Intro** — what the statement applies to (the service URL and the body that runs it).
2. **How accessible this website is** — known issues, ordered by user impact.
3. **Feedback and contact information** — request alternative formats, contact route.
4. **Reporting accessibility problems with this website** — escalation route if the user is unhappy with the response.
5. **Enforcement procedure** — references EHRC (or ECNI in NI), routes to EASS.
6. **Technical information about this website's accessibility** — compliance status (fully / partially / not compliant) against WCAG 2.2 AA.
7. **Non-accessible content** — subsections for non-compliance, disproportionate burden, content out of scope of the regs.
8. **Preparation of this accessibility statement** — date prepared, date last reviewed, testing method, optional link to audit.

Optionally followed by: **What we're doing to improve accessibility** — roadmap.

Reference (model statement, including legally-required wording) — <https://www.gov.uk/government/publications/sample-accessibility-statement/sample-accessibility-statement-for-a-fictional-public-sector-website>

The starter scaffold already includes a `AccessibilityStatementPage.jsx` placeholder — the content plan should be extended to cover each of the seven sections.

---

## 8. Cross-browser and mobile expectations

The brief is light here ("work on both mobile and desktop browsers"). GOV.UK Frontend's own browser support matrix is a sensible floor:

- Browser compatibility (GOV.UK Frontend) — <https://frontend.design-system.service.gov.uk/browser-support/>

Practical implications:

- Tested in current versions of Chrome, Firefox, Edge, Safari (desktop) and Safari iOS / Chrome Android (mobile).
- Reflow at 320px width without horizontal scroll (WCAG 1.4.10) is already in the README criteria — this is the mobile floor.
- Test with **OS-level text scaling** (200%) and browser zoom up to 400% — covers WCAG 1.4.4 and 1.4.10.

---

## 8b. Adjacent technical standards

Not directly named by the brief, but expected for a GOV.UK-grade service:

- **Security headers (NCSC guidance for web apps).** Content-Security-Policy, Strict-Transport-Security, X-Frame-Options / `frame-ancestors`, Referrer-Policy, Permissions-Policy. For a Vite/React SPA, CSP interacts with any `<style>` injection. Reference — <https://www.ncsc.gov.uk/collection/application-development>.
- **Performance.** GDS guidance expects sub-1s server response and good Core Web Vitals (LCP, INP, CLS). No formal numeric budget is in the Service Manual, but the rubric's "simple to use" point implies it. Reference — <https://www.gov.uk/service-manual/technology/how-to-test-frontend-performance>.
- **Analytics.** GDS convention is no analytics by default, or GA4 gated on PECR-compliant consent. The brief does not require analytics — recommend none, which removes the PECR consent-banner obligation.
- **Inclusive language.** Beyond plain English, GDS recommends inclusive phrasings (e.g., "people who own their home" over "homeowners", "people who rent" over "renters"). Reference — <https://www.gov.uk/government/publications/inclusive-communication>.

## 9. How to test against these standards

This list seeds the test-plan section of the requirements doc; it is not an exhaustive QA plan.

| Layer | Tools / methods |
|-------|-----------------|
| Automated WCAG checks | axe DevTools, Lighthouse accessibility audit, WAVE |
| Manual keyboard | Tab / Shift+Tab / Enter / Space — every interaction reachable, focus visible, focus order matches visual |
| Manual screen reader | NVDA + Firefox (Windows), VoiceOver + Safari (macOS / iOS), TalkBack + Chrome (Android) — every question heard, error summary announced on submit |
| Contrast | axe contrast checker, manual sampling of focus indicator and panel chrome (1.4.11) |
| Reflow / zoom | DevTools 320px viewport, browser zoom 200% and 400% |
| Content review | Hemingway / readability check against plain-English target, manual style-guide pass |
| GOV.UK fidelity | Visual diff against Design System component examples |

References:
- GOV.UK testing for accessibility — <https://www.gov.uk/service-manual/helping-people-to-use-your-service/testing-for-accessibility>
- WAI WCAG-EM evaluation methodology — <https://www.w3.org/TR/WCAG-EM/>

---

## 10. Direction for the next phase

This research surfaces the following questions for the requirements / solution-planning work that follows:

1. **Map each rubric row to specific standards artefacts.** The README's six-row rubric is the assessment surface. Each row should resolve to one or more concrete patterns or success criteria from this document — including the AI-effectiveness row, which maps to the `AI_LOG.md` four-field schema (not a standard, but a graded artefact).
2. **Decide on WCAG version commitment.** Pick WCAG 2.2 AA (recommended) and reference SCs by number in test cases so every test traces back to a clause.
3. **Treat the accessibility statement as in-scope, not stretch.** Requirements should list each of the eight sections in §7 and the wording or placeholder for each.
4. **Decide on the cookie posture.** Two paths: (a) set no non-essential cookies and ship a static notice, or (b) accept cookies and ship a PECR-compliant consent banner. (a) is recommended for a teaching scaffold.
5. **Specify "Change" link behaviour explicitly.** Three standards interact here: GOV.UK check-answers pattern, WCAG 3.3.7 (Redundant Entry), and WCAG 2.5.8 (Target Size). Solution planning needs one definitive flow.
6. **Plan a "Design System fidelity" review** as a distinct gate from "functionality works" and "WCAG passes" — it is what the rubric grades under "GOV.UK visual compliance".
7. **Write a content acceptance check.** Copy quality (plain English, sentence case, currency formatting) is a graded standard, not a footnote.
8. **Define the eligibility-logic test strategy.** The README requires 5+ unit tests against eligibility logic; requirements should specify which scenarios those tests cover (golden paths × edge cases × each rule-priority branch).
9. **Commit to a browser-support floor.** Reference the GOV.UK Frontend support matrix; decide which browsers are formally in scope and which are best-effort.
10. **Scope out (or in) Welsh language.** A UK-wide scheme run by a UK department may be exempt from the Welsh Language (Wales) Measure 2011; a Wales-only or devolved-administration scheme would not. The brief is fictional — make the scoping call explicitly.
11. **Decide phase-banner feedback link target.** Currently `#` in the content plan. Owner and surface (email, form, GitHub issue) should be confirmed.

---

## Appendix A — Quick reference link list

**GOV.UK Design System**
- Home — <https://design-system.service.gov.uk/>
- Patterns index — <https://design-system.service.gov.uk/patterns/>
- Components index — <https://design-system.service.gov.uk/components/>
- Styles index — <https://design-system.service.gov.uk/styles/>
- Accessibility — <https://design-system.service.gov.uk/accessibility/>

**GOV.UK Service Manual**
- Service Standard — <https://www.gov.uk/service-manual/service-standard>
- Making your service accessible — <https://www.gov.uk/service-manual/helping-people-to-use-your-service/making-your-service-accessible-an-introduction>
- Testing for accessibility — <https://www.gov.uk/service-manual/helping-people-to-use-your-service/testing-for-accessibility>
- Form structure — <https://www.gov.uk/service-manual/design/form-structure>
- Designing good questions — <https://www.gov.uk/service-manual/design/designing-good-questions>

**Content style**
- A-to-Z style guide — <https://www.gov.uk/guidance/style-guide/a-to-z-of-gov-uk-style>
- Content design — <https://www.gov.uk/guidance/content-design>

**Accessibility regulations**
- Understanding the regs — <https://www.gov.uk/guidance/understanding-accessibility-requirements-for-public-sector-bodies>
- Publish an accessibility statement — <https://www.gov.uk/guidance/make-your-website-or-app-accessible-and-publish-an-accessibility-statement>
- Sample / model statement — <https://www.gov.uk/government/publications/sample-accessibility-statement/sample-accessibility-statement-for-a-fictional-public-sector-website>

**WCAG 2.2**
- Standard — <https://www.w3.org/TR/WCAG22/>
- Quick reference — <https://www.w3.org/WAI/WCAG22/quickref/>
- Understanding docs — <https://www.w3.org/WAI/WCAG22/Understanding/>
- What's new in 2.2 — <https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/>

**Privacy & cookies**
- ICO UK GDPR guide — <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/>
- ICO PECR guide — <https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/>
- DPA 2018 — <https://www.legislation.gov.uk/ukpga/2018/12/contents>
- GOV.UK cookie banner component — <https://design-system.service.gov.uk/components/cookie-banner/>

**Production packages (referenced for context — not used in this teaching scaffold)**
- govuk-frontend — <https://frontend.design-system.service.gov.uk/>
- govuk-react — <https://github.com/govuk-react/govuk-react>
- Browser support — <https://frontend.design-system.service.gov.uk/browser-support/>

---

## Appendix B — Items intentionally out of scope of this research

For traceability, these were considered and not pursued. If the next phase wants any of them, they would be additive.

- **AI_LOG.md** — graded by the rubric and required by acceptance criteria, but it is an exercise artefact rather than a standard. Format is fully specified in the seeded file at `wk03/starter/AI_LOG.md`.
- **Semantic-intent stretch challenge** (README L188–196) — out of scope for MVS; depends on `@xenova/transformers` not a public standard.
- **Save-and-return / localStorage** stretch — not a standard, though GOV.UK has a "save and return" pattern that would apply if pursued.
- **Internationalisation (RTL, locale-specific formatting)** — service is monolingual English.
- **GOV.UK Prototype Kit** — Nunjucks/Express based, not applicable to the React/Vite stack mandated by the brief.

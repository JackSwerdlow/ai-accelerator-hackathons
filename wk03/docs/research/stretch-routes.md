# Research — Stretch Goal: A Second Eligibility Pathway (tenant vs. owner routes)

> **Author:** Agent-Dale
> **Date:** 2026-06-03
> **Branch:** `research/stretch-second-pathway`
> **Status:** Initial research only — no code written. Where a decision is genuinely
> open, this document lists the options and marks a **Recommended** one, but the
> final call (and any change to PLAN.md §3/§4 decisions) belongs to the user.
> **Stretch goal under study (from [`wk03/README.md`](../../README.md) → Stretch Goals):**
> *"Add a second eligibility pathway (e.g., tenant vs. owner routes with different questions)."*

---

## 1. How to read this document

The README offers this stretch goal as one line with a parenthetical example. That
single line hides several real design decisions, because the current build was
deliberately scoped to a **single linear flow** of five questions asked of everybody
(PLAN.md §1, content plan §3). "A second pathway with different questions" means
breaking that linearity for the first time.

This document:

1. Establishes what the codebase does **today** (§2) so we know the true starting point.
2. Defines what "a second pathway" can credibly mean and recommends a target scope (§3).
3. Walks each point of ambiguity, with options + a recommendation (§4–§9).
4. Maps the concrete file-by-file impact of the recommended path (§10).
5. Flags GOV.UK / WCAG considerations that branching introduces (§11).
6. Covers testing impact (§12) and risks / scope guidance (§13).

Sections that contain an open decision end with a **Recommendation** line.

---

## 2. What the code does today

The current service is a **single linear journey**. Every user answers the same five
questions in the same order, then sees a result whose *content* varies by answer.

```
/ (start)
  → /property-type   (Q1)
  → /ownership       (Q2)   ← already captures owner vs. 3 kinds of renter
  → /income          (Q3)
  → /insulation      (Q4)
  → /heating         (Q5)
  → /check-answers
  → /result
```

Key facts that matter for this stretch goal:

| Concern | Where it lives | Current behaviour |
|---|---|---|
| Route table | `src/router.jsx` | 9 flat routes, no nesting, no conditionals |
| Per-page "next" target | hard-coded `onContinueNavigateTo` prop in each page wrapper (e.g. `src/pages/OwnershipPage.jsx` → `/income`) | Static. The flow order is encoded by these string props, not by any central config. |
| Answer state | `src/contexts/FormContext.jsx` | One flat object with exactly five keys (`propertyType`, `ownership`, `incomeBand`, `insulation`, `heating`). `INITIAL_ANSWERS` is the single source of truth. |
| Progress indicator | `src/components/ProgressIndicator.jsx` + a hard-coded `step` / `totalSteps={5}` prop on every page | Each page literally passes `step={2} totalSteps={5}`. Already flagged in-code as a non-GOV.UK custom component. |
| Check-answers rows | `src/pages/CheckAnswersPage.jsx` → `FIELD_ORDER` (hard-coded array of 5) | Renders exactly those five fields and **redirects to the first missing one**. Any field left blank bounces the user out of check-answers. |
| Result guards | `src/pages/ResultPage.jsx` → `FIELDS` (hard-coded array of 5) | If *any* of the five is empty, redirect to `/`. |
| Eligibility rules | `src/eligibility.js` (pure fn) | Priority-ordered rules. **Crucially, it already branches on ownership**: renters → `partial` / `renter`; owners split by income. |

### 2.1 The important nuance

There is **already a partial owner-vs-tenant divergence** — but only at the *outcome*
layer, not the *question* layer:

- `eligibility.js` already routes renters to a distinct `partial` / `renter` result, and
  `ResultPage.jsx` already renders bespoke "ask your landlord to apply" copy for them.
- What does **not** differ today is the *questions asked*. A private renter is still
  asked about their household income and their current insulation, even though (per the
  service's own narrative) tenants cannot apply independently and their landlord drives
  the works.

So the stretch goal is really: **make the *questions* diverge by tenure, not just the
result copy.** That framing is what the rest of this document plans against.

---

## 3. What "a second pathway" should mean here — scope options

**Ambiguity:** "Different questions" is open-ended. How divergent should the two paths be?

| Option | Description | Effort | Demonstrates |
|---|---|---|---|
| **A — Outcome-only (status quo+)** | Keep one question set; only enrich the result copy per tenure. | ~none (largely done) | Nothing new — does not satisfy the stretch goal's "different questions". |
| **B — Shared prefix, divergent middle, shared tail** ⭐ | Q1 (property) and Q2 (ownership) are shared. After Q2, branch: owners get owner-specific questions, tenants get tenant-specific questions. Both converge on check-answers → result. | Moderate | Real branching, one genuinely different question per path, a path-aware summary, and a path-aware eligibility rule. Hits the rubric's "Functionality / eligibility logic handles all paths" without exploding scope. |
| **C — Two fully separate journeys** | Separate start choice → entirely independent owner and tenant flows with their own routes, state slices, and result pages. | High | Most "complete" but duplicates chrome, doubles the test surface, and risks regressing the clean single-flow MVP. Overkill for a hackathon stretch. |

**Recommendation: Option B.** It is the smallest change that genuinely satisfies
"tenant vs. owner routes with different questions," keeps the shared chrome / check-answers
/ result scaffolding, and reuses the existing generic `<QuestionPage>` component. It also
matches GOV.UK's own guidance to *"use 'branching' questions so people only have to answer
questions that are relevant to them"* (Structuring forms — see §11) rather than building a
parallel sub-app.

The rest of this document assumes **Option B**.

---

## 4. Where to branch, and on what

**Ambiguity:** What is the branch trigger — the existing 4-way `ownership` field, or a new
coarser owner/tenant split?

| Option | Description | Notes |
|---|---|---|
| **A — Derive from existing `ownership`** ⭐ | After Q2, treat `owner` as the owner path and the three renter values (`private-renter`, `housing-association`, `council`) as the tenant path. A tiny helper `isTenant(answers.ownership)` (mirroring the existing `RENTER_OWNERSHIPS` set in `eligibility.js`) decides the route. | No new question, no new state key. Reuses logic already proven by the eligibility renter rule. |
| **B — Add an explicit "are you an owner or a tenant?" question** | Insert a new binary question before/after ownership. | Redundant with `ownership`, adds a screen, risks contradictory answers (owner-or-tenant says "owner" but ownership says "council"). Avoid. |

**Recommendation: Option A.** Reuse `ownership`. Lift the renter-set test into a shared
helper so the router and `eligibility.js` agree on who is a tenant (single source of truth —
today the set is private to `eligibility.js`).

**Branch point:** after **Q2 Ownership**. Q1 (property type) and Q2 (ownership) stay shared
because both paths need them (property type still feeds the measures list; ownership is the
branch key itself).

---

## 5. What the divergent questions should be

**Ambiguity:** The README only says "different questions" — it does not specify *which*.
These are fictional-scheme questions, so we have latitude, but they should be plausible and
should *change the eligibility outcome* (otherwise the branch is cosmetic).

### 5.1 Owner path (after Q2)

Keep the existing owner-relevant questions, optionally add one owner-only gate:

| Question | Field | Why it belongs to owners | Affects outcome? |
|---|---|---|---|
| Household income (existing Q3) | `incomeBand` | Owner grant tier depends on income (existing rules 4 & 5). | Yes (already). |
| Existing insulation (existing Q4) | `insulation` | Drives measures + the "no measures needed" rule. | Yes. |
| Current heating (existing Q5) | `heating` | Drives measures + the "no measures needed" rule. | Yes. |
| *(optional new)* Is this your main home? | `mainResidence` | Plausible owner-only gate; second homes excluded. | Yes — new ineligible rule. |

### 5.2 Tenant path (after Q2)

Replace income/insulation/heating-for-self with tenant-relevant questions. **Recommended
minimum is one genuinely different, outcome-bearing question** so the branch is real:

| Question | Field | Rationale | Affects outcome? |
|---|---|---|---|
| **Do you have your landlord's permission to make improvements?** | `landlordConsent` (`yes` / `no` / `not-sure`) ⭐ | This is the real-world gating factor for tenant retrofit schemes and gives a meaningful new outcome split: `no` → signpost-landlord, `yes` → partial/landlord-applies. | **Yes** — primary recommended new question. |
| *(optional)* Tenancy type | `tenancyType` (assured shorthold / social / other) | Adds realism; could refine which landlord-route copy shows. | Optional. |
| Existing insulation | `insulation` | Still useful to populate the measures the landlord would apply for. Can be **kept** in the tenant path so measures still render. | Yes (measures). |

**Note on income for tenants:** today's flow asks tenants their household income, but the
renter rule ignores it (renters are `partial` regardless of income unless income is `high`,
which is checked first). Two sub-options:

- **5.b.i — Drop income from the tenant path.** Cleaner ("only relevant questions"), but
  then the `incomeBand === 'high'` top-priority ineligible rule no longer fires for tenants.
  Decide whether a high-income tenant should still be excluded.
- **5.b.ii — Keep income in the tenant path.** Preserves the existing high-income gate for
  everyone; less divergent.

**Recommendation:** Tenant path = `landlordConsent` (new) + `insulation` (kept for measures),
and **drop** income from the tenant path (5.b.i) — but **only if** product accepts that the
high-income exclusion is owner-only. If the high-income gate must apply to everyone, keep
income (5.b.ii). Flag this to the user; it changes the rules table.

> Minimum viable version of this stretch goal = **one** new tenant-only question
> (`landlordConsent`) with **one** new outcome branch. Everything else in §5 is optional polish.

---

## 6. Routing approach

**Ambiguity:** The flow order is currently encoded as static `onContinueNavigateTo` strings
on each page. Branching needs the "next" target to depend on state.

| Option | Description | Trade-offs |
|---|---|---|
| **A — Conditional `onContinueNavigateTo` computed from state** ⭐ | The Ownership page (the branch point) computes its next route at Continue-time: `isTenant(ownership) ? '/tenant/consent' : '/income'`. Downstream pages keep static `next` props because each path is itself linear. | Smallest delta from current design. `<QuestionPage>` already calls `navigate()`; we either pass a function instead of a string for `onContinueNavigateTo`, or compute the value in the wrapper. Pages stay dumb. |
| **B — Central flow config / state machine** | A single ordered list (or `xstate`-style machine) describes both paths; pages ask the config "what's next given current answers". | Cleaner for *many* branches; over-engineered for one branch. Adds a dependency or a hand-rolled engine and a refactor of all five existing pages. |
| **C — Nested routes (`/owner/*`, `/tenant/*`)** | React Router nested routes per path. | Tidy URLs, but forces restructuring `router.jsx` and the check-answers/result guard logic; more churn than the branch warrants. |

**Recommendation: Option A**, with a small enhancement: allow `onContinueNavigateTo` to be
**either a string or a function of `answers`**. At the branch page (Ownership) pass a
function; everywhere else keep the existing strings. This is a backward-compatible change to
`QuestionPage.handleContinue` (≈3 lines) and leaves the other four pages untouched.

New routes to add to `router.jsx` (names illustrative):

```
/tenant/consent     → LandlordConsentPage   (tenant-only)
# owner path reuses existing /income, /insulation, /heating
# tenant path: /tenant/consent → /insulation → /check-answers
```

(Exact tenant route list depends on the §5 decision about which questions the tenant path keeps.)

---

## 7. State model

**Ambiguity:** `FormContext` holds exactly five fixed keys. New per-path fields
(`landlordConsent`, maybe `mainResidence`) must live somewhere, and path-irrelevant fields
must not break the check-answers "redirect if any field empty" guard.

| Option | Description | Trade-offs |
|---|---|---|
| **A — One flat object, all keys, path-aware completeness** ⭐ | Add the new keys to `INITIAL_ANSWERS`. Replace the "all five present" checks with a **path-aware required-field list** (see §8). | Minimal structural change; keeps a single state object. Requires touching the two hard-coded field arrays. |
| **B — Nested per-path slices** (`answers.owner = {…}`, `answers.tenant = {…}`) | Separate sub-objects per path. | Avoids mixing irrelevant fields but ripples through every `answers[field]` read in `QuestionPage`, check-answers, result, and `eligibility.js`. High churn for little gain. |

**Recommendation: Option A.** Keep one flat object. The only real work is replacing the
three hard-coded "these exact five fields" assumptions (in `FormContext` initial state,
`CheckAnswersPage.FIELD_ORDER`, and `ResultPage.FIELDS`) with a **path-derived required-field
list**. See §8.

---

## 8. Check-answers and result guards (the sharpest edge)

This is the most fragile area, because three places hard-code "exactly these five fields,"
and two of them **redirect the user away** if any are missing:

- `CheckAnswersPage.jsx` → `FIELD_ORDER` (5 rows) + redirect to first missing field.
- `ResultPage.jsx` → `FIELDS` (5) + redirect to `/` if any missing.
- `FormContext.INITIAL_ANSWERS` (5 keys).

If we simply add tenant fields, an **owner** who never visited `/tenant/consent` will have an
empty `landlordConsent`, and the check-answers guard will bounce them to the tenant question —
a broken loop. So the required-field set **must become a function of the chosen path.**

**Recommendation:** Introduce a single helper, e.g.

```js
// requiredFields(answers) → string[]   (the fields THIS path must have)
// rows/summary, check-answers guard, and result guard all consume this.
```

Derive the path from `answers.ownership` via the shared `isTenant()` helper (§4). Then:

- `CheckAnswersPage` builds `FIELD_ORDER` from `requiredFields(answers)` so tenants see the
  tenant rows and owners see the owner rows.
- Both guards check only the path's required fields, not a fixed five.

This is the **single most important refactor** in the whole stretch goal — get it wrong and
the journey dead-ends. Recommend implementing and testing this *before* adding any new
question screen.

---

## 9. Eligibility rule changes

`eligibility.js` already branches on tenure, so the change is additive, not a rewrite. The
new tenant-only question needs a rule.

Proposed additions (priority order matters — slots **above** the existing generic `renter`
rule so the more specific case wins):

```
(existing) Rule 1  income high            → ineligible / income-too-high
(existing) Rule 2  full insul + heat pump → ineligible / no-measures-needed
(NEW)      Rule 3  tenant + consent = no  → ineligible / no-landlord-consent
(NEW/opt)  Rule 3b tenant + consent = not-sure → partial / renter-check-landlord
(existing) Rule 4  any renter             → partial / renter
(existing) Rule 5  owner + mid income     → partial / owner-mid-income
(existing) Rule 6  owner + low income     → eligible / owner-low-income
(NEW/opt)  Rule 0  owner + not main home  → ineligible / second-home   (if §5.1 gate added)
```

Open decisions to flag:
- Whether `incomeBand === 'high'` should still gate tenants (ties to §5.b decision).
- Exact reason codes — each new `reason` needs matching copy in `ResultPage.jsx` and the
  content plan, or the result page will render a blank body for that branch.

**Recommendation:** Add **Rule 3 (no consent → ineligible)** as the one required new rule,
plus its result copy. Treat 3b / second-home as optional stretch-within-stretch.

---

## 10. File-by-file impact map (for the recommended Option B path)

| File | Change | Size |
|---|---|---|
| `src/eligibility.js` | Add tenant-consent rule(s); export shared `isTenant()` / renter-set helper. | Small |
| `src/contexts/FormContext.jsx` | Add new key(s) to `INITIAL_ANSWERS`; optionally add `requiredFields()` helper or keep it standalone. | Small |
| `src/components/QuestionPage.jsx` | Let `onContinueNavigateTo` accept a function of `answers` (branch at Ownership). | ~3 lines |
| `src/pages/OwnershipPage.jsx` | Pass a function for `onContinueNavigateTo` that routes by tenure. | Small |
| `src/pages/LandlordConsentPage.jsx` *(new)* | New tenant-only `<QuestionPage>` wrapper. | New, small (mirrors existing wrappers) |
| `src/router.jsx` | Register the new tenant route(s). | Small |
| `src/pages/CheckAnswersPage.jsx` | Build `FIELD_ORDER` from path-aware `requiredFields(answers)`; fix the "redirect if missing" guard. | **Medium — highest risk** |
| `src/pages/ResultPage.jsx` | Path-aware completeness guard; new result copy block(s) for the new reason code(s). | Medium |
| `src/displayLabels.js` | Add labels for the new field's values (e.g. landlord consent yes/no/not-sure). | Small |
| `src/components/ProgressIndicator.jsx` + page `step`/`totalSteps` props | Decide how to handle a now-variable step count (see §11.2). | Small–Medium |
| `src/__tests__/eligibility.test.js` | Tests for new rule branches. | Small |
| `src/__tests__/QuestionPage.test.jsx` / new flow test | Cover the branch + the path-aware check-answers guard. | Medium |
| `docs/plans/2026-06-03-content-plan.md` | New question copy, new result copy, new labels, updated rules table. **Content is "fixed by the content plan" per PLAN.md — update it, don't invent copy ad hoc.** | Medium |

---

## 11. GOV.UK & WCAG 2.2 AA considerations introduced by branching

Branching is itself endorsed by GOV.UK — the Service Manual says to *"use 'branching'
questions so people only have to answer questions that are relevant to them"*
([Structuring forms](https://www.gov.uk/service-manual/design/form-structure)). But it has
knock-on effects on patterns the current build uses.

### 11.1 Back-link behaviour
The GOV.UK Question pages pattern says *"Always include a Back link… to reassure [users] it's
possible to go back and change previous answers."* The current `QuestionPage` uses a **static
`backHref`**. On a tenant-only page the Back link must return to **Ownership**, not to a
shared `/income`. When entered from check-answers (`?from=check-answers`), Back/Continue
already returns to check-answers — verify this still holds for the new page. **Action:** the
new tenant page needs a correct static `backHref` (`/ownership`); no dynamic back logic is
required because each path is linear once branched.

### 11.2 Progress indicator — the real tension
GOV.UK guidance is explicit that step counters are optional and, when used with branching,
must stay accurate: *"only include the total number of questions if you can do so reliably…
make sure the indicator updates."* It notes services (e.g. Carer's Allowance) **removed**
step indicators with no negative effect. The current app hard-codes `Step X of 5` on every
page — which becomes **factually wrong** the moment the tenant path has a different number of
questions.

| Option | Description |
|---|---|
| **A — Remove the step indicator** ⭐ | Simplest, and explicitly blessed by GOV.UK guidance. Deletes a non-GOV.UK custom component (already flagged as such in its own source comment). |
| **B — Make it path-aware** | Compute `step`/`total` from the path's required-field list. More code; must update on branch; easy to get off-by-one. |
| **C — Switch to "Question N" only (no total)** | GOV.UK-acceptable middle ground when the total is unreliable. |

**Recommendation: Option A (remove it)** as part of this work, or **C** if the team wants to
keep a sense of progress. Keeping a hard-coded "of 5" (current behaviour) is **not** an option
once paths diverge — it would mislead tenant-path users and is a GOV.UK guidance violation.

### 11.3 One thing per page
Both new questions stay single-question radio pages — fully consistent with the existing
pattern and the "one thing per page" principle. No conflict.

### 11.4 Focus management & titles
`App.jsx` already moves focus to `<main>` on every route change, and `QuestionPage` sets the
document title (with an `Error:` prefix on validation failure). New pages inherit both for
free by reusing `<QuestionPage>` — **no new accessibility work** beyond labelling the new
radios (which the component handles).

---

## 12. Testing impact

- **Unit (`eligibility.test.js`):** add cases for each new rule branch (no-consent →
  ineligible; consent variants). The existing suite is branch-per-test, so follow that style.
  This also keeps the README's "≥5 eligibility unit tests" criterion comfortably satisfied.
- **Component / flow:** the existing `QuestionPage.test.jsx` covers a generic page. Add (a) a
  test that Ownership routes owners vs. tenants to different next routes, and (b) the
  **path-aware check-answers guard** — assert an owner is *not* bounced to the tenant
  question, and a tenant *is* asked for consent. §8 is the regression-prone area, so it needs
  the most explicit coverage.
- **E2E (Playwright, already in repo per recent commits):** extend the smoke journey with a
  second run-through that takes the tenant branch end-to-end.

---

## 13. Risks, scope guidance, and a recommended increment order

**Risks**
1. **Check-answers / result redirect guards (§8)** are the highest-risk change — a wrong
   required-field set produces an infinite redirect or a dead-end. Build and test this first.
2. **Reason-code/copy drift** — every new `reason` string in `eligibility.js` must have a
   matching block in `ResultPage.jsx` and the content plan, or the result renders blank.
3. **Content-plan ownership** — PLAN.md treats copy as fixed by the content plan; new copy
   should be added *there* and flagged to the user, not improvised in JSX.
4. **Scope creep** — Option C (two full journeys) is tempting but doubles the surface; resist.

**Recommended increment order (each step independently shippable):**
1. Extract `isTenant()` + a `requiredFields(answers)` helper; refactor the two guards and
   check-answers to use it **with the current five fields** (pure refactor, no behaviour
   change — prove it green).
2. Allow `onContinueNavigateTo` to be a function; branch at Ownership (owners → existing
   flow; tenants → existing flow for now). Still no new question — proves routing.
3. Add the one new tenant question (`landlordConsent`) + route + labels + content.
4. Add the one new eligibility rule + result copy + unit tests.
5. Resolve the progress-indicator decision (§11.2).
6. Extend Playwright with the tenant journey.

This ordering means the branch infrastructure is proven *before* any user-visible question
changes, and every step leaves `main` shippable.

---

## 14. Open decisions to confirm with the user (consolidated)

| # | Decision | Recommendation | Section |
|---|---|---|---|
| 1 | Scope of the second pathway | Option B — shared prefix, divergent middle | §3 |
| 2 | Branch trigger | Reuse existing `ownership` via `isTenant()` | §4 |
| 3 | Which tenant question(s) to add | `landlordConsent` (required); insulation kept for measures | §5 |
| 4 | Keep income on the tenant path? | Drop it **iff** high-income gate may be owner-only; else keep | §5.b |
| 5 | Optional owner gate (main residence)? | Optional / defer | §5.1 |
| 6 | Routing mechanism | Function-valued `onContinueNavigateTo` at branch point | §6 |
| 7 | State shape | One flat object + path-aware required-field list | §7 |
| 8 | Progress indicator fate | Remove it (or "Question N" without total) | §11.2 |
| 9 | How far to take rules (3b / second-home) | Ship Rule 3 only; rest optional | §9 |

---

## 15. Sources

- GOV.UK Design System — Question pages (one thing per page, back links, progress indicators):
  <https://design-system.service.gov.uk/patterns/question-pages/>
- GOV.UK Service Manual — Structuring forms ("use branching questions"):
  <https://www.gov.uk/service-manual/design/form-structure>
- GOV.UK Design System — Step by step navigation (for contrast with question-page progress patterns):
  <https://design-system.service.gov.uk/patterns/step-by-step-navigation/>
- Existing in-repo standards research: [`docs/research/research.md`](./research.md) (§4 WCAG, §5 GOV.UK patterns)
- Codebase as of branch `research/stretch-second-pathway`:
  `src/router.jsx`, `src/eligibility.js`, `src/contexts/FormContext.jsx`,
  `src/components/QuestionPage.jsx`, `src/pages/CheckAnswersPage.jsx`, `src/pages/ResultPage.jsx`
- Fixed copy / rules source of truth: [`docs/plans/2026-06-03-content-plan.md`](../plans/2026-06-03-content-plan.md)

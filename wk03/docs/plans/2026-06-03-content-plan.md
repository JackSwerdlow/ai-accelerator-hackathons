# Green Home Grant – Content Plan

**Author:** Agent-Jack  
**Date:** 2026-06-03  
**Status:** Draft — to be collated with plans from other agents into a single implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the exact words, options, rules, and outcomes for the Green Home Grant eligibility checker so that any developer can build the service without inventing content.

**Architecture:** Content-only plan — no code structure decisions. Covers service narrative, all five question pages, eligibility rules in plain language, and result messages for each possible outcome. A separate implementation plan will handle code.

**Tech Stack:** React + react-router-dom + Vite, GOV.UK CSS variables (no govuk-frontend npm package — teaching scaffold).

---

## 1. Service Identity

| Element | Content |
|---------|---------|
| Service name | Green Home Grant |
| GOV.UK header service name | Green Home Grant |
| Phase | ALPHA |
| Phase banner text | This is a new service – your feedback will help us to improve it. |
| Feedback link label | feedback |
| Feedback link href | `#` (placeholder — no real survey yet) |

---

## 2. Start Page

The GOV.UK start page pattern has three parts: a title, a description (what the service does and who it is for), and a "Start now" button.

### Page title
```
Check if you can get a Green Home Grant
```

### Description paragraphs

```
Use this service to find out whether you qualify for a Green Home Grant.

The grant helps homeowners and tenants get funding toward home insulation
and heat pump installation to reduce energy bills and carbon emissions.

The check takes around 2 minutes. You will need to know:

- the type of property you live in
- whether you own or rent
- your total annual household income
- whether your home currently has insulation
- your current main heating system
```

### Button
- Label: `Start now`
- Variant: start (chevron icon)
- Navigates to: `/property-type`

---

## 3. Question Pages

### Question 1 — Property Type

| Element | Content |
|---------|---------|
| Route | `/property-type` |
| Back link | `/` (Start page) |
| Page heading | What type of property do you live in? |
| Input type | Radio buttons |
| Error message | Select the type of property you live in |

**Options (in order):**

| Value | Display label |
|-------|--------------|
| `detached` | Detached house |
| `semi-detached` | Semi-detached house |
| `terraced` | Terraced house |
| `flat` | Flat or apartment |
| `bungalow` | Bungalow |

No hint text needed — options are self-explanatory.

---

### Question 2 — Ownership Status

| Element | Content |
|---------|---------|
| Route | `/ownership` |
| Back link | `/property-type` |
| Page heading | What is your ownership status? |
| Input type | Radio buttons |
| Hint text | If you own your home with a mortgage, select "I own my home". |
| Error message | Select your ownership status |

**Options (in order):**

| Value | Display label |
|-------|--------------|
| `owner` | I own my home |
| `private-renter` | I rent from a private landlord |
| `housing-association` | I rent from a housing association |
| `council` | I rent from a council or local authority |

---

### Question 3 — Household Income

| Element | Content |
|---------|---------|
| Route | `/income` |
| Back link | `/ownership` |
| Page heading | What is your total annual household income? |
| Input type | Radio buttons |
| Hint text | Include the income of all adults living in your home, before tax and other deductions. |
| Error message | Select your annual household income |

**Options (in order):**

| Value | Display label |
|-------|--------------|
| `low` | Under £31,000 |
| `mid` | £31,000 to £60,000 |
| `high` | Over £60,000 |

---

### Question 4 — Existing Insulation

| Element | Content |
|---------|---------|
| Route | `/insulation` |
| Back link | `/income` |
| Page heading | What insulation does your home currently have? |
| Input type | Radio buttons |
| Hint text | If you are not sure, check your Energy Performance Certificate (EPC). Your landlord or mortgage provider may have a copy. |
| Error message | Select the insulation your home currently has |

**Options (in order):**

| Value | Display label |
|-------|--------------|
| `none` | No insulation |
| `partial` | Some insulation (for example, loft only or walls only) |
| `full` | Full insulation (loft and walls) |

---

### Question 5 — Current Heating System

| Element | Content |
|---------|---------|
| Route | `/heating` |
| Back link | `/insulation` |
| Page heading | What is your current main heating system? |
| Input type | Radio buttons |
| Hint text | Select the system that heats most of your home. |
| Error message | Select your current main heating system |

**Options (in order):**

| Value | Display label |
|-------|--------------|
| `gas-boiler` | Gas boiler |
| `oil-boiler` | Oil boiler |
| `electric-storage` | Electric storage heaters |
| `heat-pump` | Heat pump (air source or ground source) |
| `other` | Other |

---

## 4. Check Your Answers Page

| Element | Content |
|---------|---------|
| Route | `/check-answers` |
| Back link | `/heating` |
| Page heading | Check your answers |
| Intro paragraph | Check your answers before you find out if you are eligible. |
| Submit button label | Submit and see result |

**Summary list rows:**

| Row label | Source field | Change link destination |
|-----------|-------------|------------------------|
| Property type | `propertyType` | `/property-type` |
| Ownership status | `ownership` | `/ownership` |
| Annual household income | `incomeBand` | `/income` |
| Current insulation | `insulation` | `/insulation` |
| Current heating system | `heating` | `/heating` |

Each row has a "Change" link that takes the user back to that question and then returns them to `/check-answers` after answering.

**Display labels for stored values** (used to render human-readable answers in the summary):

| Field | Value | Display label |
|-------|-------|--------------|
| propertyType | `detached` | Detached house |
| propertyType | `semi-detached` | Semi-detached house |
| propertyType | `terraced` | Terraced house |
| propertyType | `flat` | Flat or apartment |
| propertyType | `bungalow` | Bungalow |
| ownership | `owner` | I own my home |
| ownership | `private-renter` | I rent from a private landlord |
| ownership | `housing-association` | I rent from a housing association |
| ownership | `council` | I rent from a council or local authority |
| incomeBand | `low` | Under £31,000 |
| incomeBand | `mid` | £31,000 to £60,000 |
| incomeBand | `high` | Over £60,000 |
| insulation | `none` | No insulation |
| insulation | `partial` | Some insulation |
| insulation | `full` | Full insulation |
| heating | `gas-boiler` | Gas boiler |
| heating | `oil-boiler` | Oil boiler |
| heating | `electric-storage` | Electric storage heaters |
| heating | `heat-pump` | Heat pump |
| heating | `other` | Other |

---

## 5. Eligibility Rules

The eligibility function takes the five answers and returns one of three result strings: `"eligible"`, `"partial"`, or `"ineligible"`.

Rules are evaluated in priority order (top rule that matches wins):

### Rule 1 — Income too high → NOT ELIGIBLE
If `incomeBand === "high"`, return `"ineligible"` regardless of all other answers.

### Rule 2 — No measures needed → NOT ELIGIBLE
If `insulation === "full"` AND `heating === "heat-pump"`, return `"ineligible"`.
The home already has everything the grant covers.

### Rule 3 — Renter → PARTIAL
If `ownership === "private-renter"` OR `ownership === "housing-association"` OR `ownership === "council"`, return `"partial"`.
Tenants need their landlord to be involved; they cannot apply independently.

### Rule 4 — Owner, mid income → PARTIAL
If `ownership === "owner"` AND `incomeBand === "mid"`, return `"partial"`.

### Rule 5 — Owner, low income → ELIGIBLE
If `ownership === "owner"` AND `incomeBand === "low"`, return `"eligible"`.

### Default → NOT ELIGIBLE
Any combination not matched above returns `"ineligible"`.

---

## 6. Measures Available (for result page content)

Used to tell users specifically what they could get funding for. Computed alongside the eligibility result.

| Condition | Measure offered |
|-----------|----------------|
| `insulation !== "full"` AND `propertyType !== "flat"` | Loft insulation |
| `insulation !== "full"` | Internal wall insulation |
| `heating !== "heat-pump"` | Air source heat pump installation |

A flat can get internal wall insulation and a heat pump, but not loft insulation (no accessible loft).

---

## 7. Result Page

Route: `/result`  
Back link: none (do not allow back-navigation to change answers after submission — use "Check your answers" page for that)

The result page uses a GOV.UK panel component at the top, followed by detail paragraphs and a next-steps section.

---

### Outcome A — ELIGIBLE

**Panel:**
- Panel title: `You may be eligible for a Green Home Grant`
- Panel body (low income): `You may qualify for a grant of up to £10,000`

**Body paragraphs:**
```
Based on your answers, your home could qualify for the following measures:

[bulleted list of available measures — derived from section 6 above]

The grant covers up to two-thirds of the cost of each measure, up to the
maximum grant amount.
```

**Next steps heading:** `What to do next`

**Next steps paragraphs:**
```
Contact an approved Green Home Grant installer to assess your property.
They will confirm which measures are suitable and apply for the grant on
your behalf.

You do not need to pay anything upfront. The installer will claim the grant
directly from the scheme administrator.
```

**Link:** `Find an approved installer` (href: `#` — placeholder)

---

### Outcome B — PARTIAL

**Panel:**
- Panel title: `You may be partially eligible for a Green Home Grant`
- Panel body: (empty — detail is in body paragraphs)

**Body paragraphs — if renter:**
```
As a tenant, your landlord needs to apply for this grant on your behalf.

We can send you an information pack to share with your landlord. It
explains the grant, the installation process, and how to apply.
```

**Body paragraphs — if owner with mid income:**
```
Based on your income band, you may qualify for a partial grant of up to
£5,000.

Your home could qualify for the following measures:

[bulleted list of available measures]
```

**Next steps heading:** `What to do next`

**Next steps — if renter:**
```
Ask your landlord to contact an approved installer for a property
assessment. Landlords can apply directly through the Green Home Grant
scheme.
```

**Next steps — if owner mid income:**
```
Contact an approved Green Home Grant installer to assess your property.
The installer will apply for the grant on your behalf.
```

**Link:** `Find an approved installer` (href: `#` — placeholder)

---

### Outcome C — NOT ELIGIBLE

**Panel:**
- Panel title: `You are not eligible for a Green Home Grant`
- Panel body: (empty)

**Body paragraphs — if income too high:**
```
Your household income is above the threshold for this grant.
```

**Body paragraphs — if already fully insulated and has heat pump:**
```
Your home already has the insulation and heating measures this grant
covers. No further measures are available under this scheme.
```

**Body paragraphs — shown in all ineligible cases:**
```
You may still be able to improve your home's energy efficiency through
other government schemes.
```

**Link:** `Find other energy efficiency schemes` (href: `#` — placeholder)

---

## 8. Error Message Pattern

Every question page follows the same GOV.UK error pattern:

1. The `<title>` element gains the prefix `Error: ` when a validation error is present
2. An error summary box appears at the top of the `<main>` area:
   - Heading: `There is a problem`
   - A list item linking to the first errored field
3. An inline error message appears directly above the errored input, prefixed with a visually hidden `Error:` span

**Generic format for inline error:**  
`Error: [field-specific error message from section 3 above]`

---

## 9. Accessibility Statement

Route: `/accessibility-statement`  
Linked from the GOV.UK footer.

The statement follows the Public Sector Bodies Accessibility Regulations (PSBAR) structure. Key content:

| Field | Content |
|-------|---------|
| Service name | Green Home Grant eligibility checker |
| Compliance status | Partially compliant with WCAG 2.2 level AA |
| Known issues | None identified at time of writing (placeholder — update after accessibility audit) |
| Preparation date | 2026-06-03 |
| Last reviewed | 2026-06-03 |
| Contact email | accessibility@greengrant.gov.uk (placeholder) |

---

## 10. Footer Links

The GOV.UK footer should contain at minimum:

| Link label | Destination |
|------------|-------------|
| Accessibility statement | `/accessibility-statement` |
| Cookies | `#` (placeholder — no real cookie policy) |

---

## Content Decisions & Rationale

| Decision | Reason |
|----------|--------|
| Three income bands (not a free-text field) | Avoids users entering exact salaries; reduces friction and protects privacy. Bands match simplified Housing Benefit thresholds. |
| "Partial" outcome for all renters regardless of income | Landlord involvement is always required; eligibility cannot be confirmed without it. Simpler to route all renters to partial. |
| No branching on property type for eligibility outcome | Property type affects *measures available*, not eligibility itself. Keeps the question flow linear and predictable. |
| Flat cannot get loft insulation | Physical reality — flats typically have no accessible loft. Prevents unrealistic measure suggestions. |
| No back link on result page | Prevents users from using browser Back to silently re-submit. "Change" links on the check-answers page are the intended route for corrections. |
| Grant amount shown as "up to £10,000 / £5,000" | Actual amount depends on installer quote and approved measures — an exact figure cannot be given. "Up to" sets a ceiling without misleading. |

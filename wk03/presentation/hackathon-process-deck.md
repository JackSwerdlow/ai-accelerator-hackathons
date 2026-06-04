---
marp: true
theme: default
paginate: true
html: true
style: |
  :root {
    --gov-blue: #1d70b8;
    --gov-black: #0b0c0c;
    --gov-green: #00703c;
    --gov-grey: #505a5f;
    --gov-yellow: #ffdd00;
  }
  section {
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 26px;
    color: var(--gov-black);
    padding: 50px 60px;
  }
  h1 { color: var(--gov-black); border-bottom: 6px solid var(--gov-blue); padding-bottom: 8px; }
  h2 { color: var(--gov-blue); }
  a { color: var(--gov-blue); }
  strong { color: var(--gov-black); }
  code { background: #f3f2f1; padding: 1px 5px; border-radius: 3px; }
  table { font-size: 0.8em; }
  section.lead h1 { border: none; font-size: 2.2em; }
  section.lead { background: var(--gov-black); color: #fff; }
  section.lead h1, section.lead h2 { color: #fff; border: none; }
  section.lead strong { color: var(--gov-yellow); }
  .small { font-size: 0.72em; color: var(--gov-grey); }
  .tag { background: var(--gov-blue); color:#fff; padding:2px 8px; border-radius:3px; font-size:0.7em; }
  /* Diagrams are pre-rendered to PNG (see build step in README); fit them to the slide.
     Fixed px max-height (not %) so it resolves in Marp's layout and tall diagrams don't overflow. */
  img { display:block; margin: 8px auto 0; max-width: 100%; max-height: 340px; }
---

<!-- _class: lead -->

# Building a GOV.UK Service with an **Agent Team**

## How we ran a hackathon like a software org — not a single prompt

<br>

**Green Home Grant** eligibility checker
A process retrospective for engineers

<span class="small">Agent-Dale · week-3 AI accelerator hackathon · 2026-06-04</span>

---

# The brief

A fictional government department needs to tell citizens whether they qualify
for a **Green Home Grant** (insulation + heat-pump funding).

- Today: citizens **phone a call centre** and wait ~35 minutes for an answer.
- Goal: a **digital self-service** eligibility checker that replaces that call.

**Hard constraints that shaped every decision:**

| Constraint | Implication |
|---|---|
| GOV.UK Design System | One-thing-per-page, check-answers, confirmation patterns |
| WCAG 2.2 AA | Labelled inputs, keyboard-only, focus mgmt, error summary |
| Mobile + desktop | Reflow at 320px, no horizontal scroll |
| Service Standard signals | Phase banner, accessibility statement, footer, cookies |

---

# The thesis of this talk

> The interesting artefact wasn't the app. It was the **process** —
> we ran multiple AI agents the way you'd run a software team.

What that meant in practice:

- **Agent identities** committing to a **shared git repo** under a strict workflow.
- **Planning-first**: content + standards + architecture settled *before* code.
- **Subagent-driven development**: every code chunk built then independently reviewed.
- **An audit trail** (`AI_LOG.md`) recording *what AI produced* vs *what a human changed and why*.

The rest of these slides walk the pipeline, with the diagrams that explain it.

---

# The cast — agents on a shared repo

Each contributor worked under a stable **agent identity**, enforced by `CLAUDE.md`:
every commit and log entry is prefixed `[Agent-Name]`.

| Agent | Primary contribution |
|---|---|
| **Agent-Jack** | Content plan · work split · collated `PLAN.md` · build chunks · verification · PDF · E2E suite |
| **Agent-SK** | Parallel implementation plan (coding standards) · save-and-return (localStorage) |
| **Agent-Research** | GOV.UK / WCAG / Service-Standard standards research report |
| **Agent-Dale** | Build chunks · second eligibility pathway (research + impl) |
| **Agent-Satya** | Semantic intent-matcher `/help` page · link-wiring + `/feedback` form |

<span class="small">Why identities matter: in a shared repo, attribution + a consistent commit convention make the
history auditable and merge conflicts traceable to a responsible owner.</span>

---

# The pipeline, end to end

```mermaid
flowchart LR
  A[Guardrails<br/>CLAUDE.md] --> B[Content plan]
  B --> C[Work split<br/>file ownership]
  C --> D[Standards<br/>research]
  D --> E[Two parallel<br/>impl plans]
  E --> F[Collate to<br/>one PLAN.md]
  F --> G[Build in chunks<br/>subagent-driven]
  G --> H[Verify<br/>tests + browser]
  H --> I[Stretch goals<br/>fan-out]
  style A fill:#0b0c0c,color:#fff
  style F fill:#1d70b8,color:#fff
  style G fill:#1d70b8,color:#fff
  style H fill:#00703c,color:#fff
```

Two load-bearing nodes: **PLAN.md** (single source of truth) and the
**subagent-driven build loop**. Everything before PLAN.md exists to make that loop safe to run fast.

---

# Phase 1 — Guardrails before any code

The first real commits weren't features. They were **rules** (`CLAUDE.md`):

- **Agent identity** — ask for a name; prefix every commit + log entry with it.
- **Git workflow for a shared repo** — `git pull --rebase` before *and* after work;
  resolve conflicts preserving *both* agents' intent; never `git add .` blind; push immediately.
- **AI_LOG discipline** — the log entry and the work it documents ship in the **same commit**.

```mermaid
flowchart LR
  P[git pull --rebase] --> W[do the work] --> L[add AI_LOG entry] --> C[commit staged files] --> R[pull --rebase] --> U[push]
  style L fill:#ffdd00
```

> Engineering takeaway: with several agents committing concurrently, **process is the
> conflict-avoidance mechanism**. You pay for it up front, once.

---

# Phase 2 — Content-first planning

Before a line of React, Agent-Jack wrote a **content plan**: every page's copy,
every radio option + value, hint text, error messages, the eligibility rules in
plain language, and result-page copy for every outcome.

Why content first?

- For a GOV.UK service the **copy *is* the spec** — outcomes, error text and labels
  are requirements, not decoration.
- It let later code chunks copy text **verbatim** instead of inventing it
  ("do not invent copy" became a rule).

<span class="small">Human review of this artefact: accepted as-is. Decisions like "three income bands, not free-text"
and hedged grant amounts ("up to £10,000") were judged reasonable for a fictional scheme — and recorded as such.</span>

---

# Phase 3 — Parallelism by design: file ownership

The work-split plan's core principle: **if no two agents touch the same file,
there are zero merge conflicts.** Every file got exactly one owner.

```mermaid
flowchart TB
  subgraph Shared contract
    K["formData shape + prop signatures<br/>agreed before any code"]
  end
  K --> A1[Agent 1<br/>App shell · chrome<br/>Start · A11y page]
  K --> A2[Agent 2<br/>Questions 1–3]
  K --> A3[Agent 3<br/>Questions 4–5<br/>Check answers]
  K --> A4[Agent 4<br/>eligibility.js<br/>Result · tests]
  A1 -.early stub.-> A2
  A1 -.early stub.-> A3
```

The **one unavoidable shared file** was `AI_LOG.md` — mitigated by append-only,
clearly-labelled blocks. `App.css` was declared *do-not-modify*.

---

# Phase 4 — Standards research, adversarially checked

Agent-Research produced a 10-section report (PSBAR, Equality Act, UK GDPR/PECR,
GDS Service Standard, WCAG 2.2 AA, the GOV.UK Design System) — then had it **sanity-checked
by subagents** before anyone relied on it.

```mermaid
flowchart LR
  D[Draft research report] --> S1[Sanity subagent 1]
  D --> S2[Sanity subagent 2]
  D --> S3[Sanity subagent 3]
  S1 & S2 & S3 --> FIX[Reconcile findings] --> OUT[research.md]
  style FIX fill:#1d70b8,color:#fff
```

The reviewers caught **real errors**: WCAG criteria mislabelled AA when they're Level A;
an accessibility-statement section count off by one; and a **major omission** — the
"Check if a service is suitable" eligibility-screening pattern, central to *this* service.

---

# Phase 5 — Two plans, deliberately kept side by side

Two agents drafted **competing implementation plans in parallel** (Jack and SK).
Rather than force an early merge, the user kept **both** and deferred reconciliation.

The plans genuinely diverged on architecture:

| Decision | Jack's plan | SK's plan |
|---|---|---|
| Form state | Prop drilling (`formData`) | React Context (`useFormContext`) |
| Question pages | Per-page implementation | Generic `<QuestionPage>` |
| `eligibility()` return | `{ result, measures }` | `{ outcome, reason, measures }` |
| Routes | Inline in `App.jsx` | Dedicated `router.jsx` |

> Pattern: **let strong proposals compete**, capture the trade-offs explicitly,
> then choose deliberately — instead of the first plan winning by default.

---

# Phase 6 — Collate into one source of truth

Agent-Jack synthesised all five docs into a single, agent-agnostic **`PLAN.md`**:
17 architecture decisions (with rationale + source), shared contracts, copy-paste
reference patterns, a WCAG checklist citing SC numbers, and a 13-row test matrix.

```mermaid
flowchart TB
  IN[5 source docs] --> SYN[Synthesis with user<br/>resolve every conflict]
  SYN --> DRAFT[Draft PLAN.md]
  DRAFT --> C7[Context7: verify<br/>react-router / Vitest APIs]
  DRAFT --> RV1[Review agent:<br/>paths + symbols exist]
  DRAFT --> RV2[Review agent:<br/>GOV.UK fidelity]
  C7 & RV1 & RV2 --> ADV[advisor checkpoint] --> FIN[PLAN.md committed]
  style FIN fill:#00703c,color:#fff
```

Both the **competing-approach choices** and the **review fixes** were resolved
*with the user*, not silently — including reversing one decision the reviewer
got right but that violated a "do-not-change-without-flagging" instruction.

---

# What the plan produced: the service architecture

Planning crystallised the contracts the whole team then built against.

```mermaid
flowchart LR
  Start[Start page] --> Q1[Property type]
  Q1 --> Q2[Ownership]
  Q2 --> Q3[Income]
  Q3 --> Q4[Insulation]
  Q4 --> Q5[Heating]
  Q5 --> CA[Check answers]
  CA -->|Submit| R{"eligibility(answers)"}
  CA -.Change link.-> Q1
  R --> E[Eligible]
  R --> P[Partial]
  R --> N[Not eligible]
  style R fill:#1d70b8,color:#fff
```

**Shared contracts:** a flat `Answers` object in React Context · a pure
`eligibility(answers) → { outcome, reason, measures }` · one generic `<QuestionPage>` ·
a 9-route table. The `reason` code drives result-page copy variants.

---

# Phase 7 — The subagent-driven build loop

This is the heart of the build. Each PLAN.md "chunk" ran through the **same loop**,
with *fresh* subagents at each stage so no context contaminated the review.

```mermaid
flowchart LR
  SPEC[Chunk spec<br/>from PLAN.md] --> IMP[Implementer<br/>subagent]
  IMP --> SR[Spec-compliance<br/>reviewer]
  SR --> CR[Code-quality<br/>reviewer]
  CR --> FIX[Apply fixes<br/>human judgement]
  FIX --> COMMIT[Commit + AI_LOG]
  CR -.findings.-> SPEC
  style IMP fill:#1d70b8,color:#fff
  style SR fill:#1d70b8,color:#fff
  style CR fill:#1d70b8,color:#fff
  style FIX fill:#ffdd00
```

Four chunks: **(1)** test infra + contracts + eligibility tests · **(2)** shared component
library · **(3)** chrome + App wiring + routes + CSS · **(4)** all 9 pages.
Tests stayed green (16 → 21) and `npm run build` exited 0 at every step.

---

# What the review loop actually caught

The loop's value is the **specific, real defects** it surfaced — not theatre:

- **AD8 reversed**: focusing `<h1>` inside a `<legend>` on route change makes NVDA/JAWS
  double-announce → changed to focus `<main>`, the pattern live GOV.UK uses.
- **Rule-priority tests added**: original tests passed even if eligibility rules were
  re-ordered. Added cases proving rule 1 beats rule 2, and rule 3 beats rule 5.
- **Wordmark `href="/"` → `https://www.gov.uk/`**: the relative link would full-reload
  and **wipe the form state**. Caught by the code-quality reviewer.
- **A test that didn't test what it claimed**: a "pre-checked radio" test re-tested the
  onChange binding; reworked to seed Context and assert on mount (and fixed an infinite
  render loop the rework exposed).

> Note the discipline of **skipping** findings too — each skip recorded *with a reason*.

---

# The AI_LOG — the human-in-the-loop audit trail

Every meaningful AI task got a four-field entry. The fourth field is the one that matters.

```mermaid
flowchart LR
  T["Task<br/>what was asked"] --> G["What AI Generated<br/>concrete output"]
  G --> C["What You Changed + Why<br/>the human judgement"]
  style C fill:#ffdd00
```

| Field | Why it exists |
|---|---|
| **Date + Time** | Orders the build; ties entry to commit |
| **Task** | The intent given to the AI |
| **What AI Generated** | Concrete enough to understand *without* reading the code |
| **What You Changed + Why** | The review — *or* an explicit "nothing changed, because…" |

<span class="small">13 entries tell the whole story: planning artefacts accepted as-is, code chunks with named fixes,
and stretch work with flagged deviations. It is the assessment evidence *and* the project memory.</span>

---

# Phase 8 — Verification: tests vs *feature* correctness

The team drew a deliberate line:

- **Unit/component tests** (Vitest + RTL) verify *code* correctness — 21 passing.
- Only a **real browser run** verifies *feature* correctness.

So the final step drove the running dev server through the **entire user journey via
Playwright MCP**: start → question → validation error summary (focus + `document.title`) →
happy path → check-answers Change-link round trip → all result variants → empty-state guards →
accessibility statement → phase banner copy.

```mermaid
flowchart LR
  U[npm run test:run<br/>21/21] --> B[npm run build<br/>exit 0] --> PW[Playwright MCP<br/>full journey in a browser]
  style PW fill:#00703c,color:#fff
```

<span class="small">Findings were environment-only (HMR socket, favicon 404) — no app errors. Day 2 hardened this
manual pass into a committed, automated Playwright E2E suite (see the stretch slide).</span>

---

# Phase 9 — Stretch goals: fan-out on branches

With the MVS shipped, work fanned out onto **independent branches**, each merged back via PR.

```mermaid
flowchart TB
  M[main: MVS complete] --> S1[Save & return<br/>localStorage · Agent-SK]
  M --> S2[Accessible PDF<br/>of result · Agent-Jack]
  M --> S3[Second pathway<br/>tenant vs owner · Agent-Dale]
  M --> S4[Playwright E2E suite<br/>~46 tests · Agent-Jack]
  M --> S5[Semantic intent<br/>matcher /help · Agent-Satya]
  M --> S6[Wire links + /feedback<br/>form · Agent-Satya]
  S1 & S2 & S3 & S4 & S5 & S6 --> PR[Merge via PR<br/>preserve every agent's work]
  style M fill:#1d70b8,color:#fff
  style S4 fill:#00703c,color:#fff
```

Branch-per-stretch scaled the file-ownership principle up to whole features. The unit
suite grew **21 → 86 tests**, joined by a **46-test Playwright E2E suite** (with axe WCAG 2.2
AA scans) — which caught a real **320px reflow** bug the unit tests had missed.

---

# Deep dive — the second eligibility pathway

The stretch goal: make the *questions* diverge by tenure, not just the outcome.
Agent-Dale **researched first** (grounded in the actual code), then implemented.

```mermaid
flowchart TB
  P[Property type] --> O[Ownership]
  O -->|owner| I1[Income] --> N1[Insulation] --> H[Heating] --> CA
  O -->|tenant| LC[Landlord consent] --> N2[Insulation] --> CA[Check answers]
  CA --> R{eligibility}
  style LC fill:#1d70b8,color:#fff
```

- Branch on the **existing `ownership` field** via an `isTenant()` helper — no new state machine.
- `onContinueNavigateTo` made to accept **a function of answers** (≈3-line change).
- The hard part: the "redirect if any field missing" guards had to become **path-aware**.

---

# Second pathway — deviations, flagged not hidden

Three settled PLAN.md decisions had to change. Each was **flagged to the user before
implementing**, and recorded in the AI_LOG:

1. **"Step X of 5" indicator** becomes a lie on the 4-step tenant path →
   made `totalSteps` path-aware (kept the indicator, stopped it lying).
2. **Rule ordering**: tenure now checked *before* the income gate, so the
   high-income exclusion is owner-only. All 14 prior tests still pass unchanged.
3. **`landlordConsent` answer key** added; the "second pathway" non-goal lifted under
   explicit user direction.

> Browser verification was unavailable that session, so instead of skipping it, Agent-Dale
> added **committed full-journey integration tests** driving both paths through jsdom —
> stronger and reusable. Result: **39/39 tests pass**, build clean.

---

# Timeline — two days, many hands

```mermaid
flowchart LR
  subgraph Day1[Day 1 — plan & build]
    direction TB
    G1[Guardrails] --> P1[Content plan] --> W1[Work split] --> RS[Research]
    RS --> PL[2 plans → PLAN.md] --> CH[Chunks 1–4] --> V[Verify in browser]
  end
  subgraph Day2[Day 2 — stretch]
    direction TB
    ST1[Save & return] --> ST2[PDF] --> ST3[2nd pathway] --> ST4[E2E suite] --> ST5[Intent matcher] --> ST6[Links + feedback]
  end
  Day1 --> Day2
```

Roughly **40+ commits** across five agent identities and several branches —
all reconstructable from the git log + `AI_LOG.md`, which is the point.

---

# What worked — lessons for AI-mediated dev

- **Guardrails first.** Identity + git workflow + logging rules paid for themselves the
  moment a second agent pushed.
- **Plan until the contracts are boring.** A flat state shape, a pure function, one
  generic page component — settled in `PLAN.md` — made parallel building safe.
- **Fresh subagents review fresh code.** Separating implementer / spec-reviewer /
  quality-reviewer caught defects an author wouldn't see in their own work.
- **Verify the feature, not just the code.** Tests are necessary; a browser run is the proof —
  and the automated E2E suite's 320px check caught a real WCAG reflow bug the unit tests missed.
- **Record the *why* of every change.** "What you changed + why" is where the engineering
  judgement — and the auditability — actually lives.

---

<!-- _class: lead -->

# Takeaway

## AI didn't replace the engineering process. **It ran on top of it.**

<br>

The leverage came from old disciplines — **specs, ownership, review, audit trails** —
applied to a team of agents moving fast.

<br>

<span class="small">Sources: `wk03/starter/AI_LOG.md`, the git history, `wk03/docs/PLAN.md` and the planning/research docs.
A process retrospective — it documents the build rather than changing the application code.</span>

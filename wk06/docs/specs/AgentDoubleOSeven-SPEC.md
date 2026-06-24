# FOI Multi-Agent System — Specification

**Author:** AgentDoubleOSeven · **Date:** 2026-06-24 · **Status:** Draft for comparison

## About this document

This is the **specification**: it defines *what* the system is, *why* it exists, and the
*approach* (solution strategy) we are taking, and it states the **acceptance criteria and tests
the pipeline must pass**. It is deliberately **implementation-agnostic** — it does **not** decide
file layout, function signatures, schema shapes, prompt text, chunk sizes, retrieval depth, or
model identifiers. Those are the implementation plan's job (`AgentDoubleOSeven-PLAN.md`). A
context-free agent should be able to read this document alone and understand the project's intent
and the bar it must clear.

**Provenance.** Every decision below traces to the operator's design-brainstorm planner
(`wk06/docs/research/foi-spec-planner.html`) and their exported JSON. No other agent's documents
were used as input.

---

## 1. Purpose & intent

A government department receives dozens of Freedom of Information (FOI) requests each month. Each
follows a defined workflow: log the request, classify it, check whether exemptions apply under the
Freedom of Information Act 2000, draft a response, and obtain senior approval before release. Today
this is manual, and a small team spends most of its time on repetitive classification and
exemption-checking.

**The system automates the repeatable parts of that workflow while keeping a human in control of
every release.** It exists to save officer time on mechanical steps, to make the reasoning behind
each decision explicit and auditable, and to ensure no response leaves the department without a
human approving it.

---

## 2. Problem statement

The manual process is slow and inconsistent at exactly the steps that are most repetitive:
classifying requests and checking them against exemption policy. The judgement that genuinely needs
a human — whether to release, partially release, or withhold — is bottlenecked behind that
repetitive work. The goal is to move the mechanical effort to software and present the human with a
well-evidenced decision to approve, reject, or amend.

---

## 3. Goals & non-goals

**Goals**

- Process a folder of FOI request files and produce, for each, a structured outcome and a drafted
  response.
- Classify requests, and check them against policy with genuine retrieval and citation, not from
  the model's memory.
- Reason about exemptions in a way a real FOI officer would recognise (distinguishing absolute from
  qualified exemptions, and applying a public-interest balance where the law requires one).
- Mask personal data before a human reviews the draft.
- Pause for human approval at the decision point, and record that decision for audit.
- Survive failures gracefully and never crash a batch.
- Make the cost of automation visible.

**Non-goals**

- Not a replacement for the officer's judgement — it prepares and evidences decisions; it does not
  make final release decisions autonomously.
- Not a case-management or correspondence system; it processes request files and emits artefacts.
- Not in scope: statutory-deadline tracking beyond what the policy corpus states, "neither confirm
  nor deny" handling, or an authentication system for operators.

---

## 4. Constraints (givens, not our choices)

- **Provider:** the system uses Anthropic's Claude models. (Operator decision; fixed for this build.)
- **Vector store:** the brief mandates ChromaDB for retrieval.
- **Interface:** the system runs as a command-line application that processes a folder of request
  files.
- **Domain authority:** correctness is judged against the Freedom of Information Act 2000 and the
  department's supplied exemption/data-handling policy.

These are external constraints. Everything in §5 is *our* solution strategy and is expressed
without committing to implementation specifics.

---

## 5. Solution strategy (approach)

The approach is a **pipeline of specialised agents with distinct roles, run by a supervisor**, with
a human approval gate before any response is finalised. The stances below are the architectural
decisions; the *how* is deferred to the plan.

1. **Specialised roles, one orchestrator.** Distinct responsibilities — triage (classification),
   compliance (exemption checking via retrieval), response drafting, and redaction — coordinated by
   a supervisor that enforces ordering and the human gate.

2. **Deterministic, code-controlled orchestration.** The pipeline runs in explicit, repeatable
   control flow rather than model-driven tool routing. Determinism is what makes the human gate,
   the cost attribution, and the demonstrability reliable. *(Confirmed by the operator over a
   framework-led alternative.)*

3. **Retrieval-grounded, citation-required compliance.** Exemption reasoning is grounded in
   retrieved policy material, and every exemption asserted must cite the specific policy source it
   rests on. Retrieval is organised so that each exemption is independently citable.

4. **Rule-assisted exemption reasoning.** The compliance step distinguishes **absolute** exemptions
   from **qualified** ones, and where an exemption is qualified it applies a **public-interest
   test**. The outcome is one of release / partial release / withhold, consistent with the
   exemptions found.

5. **Tiered model policy.** Lower-cost models are used for mechanical stages (classification,
   redaction) and stronger models for reasoning stages (compliance, drafting), to spend capability
   where it changes the answer. *(Specific tiers are a plan/config decision.)*

6. **Validated, structured outputs.** Each agent's output is schema-validated at the boundary so
   malformed model output cannot silently propagate to the next stage.

7. **A single, decision-centred human gate.** Execution pauses once, after the decision has been
   formed, and presents the **decision** as the primary thing the operator reviews (supporting
   evidence available but secondary). The operator may **approve**, **reject** (with a reason), or
   **modify** (edit the draft, or instruct a regeneration). Nothing is finalised without a human
   action.

8. **Layered, fail-safe error handling.** Failures (API errors, malformed or empty model output) are
   caught and handled with safe fallbacks at multiple levels, biased toward caution (withhold /
   route-to-human) and never toward unreviewed release; one bad request never aborts the batch.

9. **Cost transparency.** Every model call's usage and estimated cost are captured and rolled up per
   agent and per request, with an end-of-run summary. Cost is recorded in the audit trail but is
   **not** shown at the human gate (it is not decision-relevant there). *(Operator instruction.)*

10. **Auditable persistence.** Each request yields a structured, machine-readable result, and the run
    appends to a **human-readable** audit trail capturing every agent decision, human override, and
    cost entry, with operator identity, timestamps, and evidence references.

11. **Sequential processing with visible progress.** Requests are processed one at a time — the
    natural fit for an interactive gate — with per-request status, cumulative cost, and progress
    shown to the operator.

---

## 6. Acceptance criteria

The pipeline is acceptable when all of the following hold. Each criterion is observable and is
verified by the correspondingly-lettered tests in §7. None prescribe implementation.

**A — End-to-end pipeline**
- **AC-A1** Every request file in a folder produces an outcome; a failure on one request never
  aborts the batch.
- **AC-A2** Each request flows through classification → compliance → drafting → redaction → human
  gate in a deterministic, repeatable order.

**B — Triage / classification**
- **AC-B1** Every request is assigned a topic and a complexity level, each drawn from a defined,
  closed set.
- **AC-B2** The complexity assignment is accompanied by the factors that justify it.

**C — Compliance, retrieval & exemptions**
- **AC-C1** The compliance step retrieves policy material and cites at least one specific policy
  source for every exemption it asserts.
- **AC-C2** For a **qualified** exemption, a public-interest test is recorded; for an **absolute**
  exemption, no public-interest test is asserted.
- **AC-C3** The recommendation is exactly one of release / partial release / withhold and is
  consistent with the exemptions asserted.
- **AC-C4** When no exemption applies, the recommendation is release.

**D — Response drafting**
- **AC-D1** The draft reflects the recommendation and references the classification and the
  compliance findings.
- **AC-D2** A withhold or partial-release draft states the relevant exemption(s) and, for qualified
  ones, the public-interest reasoning.

**E — Redaction**
- **AC-E1** Personal data in the draft (contact identifiers and personal names) is masked before the
  human sees it.
- **AC-E2** If redaction cannot complete confidently, the draft is surfaced **flagged for mandatory
  review** rather than silently released unredacted.

**F — Human-in-the-loop & governance**
- **AC-F1** Execution pauses at a single gate after the decision is formed and does not finalise
  without a human action (no path silently auto-approves).
- **AC-F2** The gate presents the decision as the primary item, with classification, exemption
  reasoning, cited policy sources, and the draft available as supporting evidence.
- **AC-F3** The operator can approve, reject (with a reason), or modify (edit or request
  regeneration), and the chosen path takes effect on the finalised response.
- **AC-F4** Each decision is recorded with operator identity, a timestamp, evidence references, and
  any notes.
- **AC-F5** Cost figures are absent from the gate but present in the audit record.

**G — Reliability**
- **AC-G1** An API error, malformed output, or empty result at any stage is logged and handled with
  a fallback; the request continues or degrades without crashing.
- **AC-G2** Fallback outcomes fail safe (bias to withhold / route-to-human), never toward unreviewed
  release.
- **AC-G3** A persistent failure on one request does not affect the processing of others.

**H — Cost awareness**
- **AC-H1** Every model call records the model used, its input and output token counts, and an
  estimated cost.
- **AC-H2** Costs roll up per agent and per request, and an end-of-run summary is produced.

**I — Persistence & audit**
- **AC-I1** Each request yields a structured, machine-readable result containing the classification,
  exemption findings, draft, human decision, and cost breakdown.
- **AC-I2** A human-readable, append-only audit trail records every agent decision, human override,
  and cost entry, each with a timestamp and operator identity where applicable.

**J — Interface & batch**
- **AC-J1** The system runs as a CLI that can build the policy index and process a folder of
  requests.
- **AC-J2** Batch processing is sequential and shows per-request status, cumulative cost, and
  progress.

**K — Generalisation**
- **AC-K1** The system behaves correctly on **held-out** requests it was not developed against — it
  is not overfitted to the sample corpus.

---

## 7. Test specification

Tests are defined as **behaviour the system must exhibit**, not as code. Each maps to the
acceptance criteria above. They are grouped by category; an implementation realises them with
whatever framework and fixtures it chooses.

### 7.1 Test data strategy

- **Sample corpus** — the supplied request files, used during development.
- **Crafted requests** — purpose-built requests that each exercise a distinct path: one that engages
  an **absolute personal-data exemption** (drives redaction), one that is **broad/expensive**
  (drives a cost-limit style exemption), and one that is **clearly releasable** (drives the release
  path).
- **Held-out requests** — requests withheld from development, used only to verify generalisation
  (AC-K1). The build must not be tuned against these.

### 7.2 Functional tests (per-agent behaviour)

| ID | Scenario | Expected outcome | ACs |
|----|----------|------------------|-----|
| T-B1 | A typical request is triaged. | A valid topic and complexity from the closed set, with justifying factors. | AC-B1, AC-B2 |
| T-B2 | A garbled or ambiguous request is triaged. | A valid classification is still produced; complexity errs high; no crash. | AC-B1, AC-G1 |
| T-C1 | A request engaging a **qualified** exemption is checked. | The exemption is asserted with a citation, a public-interest test is recorded, and the recommendation matches. | AC-C1, AC-C2, AC-C3 |
| T-C2 | A request engaging only an **absolute** exemption is checked. | The exemption is asserted with a citation; **no** public-interest test is asserted. | AC-C1, AC-C2 |
| T-C3 | A clearly releasable request is checked. | No exemption asserted; recommendation = release. | AC-C3, AC-C4 |
| T-C4 | Any compliance result is inspected. | Every asserted exemption carries a specific policy citation. | AC-C1 |
| T-D1 | A draft is produced for a withhold/partial outcome. | The draft names the exemption(s) and gives the public-interest reasoning for qualified ones, and references the classification. | AC-D1, AC-D2 |
| T-E1 | A draft containing personal identifiers and names is redacted. | Identifiers and names are masked before review. | AC-E1 |
| T-E2 | The redaction step fails or is uncertain. | The draft reaches the gate flagged for mandatory review, never silently unredacted. | AC-E2, AC-G2 |

### 7.3 Governance tests (human gate & audit)

| ID | Scenario | Expected outcome | ACs |
|----|----------|------------------|-----|
| T-F1 | A request reaches the gate. | Execution pauses; the decision is the headline; no auto-approval occurs. | AC-F1, AC-F2 |
| T-F2 | Operator approves. | The reviewed response is finalised; a decision record with operator id, timestamp, evidence refs, notes is written. | AC-F3, AC-F4 |
| T-F3 | Operator rejects with a reason. | The response is not finalised; the reason is recorded. | AC-F3, AC-F4 |
| T-F4 | Operator modifies (edit and, separately, regenerate). | The finalised response reflects the edit / regeneration. | AC-F3 |
| T-F5 | Gate is inspected for cost. | No cost shown at the gate; cost present in the audit record. | AC-F5, AC-I2 |

### 7.4 Reliability tests (fault injection)

| ID | Scenario | Expected outcome | ACs |
|----|----------|------------------|-----|
| T-G1 | An API error is injected at each stage in turn. | Each is logged; the request continues or degrades with a safe fallback; no crash. | AC-G1, AC-G2 |
| T-G2 | A malformed / empty model output is injected. | Caught and handled with a fallback; nothing malformed propagates downstream. | AC-G1 |
| T-G3 | One request in a batch fails persistently. | The remaining requests complete unaffected. | AC-A1, AC-G3 |
| T-G4 | A fallback outcome is examined. | It fails safe (withhold / route-to-human), never unreviewed release. | AC-G2 |

### 7.5 Cost tests

| ID | Scenario | Expected outcome | ACs |
|----|----------|------------------|-----|
| T-H1 | A full run completes. | Each call logged model + token counts + estimated cost; per-agent and per-request rollups and an end-of-run summary are produced. | AC-H1, AC-H2 |
| T-H2 | A known token count is priced. | The estimated cost matches tokens × the agreed rates. | AC-H1 |

### 7.6 Persistence tests

| ID | Scenario | Expected outcome | ACs |
|----|----------|------------------|-----|
| T-I1 | A request is processed end-to-end. | A structured result artefact contains classification, exemptions, draft, human decision, and cost. | AC-I1 |
| T-I2 | A run completes. | A human-readable, append-only audit trail records every agent decision, human override, and cost entry with timestamps and operator identity. | AC-I2 |

### 7.7 Integration & generalisation tests

| ID | Scenario | Expected outcome | ACs |
|----|----------|------------------|-----|
| T-A1 | A folder (including one request crafted to fail a stage) is processed. | One outcome per request; the failing request degrades gracefully; batch completes. | AC-A1, AC-A2 |
| T-J1 | The CLI indexes policy and processes a folder. | Index builds; processing shows per-request status, cumulative cost, and progress. | AC-J1, AC-J2 |
| T-K1 | Held-out requests are processed. | They flow end-to-end and satisfy the relevant functional, governance, and persistence ACs. | AC-K1 |

### 7.8 Definition of done

The pipeline is **done** when: every acceptance criterion in §6 has at least one passing test in
§7.2–7.7; the reliability tests pass with faults injected at **every** stage; and the
generalisation test (T-K1) passes on requests the build was not tuned against.

---

## 8. Mapping to the assessment rubric

| Rubric axis | Criteria that evidence it |
|-------------|---------------------------|
| **Automation value** | AC-C1–C4, AC-D1–D2 (accurate, evidence-backed, end-to-end with one human touch). |
| **Reliability** | AC-A1, AC-G1–G3 (all error paths handled; batch never crashes). |
| **Governance** | AC-E2, AC-F1–F5, AC-I2 (decision-centred gate, fail-safe redaction, full audit trail). |
| **Cost awareness** | AC-H1–H2 (per-agent and per-request breakdown + summary). |

---

## 9. Assumptions & open questions

- The triage taxonomy and the result artefact's exact shape are AI proposals carried into the plan;
  they are provisional pending validation against real requests and operator review.
- Operator identity is a supplied value; the spec assumes no authentication system.
- Retrieval quality depends on the supplied policy corpus being representative; live FOIA practice
  beyond that corpus is out of scope for this build.

---

## 10. Decision log (approach-level, from the planner)

Confirmed stances the implementation must honour (the *how* lives in the plan): deterministic
code-orchestrated supervisor over a framework; retrieval-grounded compliance with per-exemption
citation; the absolute/qualified split with a public-interest test for qualified exemptions; a
tiered model policy; schema-validated outputs; a single **decision-centred** human gate with
approve/reject/modify; **cost logged but not shown at the gate**; layered fail-safe error handling;
sequential batch processing with visible progress; and an auditable structured-result +
human-readable-trail persistence model.

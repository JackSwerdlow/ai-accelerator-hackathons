# FOI Intelligent Automation System — Specification

**Author:** Agent-Jack
**Date:** 2026-06-24
**Status:** Draft for review
**Companion document:** `Agent-Jack-PLAN.md` (implementation plan — written separately, later)

---

## 0. How to read this document

This is the **specification**: it defines *what* the system is, *why* it exists, and the
*approach* (solution strategy) we are taking. It is deliberately **implementation-agnostic**
— it does **not** decide file layout, function signatures, schema shapes, prompt text,
chunk sizes, retrieval `k`, or model IDs. Those are *plan* decisions and live in
`Agent-Jack-PLAN.md`.

> **The litmus test used throughout:** if a statement would have to change when we swap one
> library for another (e.g. the orchestration framework), it belongs in the plan, not here.
> A statement about *what the system must do and how well* belongs here.

A context-free agent should be able to read this document alone and understand the project's
intent. Where domain or governance facts are asserted, they are grounded in
`wk06/docs/research/foi-landscape-synthesis.md` and its cached sources.

**The `starter/` scaffold is reference-only.** It is a beginner-oriented stub (it even
auto-approves at the gate and uses OpenAI). It is **not** a template and is **not**
authoritative for our design. We aim higher and design cleanly.

---

## 1. Problem & context

A UK government department receives **dozens of Freedom of Information (FOI) requests every
month** (the national figure was ~94,500 in 2025, rising ~14% year-on-year, partly driven by
AI-assisted request drafting). Each request follows a defined workflow: log it, classify it
by topic and complexity, check whether any exemptions apply under the **Freedom of
Information Act 2000 (FOIA)**, draft a response, and obtain senior approval before release.

Today this is **manual**. A small team spends most of its time on the *repetitive* parts —
classification and exemption-checking — before any genuine judgement is exercised. The
repetitive work is automatable; the judgement (ultimately, *release vs withhold*) must remain
human and defensible under oversight.

**The intent of this project:** automate the repetitive majority of the workflow, surface
clear evidence to the operator, and keep a human in command of every release — producing a
faster, more consistent, and fully auditable FOI pipeline.

---

## 2. Users & jobs-to-be-done

| User | Job-to-be-done | What they need from the system |
|------|----------------|--------------------------------|
| **FOI officer (operator)** — primary user | Decide, quickly and defensibly, whether each drafted response should be released | A clear, actionable decision point with enough evidence (classification, retrieved policy excerpts, exemption reasoning, draft) to approve/reject/modify confidently — *not* a wall of raw agent output |
| **Requester** — indirect | Receive a lawful, clear, timely response | Accurate classification and exemption handling so the response is correct and complete |
| **Oversight / audit** — indirect | Reconstruct how any decision was reached | A complete, attributed, timestamped audit trail showing exactly what the AI produced and what the human decided |

Design philosophy (after mySociety's Alaveteli): **hide the complexity of the FOI process**.
Surface a crisp decision to the operator, not the machinery behind it.

---

## 3. Domain primer & glossary

Enough UK-FOI context for an agent with no prior knowledge to understand the project.

**FOIA exemptions in scope** (grounded in the policy corpus we index):

| Section | Name | Type | Note |
|---------|------|------|------|
| **s12** | Cost limit | — | Authority need not comply if cost exceeds the appropriate limit (~£450 / 18 hrs central govt). Must advise on narrowing. |
| **s21** | Accessible by other means | Absolute | Info the requester can reasonably obtain elsewhere (e.g. already published). Must point them to it; the duty to confirm/deny is also disapplied. |
| **s36** | Prejudice to conduct of public affairs | **Qualified** | Inhibits free/frank advice & deliberation. Requires a *qualified-person opinion* (s36(5)) for the exemption to apply **at all**, *and* a public interest test. |
| **s40** | Personal information | Qualified (s40(2)) / absolute (s40(1)) | **Most commonly applied.** Third-party personal data; applicability turns on a UK GDPR / DPA 2018 lawfulness assessment (not an automatic bar). s40(1) — the requester's *own* data — is absolute. |
| **s41** | Information provided in confidence | Absolute | May require **third-party notification** before disclosure. |
| **s43** | Commercial interests | **Qualified** | Tender pricing, scoring, negotiation detail. Requires a public interest test. (Contract *existence* and *total value* are generally releasable.) |

**Other key terms:**
- **Public interest test (PIT):** for *qualified* exemptions (s36, s43), weigh public interest in disclosure against the interest in maintaining the exemption.
- **Partial disclosure / redaction:** release the non-exempt parts of a document with exempt portions redacted; each redaction labelled with its exemption and recorded in a **redaction schedule**.
- **Recommendation outcomes:** `release` · `partial_release` · `withhold`. (*Neither-confirm-nor-deny* (NCND) — e.g. s40(5) — is a real FOIA outcome but is a **documented limitation** here; see §12.)
- **20-working-day clock:** statutory deadline to respond. Extendable for a PIT — but notice must be given within the original 20 days; the extension has no fixed cap, only that it be reasonable. (Other extension grounds, e.g. third-party consultation, also exist.)
- **Duty to assist:** the authority must help requesters — so a malformed or ambiguous request is **never auto-rejected**; it is flagged for operator-led clarification.

---

## 4. Goals & success criteria

The wk06 goal is the **top ("Excellent") band on every rubric axis**. Success criteria are
written as **observable, testable outcomes**, mapped to the axis each serves.

### Automation value
- The system processes a folder of FOI requests end-to-end with no human input *except* the mandated approval gate.
- Triage classification and compliance exemption findings are **accurate** — they match the gold-answer reference (§11) for known requests — and **evidence-backed** — every exemption claim cites a specific retrieved policy excerpt and includes a verbatim supporting quote.
- Output is **always generated contextually** for the actual request. The gold-answer set is a *yardstick for grading accuracy*, never a template to emit (emitting canned text would fail on novel requests — see §11).

### Reliability
- No malformed input, API failure, or empty retrieval result causes a crash.
- In batch mode, one failing request never aborts the run; it degrades to a logged fallback and processing continues.
- The system **generalises to requests it has never seen** (§11) — it is built for the use-case, not the visible examples.

### Governance
- The approval gate displays **rich evidence** (retrieved chunks, classification, exemption reasoning, draft) before accepting a decision.
- Every decision is logged with **timestamp, operator identity, the AI's original recommendation, and any operator override**, with references to the evidence shown.
- The gate is **automation-bias-resistant**: the operator must *actively* choose approve/reject/modify; passive or default approval is impossible. (Lesson from the Robodebt scheme: a rubber-stamp checkpoint amplifies AI error at scale.)

### Cost awareness
- Every LLM call logs model, prompt tokens, completion tokens, and estimated cost.
- An end-of-run summary reports cost **per agent and per request**, plus a run total.

---

## 5. Solution overview

A **linear, supervised pipeline** over a shared **case record** that is enriched at each
stage:

```
            ┌──────────────────────── supervisor ────────────────────────┐
 request →  │  triage → compliance(RAG) → redaction → response → GATE     │  → outputs
            └─────────────────────────────────────────────────────────────┘
                         (per-stage fallback · cost accumulation · audit)
```

- A **supervisor** owns sequencing, per-stage error handling/fallback, cost accumulation, the approval gate, and output writing. It processes one request at a time and isolates failures so a batch keeps going.
- Each agent reads from and writes to a single **case record** threaded through the pipeline, so every stage sees the prior stages' findings and the final record is a complete, auditable account of the request.
- The system runs as a **CLI**, operating over a folder of request files (batch) or a single file.

**Why this shape** (vs dynamic routing or a blackboard): it is the most *reliable*,
*deterministic*, and *auditable* topology — the strongest fit for the Reliability and
Governance axes and for a clean, repeatable demo. Dynamic routing and shared-state
blackboards add non-determinism and a less uniform audit trail for no benefit at this scale.

---

## 6. Agent behavioural contracts

Each agent is scoped tightly by *trigger · inputs · output (as intent) · completion
condition · failure mode*. (Exact I/O schemas and prompts are plan-level.)

### 6.1 Triage agent
- **Trigger:** a new request enters the pipeline.
- **Inputs:** the request text.
- **Output (intent):** a classification — **topic**, **complexity**, and a one-line summary.
  - **topic** ∈ `{ finance_spending, staffing_hr, procurement_commercial, internal_deliberations, personal_data, other }`
  - **complexity:** `low` (single clear ask, no obvious exemption flag) · `medium` (multi-part, or one likely exemption such as s40 anonymisation, no PIT) · `high` (qualified exemption needing a PIT, an s41 confidence/third-party assessment, an s12 cost-limit risk, or broad/ambiguous scope). *Complexity describes handling effort/risk, not a releasability pre-judgement — the release decision is the compliance agent's (§6.2).*
- **Completion:** a valid, parseable classification is produced.
- **Failure mode:** on error/unparseable output, fall back to `topic=other, complexity=high` — deliberately conservative, forcing careful human review rather than waving the request through. (Triage errors **cascade** downstream more expensively than later errors, so the failure default fails *safe*.)

### 6.2 Compliance agent (RAG)
- **Trigger:** triage classification is available.
- **Inputs:** request text + classification.
- **Behaviour:** retrieves relevant excerpts from the policy corpus (RAG), reasons about applicable FOIA exemptions, and applies the **public interest test** for qualified exemptions (s36, s43). For s36 it must note the *qualified-person opinion* (s36(5)) precondition — which it cannot itself verify at hackathon scale — and surface any s36 assertion as *conditional* on that opinion being obtained.
- **Output (intent):** exemptions found (each with section, rationale, **citation to a retrieved excerpt, and a verbatim supporting quote**); a recommendation ∈ `{release, partial_release, withhold}`; the cited policy sources. Where **multiple exemptions** apply, each is listed with its own basis.
- **Completion:** every exemption claim is grounded in ≥1 retrieved excerpt; no claim without a citation.
- **Failure mode:** on retrieval failure or empty results, do **not** guess — recommend `withhold pending manual review` and flag for the operator. Fails safe (never silently releases).
- **Grounding requirement** (mitigates the documented 13–21% legal-citation hallucination rate): the agent must quote retrieved text to support each cited section; an exemption it cannot ground in a quote, it may not assert.

### 6.3 Redaction agent *(stretch goal — committed in scope)*
- **Trigger:** a draft is available and compliance findings flag personal or otherwise exempt data.
- **Inputs:** the draft response and compliance findings.
- **Output (intent):** the draft with personal data masked (names, contact details, staff numbers, and identifying field-combinations, per the data-handling policy), plus a **redaction schedule** (each redaction: category, exemption section, brief reason).
- **Scope boundary:** redaction operates on **the drafted response** and produces a schedule. Rewriting/redacting full source documents is **out of scope** (see §12).
- **s40 link:** where compliance flags s40, the response agent is additionally instructed not to name or describe identifiable individuals drawn from retrieved excerpts.
- **Failure mode:** on error, flag the draft as "redaction incomplete — manual check required" rather than releasing unredacted content.

### 6.4 Response agent
- **Trigger:** compliance (and redaction) findings are available.
- **Inputs:** request text + classification + compliance findings (+ redaction outcome).
- **Output (intent):** a formal FOI response letter that references the classification and compliance findings, states each exemption applied with its section number and a PIT summary where relevant, and reflects the 20-working-day timeline.
- **Completion:** a draft grounded **only** in the evidence — no claims beyond the compliance findings.
- **Failure mode:** on error, produce a minimal templated holding response and flag for manual completion.

### 6.5 Supervisor
- **Trigger:** a request file (or folder) is submitted via the CLI.
- **Responsibilities:** sequence the agents over the shared case record; wrap each stage in error handling with a logged, safe fallback; accumulate cost; drive the approval gate; write outputs; in batch mode, isolate per-request failures and show progress (per-request status, cumulative cost, ETA).
- **Completion:** every request yields a complete result record and an operator decision (or a logged rejection/failure).
- **Failure mode:** never crashes the batch; a fatal per-request error is logged and the run continues.

---

## 7. The human-in-the-loop approval gate

The gate implements the **approve / reject / modify** pattern (from the w05 pre-read), which
overrides the starter's cosmetic auto-approve. The required shape:

1. **Present evidence** — retrieved policy excerpts, classification, exemption reasoning, and the draft response. The draft is explicitly labelled **"AI-generated draft"**.
2. **Operator decides** — `approve`, `reject`, or `modify`.
3. **Log the decision** — with **timestamp**, **operator identity**, and **evidence references**: the IDs (or source filename + chunk index) of the policy excerpts displayed at the gate, so the audit trail is directly traceable to the retrieval artefacts.

**Hard rule:** *no output crosses the system boundary until the operator acts.* No
auto-approval, no default decision, no timeout-to-approve.

**Decision semantics:**
- **approve** → the draft is finalised and written as the released response.
- **reject** → that request's pipeline **halts**; no response is released; the rejection is logged. In batch mode, processing continues with the next request (the *request* pipeline halts, not the whole run).
- **modify** → the operator's override is applied, and the system **records the AI's original recommendation alongside the operator's override** (both preserved in the audit trail). The modified version becomes the finalised output.

**Operator identity** is captured for every decision as a non-empty string attributing it to
a named individual or role, supplied via a required CLI flag or config value — an empty
identity is an error, not a default (the exact capture mechanism is a plan detail). This
attribution is also what satisfies the "human review of an AI-assisted decision" expectation
under the Data (Use and Access) Act 2025. The gate's output **matches or exceeds the shape of
the reference passing checkpoint** shipped with the brief (evidence displayed, decision
logged, cost tracked).

---

## 8. Cross-cutting behaviour

### 8.1 Cost tracking & model tiering *(cost tracking is core; tiering + fallback are stretch goals — committed in scope)*
- Every LLM call records model, prompt tokens, completion tokens, and estimated cost; summarised per-agent, per-request, and per-run. **(Core — mandatory for Excellent.)** Cost estimates use **Anthropic (Claude) pricing** — never the OpenAI pricing in the starter.
- **Tiering** *(stretch)*: a cheaper Claude tier for high-volume, well-defined work (triage/routing); a stronger Claude tier for complex reasoning (compliance, response). Specific model IDs and thresholds are plan-level.
- **Model fallback** *(stretch)*: on an error or a **per-call** cost-threshold breach (granularity is per-call — a single call that would exceed its budget retries on the cheaper tier rather than abandoning), retry on an alternate/cheaper model, and **record the fallback** in the audit trail.

### 8.2 Structured audit log *(stretch goal — committed in scope)*
- Append-only, timestamped, structured (JSON) record of every agent decision, human decision/override, and cost entry — suitable for compliance reporting.
- This audit trail is a **governance asset**: it records exactly what AI output the operator saw and what they decided, supporting oversight and individual-rights requests.

### 8.3 Error-handling philosophy
- Every external call is guarded; failures return structured errors to the supervisor rather than propagating as crashes.
- Degradation is **graceful and safe** per stage (fallbacks above), never a silent release of exempt material.
- Malformed/ambiguous requests are handled in keeping with the **duty to assist**: flagged for clarification, never auto-rejected, never crash-inducing.

### 8.4 Security (light, best-practice — not a hardening exercise)
- Secrets (API keys) via environment/config, never committed and never written to logs or the audit trail.
- Basic input/path validation on CLI arguments and request files.
- No raw secrets or unnecessary personal data in logs.
- Explicitly **not** in scope: auth systems, encryption-at-rest, secret managers, threat modelling (see §12).

---

## 9. Data, inputs & outputs

### 9.1 RAG policy corpus (refreshable, citable)
- The corpus is the authoritative basis for all exemption reasoning, stored in the vector store.
- It is **refreshable**: a refresh/ingest step pulls authoritative UK FOIA sources (e.g. legislation.gov.uk for the Act text; ICO guidance for exemption interpretation) into the **version-controlled, indexed** corpus on demand/periodically. **Runtime retrieval always runs over the cached, citable corpus** — never live per-request scraping — so every citation is deterministic and auditable.
- Corpus freshness is tracked; a stale corpus should surface a warning rather than silently reasoning from outdated guidance.

### 9.2 Request corpus & the held-out discipline
- Starting point: the provided sample requests, plus **additional authored requests** that (a) cover more *valid, varied* cases to prove generalisation (e.g. an s21 already-published case, an s12 over-broad case, a mixed s40+s43 case) and (b) cover *malformed/edge* inputs (empty file, non-FOI/garbled text, oversized request).
- **Held-out acceptance test:** the true measure of success is performance on FOI requests the *builder has not seen*. A hidden held-out set (maintained outside the build) is the real acceptance gate. **The system must not be tuned to the visible corpus** — building to the examples instead of the use-case is an explicit anti-goal.
- All authored data lives under `my-work/`; the read-only `starter/` corpus is never edited.

### 9.3 Per-run outputs
- **Per-request result (JSON):** classification, exemptions + citations, draft response, redaction schedule, human decision (incl. original recommendation vs override), operator identity, timestamps, and per-request cost breakdown.
- **Audit trail:** the append-only structured log (§8.2).
- **Cost summary:** per-agent, per-request, and run total (§8.1).

---

## 10. Constraints & assumptions

**Hard constraints (pinned in this spec):**
- **LLM reasoning: Claude models (Anthropic) only.** No other LLM vendor. (Note: Anthropic provides no native embedding model — so embeddings necessarily come from elsewhere; see below.)
- **Vector store: ChromaDB** (named in the brief's requirements).
- **Embeddings: a local, open-source, downloadable sentence-transformer model under 1 GB.** Local keeps the only paid dependency as Claude itself and needs no extra vendor key. The *specific* model is a plan/research pick (best-as-of-2026-06 by retrieval quality under the size cap).
- **Interface: CLI** (brief-mandated).
- **Data: synthetic only** — no real PII or real case data.
- **Operator: a single human operator per run.**

**Assumptions:**
- The system is **inherently online** (Claude is a hosted API), so "offline operation" is not a goal; local embeddings reduce *extra* API cost/dependency, not enable true offline use.
- The provided policy corpus, augmented by the refresh step, is sufficient ground truth for exemption reasoning at hackathon scale.

**Deferred to `Agent-Jack-PLAN.md`:** orchestration framework (e.g. whether to use
LangChain), the specific embedding model, index persistence strategy, chunking/retrieval
parameters, model IDs and cost thresholds, prompt design, and file/module layout.

---

## 11. Correctness & evaluation

- **Gold-answer reference (yardstick, not template):** a lightweight reference of expected
  `topic / complexity / exemptions / recommendation` per known request, **derived from the
  policy corpus and cross-checked against live UK FOIA guidance**. It is used to *measure*
  classification/compliance accuracy and to anchor the demo narrative. It is **never emitted**
  — the system always generates a contextual response for the actual request. Because exemption
  application is fact-specific and judgement-dependent, gold answers for *qualified* exemptions
  are **rebuttable** — they record a plausible, corpus-consistent application, not legal
  certainty; the yardstick measures *consistency with the corpus*, not legal truth.
- **Citation grounding (mandatory):** every exemption claim must cite a retrieved excerpt and
  carry a verbatim supporting quote. A claim that cannot be grounded may not be asserted.
- **Generalisation over fit:** accuracy is judged primarily on the **held-out** requests
  (§9.2), not the visible corpus. **Accuracy target:** correct `topic`, `complexity`, and
  `recommendation` on all authored known requests (§9.2); the demo processes at least one
  held-out request never seen during development.
- This is intentionally **not** an exhaustive automated test suite — lightweight evaluation
  proportional to a two-day hackathon, sufficient to substantiate "accurate, evidence-backed"
  on the rubric.

---

## 12. Scope

### In scope — core (from the brief)
Triage, compliance (RAG), response drafting, supervisor orchestration, the HITL approve/
reject/modify gate, error handling with fallbacks, **per-call/agent/request/run cost
breakdown** (mandatory for Excellent — distinct from the stretch tiering/fallback in §8.1),
structured JSON per-request output, and the **`AI_LOG.md` provenance record** — at least
**3 entries** covering at least one doc/process task and at least two code tasks, each with
the four mandated fields (Date · Task · What AI Generated · What You Changed + Why).

### In scope — stretch goals (committed; slightly lower priority, **not** deferred)
1. **Redaction agent** — mask personal data in drafts; produce a redaction schedule.
2. **Structured audit log** — append-only JSON of every decision, override, and cost entry.
3. **Model fallback / tiering** — tier models by task; fall back on error or cost breach.
4. **Batch processing UX** — folder processing with per-request status, cumulative cost, ETA.

### Non-goals (explicitly excluded — do not build)
- Production deployment, hosting, or CI/CD.
- Real PII or real case data.
- Security hardening beyond §8.4 (no auth, secret managers, encryption-at-rest, threat modelling).
- Over-built or exhaustive test suites.
- A web or GUI front-end (CLI only).
- A "what would change for production" treatise.
- Live, per-request scraping of external legal sources (the corpus is refreshed offline; see §9.1).
- Multi-user concurrency.

### Considered but excluded — future work (surfaced by `foi-landscape-synthesis.md`)
These were researched and consciously left out to respect the brief's scope. Recorded so a
future team knows they were *considered*, not missed:
- **Neither-confirm-nor-deny (NCND) outcome** (e.g. s40(5)): the recommendation enum is limited to `release` / `partial_release` / `withhold`, so cases where confirming or denying that the information is *held* would itself be a disclosure are out of scope.
- **Vexatious/malformed request classification as an output field** (e.g. `topic=malformed`) — distinct from the duty-to-assist clarification handling in §8.3, which *is* in scope.
- Multi-stage industry triage (entity extraction, duplicate detection, effort estimation, sensitivity flagging); third-party (s41) notification workflow; a dedicated citation-verifier agent; a precedent/decision store; multi-department routing; proactive-disclosure flagging; and ATRS-record auto-generation.

---

## 13. Open questions / to research (for the plan stage)

1. **Specific embedding model** — benchmark the best local open-source sentence-transformer (<1 GB) by retrieval quality on this corpus (MTEB rankings shift; pick at plan time).
2. **Chunking & retrieval parameters** — validate empirically that chunk size/overlap preserve enough context for qualified-exemption reasoning, and choose retrieval `k` for multi-exemption requests (cost vs accuracy).
3. **Cost-threshold values** for model fallback.
4. **Refresh sources & cadence** — confirm which authoritative sources (legislation.gov.uk, ICO) the corpus refresh ingests, and how freshness is surfaced.
5. **Orchestration framework** — whether to adopt a framework (e.g. LangChain) or a lighter, dependency-free approach.

---

## 14. Rubric traceability

| Axis (Excellent) | Spec commitments that deliver it |
|------------------|----------------------------------|
| **Automation value** | End-to-end supervised pipeline (§5); accurate + evidence-backed findings with mandatory citation grounding (§4, §6.2, §11); contextual generation (§11) |
| **Reliability** | Per-stage safe fallbacks + batch isolation & progress reporting (§5, §6.5, §8.3, §12 stretch); generalisation/held-out discipline (§9.2, §11); duty-to-assist handling of malformed input (§8.3) |
| **Governance** | Rich-evidence, automation-bias-resistant gate (§7); attributed, append-only audit trail with original-vs-override (§7, §8.2); AI-draft labelling (§7) |
| **Cost awareness** | Per-call/agent/request/run cost (§8.1); model tiering + recorded fallback (§8.1) |

---

## 15. References

- **Brief (authoritative):** `wk06/context/slides/hackathon-intelligent-automation-system.html` (brief, requirements, Minimum Viable Submission, rubric, stretch goals).
- **Beginner reference (not a template):** `wk06/context/LAB_README.md`, `wk06/starter/`.
- **Domain & governance grounding:** `wk06/docs/research/foi-landscape-synthesis.md` and its cached sources.
- **Related parallel specs (team):** `foi-brief-agent-david.md`, `system-architecture-agent-tom.md`, `supervisor-hitl-agent-tom.md`.
- **Companion (later):** `Agent-Jack-PLAN.md` (implementation plan).

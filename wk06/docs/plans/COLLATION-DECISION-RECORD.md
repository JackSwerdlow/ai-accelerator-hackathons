# FOI Plan Collation — Decision Record

**Author:** Agent-Collator · **Date:** 2026-06-24 · **Status:** RATIFIED — see *Ratification* below; `PLAN.md` written from this record

This record consolidates the four independent FOI implementation plans into a single
recommended design, decided **per dimension** (not per document). It is the input to a
ratification step; once the human signs off (adjusting any close-call below), Phase 2 writes
the consolidated `PLAN.md` from the ratified version. **No per-agent plan is deleted** — each
winning dimension is attributed to its source.

**Sources collated** (equal footing, judged on merit not length — the plans differ ~5× in size):
- **Agent-Jack** — `docs/plans/Agent-Jack-PLAN.md` (+ `Agent-Jack-SPEC.md`)
- **Agent-Tom** — `docs/plans/implementation-agent-tom.md` (+ `mvp-spec-agent-tom.md`)
- **AgentDoubleOSeven** ("007") — `docs/plans/AgentDoubleOSeven-PLAN.md` (+ `AgentDoubleOSeven-SPEC.md`)
- **Agent-David** — `docs/plans/plan-agent-david.md` (+ `foi-brief-agent-david.md`)

**Method.** A multi-agent workflow ran four equal-footing advocates (one per plan, identical
Opus/high settings), a judge (Opus/xhigh) that picked a spine + per-dimension matrix, an
adversarial coherence/completeness critic (Opus/high), and a reconciliation pass (Opus/xhigh)
that folded the critic's flags back in. The Collator independently read all four plans + the
authoritative brief/rubric to sanity-check the result (see *Collator's independent note*).

---

## Ratification (2026-06-24)

The human ratified the spine and resolved every open close-call. Outcomes folded into `PLAN.md`:

| Decision | Ratified outcome | Source of call |
|----------|------------------|----------------|
| **Spine (dim 1 + Collator flag)** | **LangChain** (`langchain-anthropic`) confirmed over plain SDK. | Human (recommended) |
| **Execution model (dims 2 & 11)** | The "team" is **a single Claude Opus 4.8 agent implementing overnight** — *"pick what is best for that."* Resolved as: **Jack's full `foi_system/` package** (an agent wires many files easily and gains from clean testable boundaries) **+ Jack's 15 fine-grained named-test linear TDD tasks as the execution spine** (the most executable sequential hand-off for an agent; the phasing's parallelism payoff is moot for one agent), **wrapped in 007's per-task checkpoint discipline** (run-it-and-observe verification → lint → typecheck → tests green → commit). | Human delegated → Collator |
| **Embedding model (dim 4)** | **nomic-embed-text-v1.5**, with a Day-1 download validation; **all-MiniLM-L6-v2 documented as the fallback** if the lab download fails. | Human (recommended) |
| **Scope ambition (dim 12)** | **All four brief stretch goals committed** (redaction, structured audit, model fallback/tiering, batch UX); **redaction is first-to-cut** if Day-1 slips; **David's ruthless MVP** (core+cost+audit) is the documented fallback. | Human (recommended) |
| **Cost at the gate (dim 7)** | **Hidden at the gate** (automation-bias mitigation); cost still in audit + run summary. | Collator default (recommended; human did not contest) |
| **Operator identity (dim 7)** | **Strict CLI-required, hard-fail on empty, never a default**; any env-var convenience is only a pre-fill that still hard-fails when empty. | Collator default (recommended) |
| **Retry mechanism (dim 6)** | **langchain `.with_retry()` only**; Tom's tenacity dropped (knowingly overrides Tom SPEC §11); circuit-breaker counts failures **after** retry exhausts. | Collator default (recommended) |
| **Eval coverage boundary (dim 10)** | Accepted: held-out harness measures **triage+compliance+grounding only**; redaction/drafting verified by unit tests. | Collator default (accepted) |
| **Build-time verifications** | Verify the Claude-only price table and pin the exact `langchain-anthropic` minimum version for `method="json_schema"` against installed metadata. | Standing item |

---

## Recommended spine

> **Agent-Jack as the trust-critical core** (RAG correctness, citation-grounding, schemas,
> per-call cost granularity, prompt-injection hygiene, TDD task list, held-out eval), with
> **AgentDoubleOSeven's process/reliability layer** (phased 2-day parallel build + AC↔test
> traceability + section-aware chunking + five-layer fail-safe + hybrid redaction) and
> **Agent-Tom's operator-facing layer** (demo-ready HITL display + confidence / Modification /
> third-party-notification schema fields + circuit breaker + CostTracker polish) grafted on.
> **Agent-David** serves as the convergence/sanity check (it is itself a Tom+Jack synthesis) and
> contributes two governance defaults + the ruthless-MVP fallback framing.

**Shared backbone (all four converge here, so grafts are mechanically compatible):** a
deterministic, **code-controlled supervisor — not an LLM** — sequencing
`triage → compliance(RAG) → response → redaction → HITL gate`; **`langchain-anthropic`
`ChatAnthropic.with_structured_output(method="json_schema")`** for typed I/O; **local
sentence-transformer embeddings in a persistent ChromaDB**; and
**`langchain_core.callbacks.get_usage_metadata_callback`** for cost.

**Why this spine.** It is the only shape that fits a 2-day, reliability/governance-weighted
hackathon. Because the backbone is convergent across Jack/Tom/David, the orchestration / cost /
structured-output mechanics that are *normally coupled-and-incompatible across spines* are here
**identical**, so spine-then-graft is unusually safe. 007's plain-Anthropic-SDK variant is the
one real divergence; it is **subordinated** to the LangChain spine — only its *single-seam
principle* is kept (route every model call through one `llm` helper so retry + cost + fallback +
circuit-breaker live in one place), **not its raw SDK**. Jack anchors the trust-critical core
because it is the only plan that turns the rubric's hardest bar — *accurate, evidence-backed,
cited findings* — from an aspiration into a **mechanism**: a first-class `Citation` schema
carrying a verbatim quote tied to `(source, chunk_index)`, a mechanical `verify_citations`
ladder (L1 id-membership + L2 difflib verbatim match), an eval harness that reports a
citation-grounding pass-rate, compliance that fails safe to `withhold`/`grounded=False`, and the
most technically correct retrieval stack. The critic independently re-verified the two
load-bearing Context7 facts as current (`with_structured_output(method="json_schema")` is the
native Anthropic path; `get_usage_metadata_callback` is keyed-by-model-name and accumulates) and
found **no length/polish bias** — the matrix actively demotes Tom/David despite their more
rendered artefacts and fences off Jack's *own* over-reach (S-D, S-E) as scope-creep.

---

## Per-dimension decision (at a glance)

| # | Dimension | Chosen base | Key grafts | Close-call? |
|---|-----------|-------------|------------|:-----------:|
| 1 | Orchestration backbone | **Jack** (langchain spine) | 007 single-seam *principle* | No |
| 2 | Project / module layout | **Jack** (`foi_system/` pkg) | 007 standalone `audit.py` | **Yes** |
| 3 | Data contracts / Pydantic | **Jack** (Citation+CaseRecord) | Tom `confidence`/`Modification`/`third_party_notification_required`; 007 `kind`/`needs_mandatory_review` | No |
| 4 | RAG (embed/chunk/retrieve/persist) | **Jack** (correctness) | 007 section-aware chunking | **Yes** |
| 5 | Agent design & prompt strategy | **Jack** (IRAC-light + injection hygiene) | Tom s40 block; 007 Haiku-redaction + absolute/qualified rule | No |
| 6 | Error handling & reliability | **007** (five-layer) | Tom fallback table + circuit breaker; Jack `.with_retry()` | **Yes** |
| 7 | HITL gate design & UX | **Tom** (rendered display) | 007 decision-first + redaction-before-gate; Jack hard governance rules | **Yes** |
| 8 | Cost tracking & granularity | **Jack** (per-call emission) | Tom CostTracker polish; 007 cost-maths test | No |
| 9 | Audit trail & persistence | **Jack** (JSONL taxonomy) | Tom rich decision payload; 007 human-readable `.txt`; David governance defaults | No |
| 10 | Testing & evaluation strategy | **Jack** (grounding eval) | 007 AC↔test matrix + fault-at-every-stage; Tom/David FakeListChatModel | No |
| 11 | Build order & TDD approach | **007** (phased checkpoints) | Jack named-test granularity nested inside | **Yes** |
| 12 | Scope: stretch / in-out / non-goals | **Jack** (scope governance) | 007 hybrid redaction; David ruthless-MVP fallback | **Yes** |

Six dimensions (2, 4, 6, 7, 11, 12) carry a genuine human judgement call — detailed below.

---

## Per-dimension decision (detail)

### 1 — Orchestration backbone · **Jack** · close-call: No
- **Approach.** Deterministic plain-Python supervisor (not an LLM); each agent is a function
  calling Claude via `langchain-anthropic with_structured_output(method="json_schema")`.
  Supervisor owns sequencing, cost accumulation, the gate, output writing. Adopt **007's
  single-seam discipline**: every model call routes through ONE helper (`llm.py`
  `build_llm`+`structured`) so retry, cost-logging, fallback, and the circuit-breaker live in
  exactly one place. *007's raw-SDK seam is NOT adopted — only its one-injection-point principle.*
- **Rationale.** Backbone is convergent, so low-risk by construction. LangChain gives
  `with_structured_output` AND `get_usage_metadata_callback` essentially for free, de-risking the
  structured-output and cost axes. Single-seam routing structurally prevents the brief's named
  failure mode (cost tracked on only *some* agents).
- **Coherence.** Single-seam `llm.py` is fully compatible with Jack's layout (he already has
  `llm.py`). Because the spine is LangChain, the retry mechanism is `.with_retry()` — see dim 6
  for the consequence that Tom's tenacity is dropped.

### 2 — Project / module layout · **Jack** · close-call: **Yes**
- **Approach.** Jack's `foi_system/` package, but adopt 007's standalone-audit rule (`audit.py`
  is first-class, written-to by every stage, not folded into `hitl.py`). Keep `verification.py`
  and `eval/` as their own modules; keep the `corpus/gold` + `held_out.jsonl` split in the tree.
- **Rationale.** For a build whose hardest engineering is citation grounding and evaluation,
  surfacing `verification.py` and `eval/` as named modules is worth the small extra ceremony —
  they are the automation-value differentiators and must be independently testable. Standalone
  `audit.py` beats Tom/David folding audit-writing into `hitl.py` (which makes per-agent and
  error events second-class).
- **Coherence.** Jack's layout already has standalone `audit.py`; the only graft is reaffirming
  007's "every stage writes audit lines." `audit.py` renders both JSONL and `.txt` (dim 9).
- **⚠ Human note.** Genuine 2-day-feasibility tension: Jack's layout is best for
  testability/maintainability but is more files to wire. A small team absorbs it; a **solo**
  builder under time pressure could collapse `indexing.py`+`retrieval.py` into one `rag.py`
  (Tom/David shape) without losing correctness. *Decide based on team size* (settled jointly with dim 11).

### 3 — Data contracts / Pydantic schemas · **Jack** · close-call: No
- **Approach.** Jack's Pydantic v2 schemas as the base: first-class `Citation`
  (section+verbatim quote+source+chunk_index); `ExemptionFinding` with `public_interest_test`
  and `qualified_person_opinion_required` (s36(5)); `CaseRecord` threaded through, whose
  `model_dump()` **is** the result JSON; `HumanDecision` with required-non-empty operator +
  `original_recommendation` + `override` + `evidence_refs`; `RetrievedChunk.distance` kept as
  cosine distance. **Grafts:** Tom's `confidence: float`, Tom's `Modification(before/after)`,
  Tom's `ComplianceResult.third_party_notification_required: bool` *(added vs the draft — see
  below)*; 007's `kind=absolute|qualified` discriminator on `ExemptionFinding` and
  `needs_mandatory_review` on `RedactionResult`.
- **Rationale.** Jack's `Citation`-with-verbatim-quote is the single most important contract in
  the field — it is what makes mechanical grounding possible, and no other schema carries a quote
  tied to a `(source, chunk_index)` pair. Tom/David's parallel lists
  (`exemptions_found`/`policy_sources`/`chunk_ids`) can desync; Jack's nested `Citation` cannot.
  **Critic fix:** `third_party_notification_required` is ADDED here because dim 7 adopts Tom's
  third-party banner and the draft had omitted the field that triggers it. The field is a SIGNAL
  only (set when s41 or s40(2) applies); it does NOT pull in the s41 notification *workflow* Jack
  scopes out, so it is scope-compatible.
- **Coherence.** All grafts are additive fields on Jack's existing models.
  `RetrievedChunk.distance` is KEPT (not renamed to `similarity`) — load-bearing for the gate fix in dim 7.

### 4 — RAG: embedding, chunking, retrieval, persistence · **Jack** · close-call: **Yes**
- **Approach.** Jack's retrieval engineering as the backbone: a named local sentence-transformer
  with the query/document asymmetry handled explicitly, persistent ChromaDB with the
  cosine-space-on-reopen verify-or-recreate guard, `last_indexed` freshness metadata, and the
  timeboxed recall@k tuning task. **Graft 007's section-aware chunking** (split on
  s12/s21/s36/s40/s41/s43 + PIT / PARTIAL-DISCLOSURE / TIMELINE headings) in place of Jack's
  blind `RecursiveCharacterTextSplitter`, so one exemption == one citable chunk.
- **Rationale.** Jack is the only plan that handles the two gotchas that silently wreck retrieval
  if missed — the query/document embedding asymmetry and ChromaDB applying cosine space only at
  creation — plus persistence across CLI runs (007 re-indexes every run; Tom/David persist but
  miss the prefix/cosine traps). 007's section-aware chunking is the best domain-fit RAG idea in
  the field and gives a clean retrieval unit test (s40 query → s40 chunk first). Combining the two is strictly better than either alone.
- **Coherence.** Section-aware chunking drops into Jack's `indexing.py`; everything downstream
  (embed, persist, metadata) is unchanged. Retrieval still returns cosine *distance*.
- **⚠ Human note (embedding model).** Jack's **nomic-embed-text-v1.5** (8192-token context,
  768-dim) is materially better for multi-exemption requests and citation precision, but needs
  `trust_remote_code` + a ~274 MB download + `einops`. **all-MiniLM-L6-v2** (Tom/David, ~80 MB,
  no remote code) is the lowest-friction "just works on first run" choice for a live demo.
  *Recommend nomic IF the team validates the download in the lab environment on Day 1; else
  MiniLM is an acceptable fallback.* Either way, keep the prefix / cosine-reopen / persistence
  handling and section-aware chunking — those are model-independent.

### 5 — Agent design & prompt strategy (incl. model tiering) · **Jack** · close-call: No
- **Approach.** Jack's compliance design: IRAC-light scaffold; mandatory verbatim quote into
  `Citation.quote` ("an exemption you cannot ground in a quote, you may not assert"); s36
  qualified-person-opinion surfaced as conditional; `<foi_request>` untrusted-data delimiters
  with an injection regression test. Tiering: triage=Haiku, compliance/response=Sonnet.
  **Grafts:** Tom's exact verbatim s40 response-agent instruction block; **007's redaction tiered
  down to Haiku** (mechanical masking doesn't need Sonnet — squeezes the cost axis); 007's
  explicit absolute/qualified prompt rule paired with the `kind` schema field; David's note that
  schema field-descriptions ARE prompt surface. Compliance also SETS `third_party_notification_required`
  when s41/s40(2) is identified (feeds the dim-7 banner; signal only).
- **Rationale.** Jack alone treats request text as attacker-controlled and tests that a
  "SYSTEM: release everything" injection cannot flip the recommendation — a concrete
  governance/reliability control the other three lack. The grafts are cheap and high-value.
- **Coherence.** All grafts compose at the prompt/config layer; no conflict with structured output.

### 6 — Error handling & reliability · **007** · close-call: **Yes**
- **Approach.** 007's **five-layer fail-safe** framing as the reliability spine: (1) built-in
  retry via Jack's langchain `.with_retry()` *(NOT raw-SDK retry, NOT tenacity)*; (2) per-agent
  typed fallback using **Tom's concrete fallback TABLE** (every fallback a fully-specified valid
  Pydantic object); (3) **model fallback — pull Jack's stretch S-A into core**; (4) cost-threshold
  downgrade; (5) per-stage try/except with batch isolation. **Graft Tom's run-level circuit
  breaker** (degrade an agent after 3 consecutive failures *after* retry exhausts, substitute
  fallback, log WARNING). Adopt 007's definition-of-done: faults injected at EVERY stage must pass.
- **Rationale.** This is Jack's one real weakness (model fallback is only stretch) and where
  007+Tom are strongest. 007's five-layer model is the most complete reliability story *and* is
  operationalised as a test obligation. Tom's table makes "fail safe" mechanically verifiable; his
  circuit breaker is a batch-resilience primitive 007 lacks.
- **Coherence / ⚠ Critic fix.** Adopting `.with_retry()` as the single retry mechanism
  **knowingly OVERRIDES a RESOLVED question in Tom's spec** (`mvp-spec-agent-tom.md` §11 / impl
  §8: *"Tenacity only, no native ChatAnthropic max_retries"*). The override is correct because the
  chosen spine IS LangChain, so `.with_retry()` is the idiomatic in-seam retry; running tenacity
  on top would double-retry. **Pick exactly one** — recommend the built-in. Wire the
  circuit-breaker counter to count function-level failures only AFTER retry exhausts, never per HTTP attempt.

### 7 — HITL gate design & UX · **Tom** · close-call: **Yes**
- **Approach.** Tom's fully-rendered terminal display + multiline modify flow (preview+confirm)
  + conditional clarification / third-party banners + low-confidence forcing-function as the
  operator-facing UX. **Graft 007's decision-centred framing** (recommendation as headline; cost
  ABSENT at the gate — showing it invites cost-anchoring/automation bias) and **007's
  redaction-BEFORE-gate ordering** (human never sees unredacted PII) and modify-via-regeneration.
  **Graft Jack's governance hard rules:** required-non-empty operator (hard-fail, no silent
  default), no auto-approve, interrupt-exits, and `evidence_refs` mechanically copied into the
  logged audit entry (tested).
- **⚠ Critic fix (evidence metric).** The gate displays Jack's cosine **distance** with a correct
  label (e.g. `distance: 0.18 (lower = closer)`) OR converts to a 0–1 relevance score
  (`relevance = 1 − distance`) before display. It **must NOT** render Tom's verbatim
  `similarity: 0.82` over a distance field — that inverts the meaning at the decision point.
- **Rationale.** The gate is the governance centrepiece; Tom's is the most demo-ready. 007
  contributes the sharpest principle (decision-first, cost-hidden — an automation-bias mitigation
  grounded in the Robodebt lesson the specs cite). Jack contributes the traceability mechanism and
  the strictest operator-identity posture.
- **⚠ Human note (two judgement calls).** **(1) Cost at the gate** — recommend hiding dollar cost
  at the gate (it still appears in audit + run summary); a values call the team may override for
  budget visibility, though the automation-bias argument is stronger for an FOI release decision.
  **(2) Operator-identity capture mechanism (NEW, per critic)** — Jack requires a non-empty CLI
  value with empty=hard error and never a default; Tom uses `OPERATOR_ID` env-with-runtime-prompt
  fallback (can yield a default-ish path). Both satisfy "non-empty named individual/role."
  *Recommend Jack's strict CLI-required + hard-fail-on-empty for the governance axis (AC-F4); if
  the team wants env-var convenience, keep it ONLY as a pre-fill that still hard-fails when empty.*

### 8 — Cost tracking mechanism & granularity · **Jack** · close-call: No
- **Approach.** Jack's per-call granularity as the rule: emit ONE `CostEntry` per call (not
  aggregated per stage) via `get_usage_metadata_callback` with a FRESH callback per call,
  extracting usage by MODEL NAME (Context7-confirmed the dict is keyed by model and accumulates).
  Locked by `test_costentry_emitted_per_call_not_per_stage`. Claude-only price table flagged
  verify-at-build. **Grafts:** Tom's finished `CostTracker` class shape + polished end-of-run
  per-agent table + per-request cost embedded in the result artefact and audit; 007's explicit
  cost-maths test (`T-H2`) and Rich rendering.
- **Rationale.** Per-call is the finest granularity from which per-agent/per-request/per-run all
  reconstruct — strictly more defensible than Tom's per-agent aggregation, which would double-count
  the two Sonnet agents without care. Tom's shape is adopted as POLISH; Jack's per-call rule
  overrides Tom's aggregation (justified by keyed-by-model accumulation, not an automatic tiebreaker).
- **Coherence.** The hook lives at the single `llm` seam (dim 1), so every agent is covered. Cost
  shown nowhere at the gate (dim 7).

### 9 — Audit trail & persistence · **Jack** · close-call: No
- **Approach.** Jack's append-only JSONL audit with a uniform `event_type` taxonomy (every agent
  stage, the human decision, each cost entry, each error emits one `AuditEntry`) + the
  no-secrets-in-audit test; per-request result JSON = `CaseRecord.model_dump()`. **Grafts:** Tom's
  richer decision-entry content (AI original recommendation vs override, `Modification`
  before/after, `rejection_reason`) into the decision `AuditEntry.payload`; **007's human-readable
  `.txt` audit trail alongside the JSONL** (both rendered from the same `AuditEntry` stream);
  David's two governance defaults — **append-only ACROSS runs (never reset)** and **rejected
  requests STILL write a result JSON** ("rejection is a decision on record").
- **Rationale.** The brief's stretch goal asks for the audit log "as structured JSON, suitable
  for compliance reporting" — Jack's JSONL taxonomy matches that wording and is most queryable;
  007's insight that an auditor reads a *narrative* is fit-for-purpose too, so producing BOTH is
  the ideal and cheap.
- **Coherence.** Jack's standalone `audit.py` (dim 2) writes both formats from one event stream; Tom's richer payload is additive.

### 10 — Testing & evaluation strategy · **Jack** · close-call: No
- **Approach.** Jack's evaluation as the base: `eval_harness.py` running **triage+compliance ONLY**
  (no gate, nothing released) over a 20–30 item gold set, reporting exemption-classification
  accuracy, coverage recall, false-positive rate, AND a **citation-grounding pass-rate** (via the
  `verify_citations` difflib ladder); a physically separate gitignored `held_out.jsonl` kept out
  of the tuning loop; the injection regression test. **Graft 007's** bidirectional AC↔test
  traceability matrix and its fault-injection-at-EVERY-stage definition-of-done. **Adopt
  Tom/David's `FakeListChatModel`** as the standard unit seam (lower-friction than Jack's
  hand-rolled stub) and their hard "no Sonnet in CI" cost guard.
- **⚠ Critic coverage fix (stated, not a close-call).** The eval/held-out harness measures
  **triage+compliance accuracy and citation grounding ONLY** — it does NOT exercise redaction
  correctness or response/drafting quality; those are verified by UNIT tests (redaction T-E1/E2,
  response T-D1), NOT by the generalisation harness. The consolidated plan must state this boundary
  so reviewers don't assume held-out validates redaction or drafting.
- **Rationale.** Testing (does the plumbing work?) and evaluation (is it accurate, does it
  generalise?) are different bars and the rubric demands both. Jack is decisively strongest on
  EVALUATION (the only plan that *measures* grounding); 007 is strongest on TESTING STRUCTURE.

### 11 — Build order, task granularity & TDD approach · **007** · close-call: **Yes**
- **Approach.** 007's phased structure as the process spine: per-phase
  Tasks → Unit tests → Verification (run it, observe stated output) → Checkpoint (lint → typecheck
  → tests green → human review → commit), with the explicit Day-1-to-MVS / Day-2-deepen
  parallel-team schedule. **Graft Jack's finer granularity INSIDE each phase:** each phase's tasks
  carry Jack's named test-case identifiers and follow red→green→commit (true test-first); keep
  Jack's schemas-first ordering and spec/rubric traceability table.
- **Rationale.** 007's phasing fits the actual constraint — a 2-day PARALLEL team with checkpoint
  gates tied to the brief's own MVS-by-Day-1 schedule and verification-before-done. But its
  phase-level grouping is coarser than Jack's 15 pre-named per-task tests (the most executable
  hand-off and most genuinely test-first). Tom/David put tests LAST — rejected as not-TDD.
- **⚠ Human note.** Process call, not a code call. If the build is **solo**, Jack's flat 15-task
  linear list is actually easier to execute than 007's phase grouping (the phasing's payoff is
  parallelism). *Pick based on team size — the same question that drives dim 2.* Either way keep
  test-first + verification-before-done.

### 12 — Scope: stretch-goal selection, in/out, non-goals · **Jack** · close-call: **Yes**
- **Approach.** Jack's scope governance: commit the **four brief stretch goals** in-scope
  (redaction, structured audit, model fallback/tiering, batch UX) and keep his
  "considered-but-excluded — future work" list (NCND/s40(5), vexatious classification, s41
  notification WORKFLOW, citation-verifier-as-agent, security hardening, web UI, live scraping) as
  explicit non-goals. **Graft 007's hybrid deterministic+model redaction** (regex
  email/phone/postcode + model pass for names, with `needs_mandatory_review` fail-safe) as the
  redaction definition. **STRICTLY DEPRIORITISE Jack's own S-D** (hybrid BM25+dense) **and S-E**
  (DeepEval L3 entailment) — real scope-creep risk in 2 days; only touch if core + four stretch
  goals are done and tested. The third-party SIGNAL/banner (dims 3/7) is IN scope; the s41
  notification WORKFLOW stays OUT (Jack) — distinct things.
- **Rationale.** Jack's scope is most defensible: it separates brief-mandated stretch (committed)
  from plan-additions (labelled), and the considered-but-excluded list proves exclusions were
  deliberate. 007's hybrid redaction is more reliable than model-only masking. Tom/David's
  deferral of redaction lowers their governance ceiling by design; targeting Excellent on all four
  axes means redaction must be in-scope.
- **⚠ Human note.** 2-day feasibility risk lives here. Committing all four stretch goals is the
  right Excellent-band ambition *only if the core lands by the Day-1 checkpoint.* The safe fallback
  if Day 1 slips is **David's ruthless MVP** (core + cost + audit, defer redaction) — a
  guaranteed-shippable floor. *Recommend: build to the committed-four scope, treat redaction as the
  first stretch to cut if time runs short, keep David's tight core as the documented fallback.*

---

## Grafts (compatibility-checked)

| Dim | From | Graft | Compatibility |
|-----|------|-------|---------------|
| 1 | 007 | Single `llm.call_structured()` seam *principle* (not raw SDK) | Jack already has `llm.py`; elevates it to sole injection point. Retry = langchain `.with_retry()`. |
| 2 | 007 | Standalone `audit.py` (every stage writes) | Jack's layout already has it; renders both JSONL + `.txt` (dim 9). |
| 3 | Tom | `confidence:float`, `Modification(before/after)`, `third_party_notification_required:bool` | Additive fields. `Modification` replaces `override:str`. **Critic fix** — `third_party` field added (drives dim-7 banner). Keep Jack's `distance` (not `similarity_score`). |
| 3 | 007 | `kind=absolute\|qualified` on `ExemptionFinding`; `needs_mandatory_review` on `RedactionResult` | Additive; `kind` makes qualified→PIT / absolute→no-PIT a schema invariant. |
| 4 | 007 | Section-aware chunking replaces `RecursiveCharacterTextSplitter` | Drops into Jack's `indexing.py`; embed/persist/metadata unchanged; retrieval still returns distance. |
| 5 | Tom | Exact verbatim s40 response-agent instruction block | Appended when compliance flags s40. |
| 5 | 007 | Redaction tiered to Haiku; explicit absolute/qualified prompt rule | One entry in `config.MODEL_TIERS`; pairs with `kind` field. |
| 6 | 007 | Five-layer fail-safe + fault-at-every-stage DoD; pull Jack S-A model-fallback into core | Layers attach at the single `llm` seam; retry uses langchain `.with_retry()`. |
| 6 | Tom | Per-stage fallback TABLE + run-level circuit breaker | Breaker in supervisor, counts failures AFTER retry exhausts. **Critic fix** — tenacity DROPPED (overrides Tom SPEC §11); don't run both. |
| 7 | Tom | Fully-rendered display + multiline modify + conditional banners + low-confidence forcing-function | **Critic fix** — relabel/convert `similarity` → distance; banner driven by dim-3 field. |
| 7 | 007 | Decision-centred framing (recommendation headline, cost absent at gate); redaction-before-gate | Reorders panels, inserts redaction before gate; cost still in audit + summary. |
| 8 | Tom | Finished `CostTracker` class + per-agent table + cost-in-audit | `track()` becomes per-call-emitting (not per-agent aggregation); summary rolls up from entries. |
| 8 | 007 | Cost-maths test (`T-H2`) + Rich rendering | Additive test + display. |
| 9 | Tom | Richer decision payload (original-vs-override, Modification, rejection_reason) | Additive to `AuditEntry.payload`. |
| 9 | 007 | Human-readable `.txt` audit alongside JSONL | Both rendered from the same `AuditEntry` stream. |
| 9 | David | Append-only ACROSS runs; rejected requests still write result JSON | Governance defaults. |
| 10 | 007 | Bidirectional AC↔test matrix; fault-at-every-stage DoD | Maps 007 AC letters onto Jack's named tests + eval metrics. |
| 10 | Tom | `FakeListChatModel` unit seam; no-Sonnet-in-CI guard | Replaces Jack's hand-rolled stub. |
| 11 | 007 | Phased checkpoint structure + Day-1/Day-2 parallel schedule | Jack's named-test tasks nest inside the phases. |
| 12 | 007 | Hybrid regex+model redaction with `needs_mandatory_review` | Refines Jack's model-only Task 8; same scope footprint. |
| 12 | David | Ruthless MVP (core+cost+audit, redaction deferred) as documented fallback | If Day-1 checkpoint slips; redaction is first cut. |

---

## Open for human decision

These are the genuine judgement calls the workflow deliberately did **not** silently resolve.
Please ratify or adjust each:

1. **Embedding model (dim 4)** — nomic (better retrieval, needs `trust_remote_code` + ~274 MB +
   `einops`) vs all-MiniLM-L6-v2 (~80 MB, lowest-friction). *Recommend nomic if the lab download is
   validated Day 1, else MiniLM.* Model-independent handling (prefixes, cosine-reopen, persistence,
   section-aware chunking) stays either way.
2. **Cost at the gate (dim 7)** — hide dollar cost at the decision moment (automation-bias
   mitigation; recommended) vs surface it for budget-awareness. Cost still appears in audit + summary.
3. **Operator-identity capture (dim 7, NEW)** — Jack's strict CLI-required + hard-fail-on-empty
   (recommended for AC-F4) vs Tom's env-var-with-runtime-prompt fallback. If env convenience is
   wanted, keep it only as a pre-fill that still hard-fails on empty.
4. **Team size drives dims 2 AND 11** — 007's phased parallel schedule + Jack's full package suit a
   *team*; Jack's flat 15-task list + a collapsed `rag.py` are easier *solo*. One answer settles both.
5. **2-day scope ambition (dim 12)** — commit all four brief stretch goals (Excellent-band, assumes
   core lands Day 1) with redaction as the first cut-line and David's tight MVP as the documented fallback.
6. **Retry mechanism (dim 6)** — confirm the single retry mechanism is langchain `.with_retry()`
   (recommended), which **knowingly reverses Tom SPEC §11's resolved "tenacity only" decision**.
   Tom's tenacity decorators must NOT also wrap each agent (double-retry). Wire the circuit-breaker
   counter to count failures only AFTER retry exhausts.
7. **Eval coverage boundary (dim 10)** — confirm the team accepts that held-out generalisation
   exercises triage+compliance+grounding ONLY, not redaction or drafting (those are unit-tested). If
   stronger redaction assurance is wanted, add a small redaction-specific eval outside the held-out loop.
8. **Build-time verifications** — the Anthropic price table (`config.py`) is flagged verify-at-build
   in every plan; pin the exact minimum `langchain-anthropic` version for `method="json_schema"`
   against installed package metadata at build time (the method itself is confirmed current).

---

## Critic's surviving flags (verdict: **PASS**)

The adversarial critic passed the design with three fixable incoherences and three coverage notes,
**all of which the reconciliation pass folded into the matrix above.** Recorded here for the human:

**Incoherences (all now reconciled in-matrix):**
1. *Retry-mechanism override of a Tom spec resolution, under-flagged in the draft.* — Now stated as
   a deliberate override of Tom SPEC §11, not a mere nuance (dim 6 + open item 6).
2. *`similarity_score` vs `distance` UX incoherence.* — Grafting Tom's `(similarity: 0.82)` display
   onto Jack's `distance` field would show a number meaning the OPPOSITE of its label. Now fixed:
   relabel/convert at the gate (dim 7).
3. *Third-party banner adopted without its backing field.* — Dim 7 used Tom's banner but dim 3 had
   omitted `third_party_notification_required`. Now added to the dim-3 schema graft.

**Completeness notes (all addressed):**
- Third-party (s41/s40(2)) notification handling was orphaned at the data-contract layer → field
  added (dim 3); signal in scope, workflow out (dim 12).
- Operator-identity capture mechanism was left ambiguous → surfaced as open item 3, not silently resolved.
- Eval scope vs redaction/response coverage → boundary now stated explicitly (dim 10).

**Bias check:** *No length/polish bias detected.* The matrix anchors on Jack for verifiable
mechanisms (Citation-with-quote, `verify_citations` ladder, embedding/ChromaDB gotchas), demotes
Tom/David despite their more rendered artefacts, and fences off Jack's own over-reach (S-D, S-E) as
scope-creep. The two Context7 facts used to anchor on Jack were independently confirmed current.
*Minor watch-item:* every `close_call=false` Jack win (dims 3, 5, 8, 9, 10) should be sanity-checked
to ensure "Jack is verified-correct" isn't an automatic tiebreaker on dimensions where the other
plans weren't themselves Context7-checked — the critic judged the asymmetry justified in each case.

---

## Collator's independent note (one flag beyond the workflow)

I read all four plans + the authoritative brief/rubric independently to sanity-check the workflow.
I concur with the spine and the per-dimension matrix. **One thing I would surface that the workflow
marked as settled (dim 1, `close_call=false`):**

- **The spine is convergent only for *three* of four plans.** Jack/Tom/David chose
  `langchain-anthropic`; **AgentDoubleOSeven deliberately chose the plain `anthropic` SDK**
  (+ typer/rich, native structured outputs, `response.usage` for cost). The workflow subordinated
  007's SDK to the LangChain majority — defensible, and I agree LangChain's
  `get_usage_metadata_callback` + `with_structured_output` + `FakeListChatModel` are net-positive.
  **But two signals point the other way and the human should weigh them:** (a) the **starter
  scaffold** is plain-Python with a partially-implemented `CostTracker` class (`python main.py
  process documents/foi_requests/`), not LangChain; and (b) `wk06/CLAUDE.md`'s working rules name
  *"the `anthropic` SDK, ChromaDB"* as the libraries to confirm via Context7. The plain SDK is
  leaner (fewer deps, no `langchain-anthropic>=1.1.0` version-pin risk) and matches the scaffold;
  per-call cost tracking is trivial via `response.usage` without callback machinery. I still
  **recommend the LangChain spine** for the reasons above, but I flag this as a **genuine close-call
  worth an explicit human decision** rather than a settled point — it is the single most coupled
  decision in the build, so it is worth getting deliberately right.

---

*Next step: human ratifies / adjusts the open items and the spine flag above. Phase 2 then writes
`wk06/docs/plans/PLAN.md` from the ratified record, attributing each major decision to its source.*

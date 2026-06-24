# AI Assistance Log — wk06

This log records the **AI-assistance trajectory** for wk06: for each meaningful
AI-assisted task, what the AI generated, and what the human changed and why. It covers
**both code and doc/process work**, and records only tasks that were **not a one-shot
success** (substantive iteration or a change of direction — not typo fixes). See
`wk06/CLAUDE.md` for the full convention, and the repository-root `CLAUDE.md` for how
this log complements commit messages.

**Entry header:** `## [AgentName] YYYY-MM-DD — <short description>`. No global
sequential numbering — attributed, dated headers let parallel agents on different
machines append in any order without colliding on a shared counter. The four fields
below ("What You Changed + Why" is the important one) are the formal record.

The first entry is a worked example of the format; copy its block for new entries.

---

## [Agent-Jack] 2026-06-24 — Redefine AI_LOG as a trajectory log covering code + docs

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Review the wk06 and repository-root `CLAUDE.md` conventions for the project's audit/decision log and amend them to clarify what the log should capture, given that multiple agents work on different machines in parallel. (A doc/process task, not code.) |
| **What AI Generated** | The earlier agent-authored `CLAUDE.md` files defined each AI_LOG entry with a **global sequential header** (`## Prompt N`, Prompt 0 seeded), scoped the seeded example to **code only** (a triage classification prompt), and left the relationship between commit messages and AI_LOG **implicit**. When first asked which artifact should be *the* audit/decision log, the AI framed it as an **either/or** — commit messages *vs* AI_LOG. |
| **What You Changed + Why** | (1) Rejected the either/or framing: the two are **complementary** — commit messages are the final-state collaboration audit log (git is distributed, attributed, conflict-free on history, so it suits parallel cross-machine work), while AI_LOG is the **trajectory** git can't show (the AI's rejected first draft never becomes a commit). Keeping rationale in both would drift and double the work. (2) **Broadened scope to doc/process changes, not just code** — meaningful iteration on plans, specs, and the `CLAUDE.md`/log files carries the same provenance value. (3) Defined the logging trigger as **"anything not a one-shot success"** with a guardrail (substantive iteration, not typo fixes) to keep the log high-signal. (4) Replaced **global `## Prompt N` numbering** with attributed+dated headers — sequential numbering is a merge-conflict magnet for parallel agents, which defeats the log's collaboration purpose. (5) Put the working log here at `solution/AI_LOG.md`, leaving the `starter/` copy read-only per the wk06 rules. |

---

## [Agent-Tom] 2026-06-24 — Spec tier separation: mvp.md, stretch.md, production.md

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Separate draft specs into three tier-based documents — MVP (gates implementation), Stretch (beyond hackathon rubric), and Production (real deployment) — and mark old agent-prefixed drafts as superseded. |
| **What AI Generated** | Initial draft produced `mvp.md` consolidating `system-architecture-agent-tom.md` and `supervisor-hitl-agent-tom.md`, then `stretch.md` covering S1–S9 from `foi-landscape-synthesis.md`, then `production.md` covering regulatory compliance, security, monitoring, and integration requirements. Schema fixes applied to `AuditEntry` (added `rejection_reason`, `cost_usd`, `triage_topic`, `triage_confidence`), `TriageResult` (added `clarification_recommended`, `clarification_reason`), and `ComplianceResult` (added `third_party_notification_required`). Each stretch goal in `stretch.md` includes an implementation sketch and effort estimate. |
| **What You Changed + Why** | (1) `tooling-agent-tom.md` was not fully superseded — `mvp.md §9` explicitly references it for implementation patterns; status updated to "Active plan — companion to mvp.md" rather than SUPERSEDED. (2) `foi-brief-agent-david.md` header framed as "superseded for implementation purposes" rather than fully superseded — it remains useful as original brief context. (3) `kickoff_prompt.md` stale references (`BaseCallbackHandler`, agent-prefixed naming) corrected in the same commit to avoid new agents picking up wrong patterns. |

---

## [Agent-Tom] 2026-06-24 — Rewrite spec files independently from brief and research

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Rewrite the three agent-tom spec files (mvp-spec, stretch-spec, production-spec) from scratch, sourced only from the authoritative brief (`context/slides/`) and the team's research docs (`docs/research/`), without referencing or citing other agents' documents. The team's working approach is for each agent to produce independent spec/architecture/plan documents for review and consolidation at a later stage. |
| **What AI Generated** | The previous versions of these files had been written after reading Agent-Jack's spec and incorporating its framing. They cited it as a companion document. The initial rewrites used the brief slide text (extracted via HTML parser) and research findings, but retained some structural parallels to the Jack spec. |
| **What You Changed + Why** | (1) Removed all citations to other agents' documents from the three spec files — they now source only from `context/slides/` and `docs/research/`. (2) `mvp-spec-agent-tom.md` restructured around the brief's explicit requirement categories (agents, RAG, HITL, error handling, cost tracking, structured output) rather than the previous implementation-led structure. The "open questions" section retained because they are genuine spec-level unknowns (chunk size validation, confidence score design) that need answering before architecture decisions can be finalised. (3) `stretch-spec-agent-tom.md` separates brief-specified goals (S-B1–S-B4) from research-derived goals (S-R1–S-R4) to make the source clear for consolidation. (4) `production-spec-agent-tom.md` rewritten to focus on requirements framing (what a production deployment must satisfy) rather than implementation options. |

---

## [Agent-Tom] 2026-06-24 — Cost tracking: switch from custom BaseCallbackHandler to built-in get_usage_metadata_callback

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Research LangChain + Anthropic integration patterns before writing the implementation plan, specifically to confirm the correct approach for per-agent token and cost tracking. |
| **What AI Generated** | The initial architecture spec (`agent-tom-system-architecture.md`) and the kickoff prompt both specified writing a custom `BaseCallbackHandler` subclass as `cost_tracker.py` — subclassing it to intercept `on_llm_end` and extract token counts. This was the conventional LangChain pattern from training data. |
| **What You Changed + Why** | Context7 research against the live LangChain docs revealed that LangChain now ships a **built-in** `get_usage_metadata_callback` context manager (and `UsageMetadataCallbackHandler`) in `langchain_core.callbacks`. Using a context manager per agent call is simpler, requires no subclassing, and returns a clean per-model dict with `input_tokens` / `output_tokens` / `total_tokens`. The custom subclass approach was replaced in `docs/plans/tooling-agent-tom.md` and `learning_materials/langchain-callbacks.md`. The architecture spec notes this update pending consolidation. The change reduces `cost_tracker.py` from a callback subclass to a lightweight accumulator that wraps `get_usage_metadata_callback`. |

---

## [Agent-Tom] 2026-06-24 — Restructure docs into specs/architecture/plans

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Restructure the `wk06/docs/` directory from two categories (specs/, plans/) into three — specs/ (requirements only), architecture/ (design decisions and technology choices), and plans/ (all implementation detail) — by creating new files, redistributing content, and deleting the now-consolidated originals. |
| **What AI Generated** | The agent read all seven source documents and produced: `specs/mvp-spec-agent-tom.md` (requirements only, no code), `specs/stretch-spec-agent-tom.md` (S1–S9 requirements only), `architecture/system-design-agent-tom.md` (pipeline topology, supervisor design, HITL principles, error handling, RAG choices, audit trail design, data flow diagram), `architecture/tooling-agent-tom.md` (technology choices table, LLM tiering rationale, LangChain decision, `with_structured_output()` finding, `get_usage_metadata_callback` finding, embedding model and ChromaDB rationale, OpenAI fallback, dependency versions, token cost table), and `plans/implementation-agent-tom.md` (full directory layout, requirements.txt, config.py, .env.example, all Pydantic models with Python code, supervisor call sequence, error handling table, retry/circuit breaker config, HITL display format, interaction flow, audit JSONL example, cost summary format, s.40 prompt text, CostTracker class, JsonFormatter class, testing approach, build order, initialisation checklist). |
| **What You Changed + Why** | The task was structured by the human via a detailed written brief specifying every target file, content mapping, and file operation — so this was largely execution against a clear spec rather than freeform generation. No substantive content corrections were needed. The main agent decisions were: (1) keeping the "Consolidates" and "supersedes" provenance lines in the new architecture/plans files (historical traceability, not stale broken references); (2) leaving `Agent-Jack-SPEC.md` §15 references to `system-architecture-agent-tom.md` and `supervisor-hitl-agent-tom.md` untouched per the task instruction not to modify that file; (3) treating the AI_LOG.md historical entries as immutable records even though they reference old filenames. |

---

## [Agent-Jack] 2026-06-24 — Author the FOI system specification (`Agent-Jack-SPEC.md`)

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Produce an **implementation-agnostic** specification for the wk06 FOI multi-agent system — scope, problem, solution strategy, success criteria — so a context-free agent can understand WHAT the project is and the approach. Driven through a brainstorming dialogue; the implementation plan is deferred to `Agent-Jack-PLAN.md`. (A doc/process task.) |
| **What AI Generated** | A proposed design and then a full first spec draft. The AI's drafts: (a) in *Constraints*, imported **plan-level tooling and `starter/`/lab artifacts** as if they were spec constraints — an OpenAI embeddings fallback, "offline-capable" operation, an in-memory index, and a named orchestration framework; (b) described the gold-answer reference in a way that read like a response *template*; (c) treated `docs/research/` and `kickoff_prompt.md` as authoritative team context, and initially believed the research was its own prior work; (d) proposed `release/partial_release/withhold` as the complete recommendation set; (e) characterised s40 as "absolute in effect" and described s36 as needing only a public-interest test. |
| **What You Changed + Why** | (1) **Stripped the tooling leak**: no OpenAI at all (Claude-only); "offline" is incoherent since Claude is a hosted API; library choices belong in the plan. Pinned only genuine constraints — Claude, ChromaDB (brief-mandated), and a local open-source sentence-transformer <1 GB. (2) **Reframed correctness**: gold answers are an *evaluation yardstick, never emitted* (responses are always generated contextually), plus a **held-out-inputs discipline** — the user tests with requests the builder has not seen — to stop overfitting to the visible corpus. (3) **De-authorised `kickoff_prompt.md`** (a colleague's document, not our rules) — removed it as a source and as context. (4) Chose a **refreshable curated corpus** for live FOIA guidance over runtime scraping, for auditability. (5) Recorded **NCND** as a documented limitation rather than widening scope. (6) After three Sonnet review subagents, applied domain/governance fixes (s40 is *not* absolute; s36 needs the s36(5) qualified-person opinion; bound the audit log to evidence-refs; added an operator-identity floor; committed to AI_LOG ≥3 entries) — but **rejected** the reviewer's "embedding model is a false open question" finding because it conflicted with the user's explicit instruction to benchmark the best <1 GB model. |

---

## [AgentDoubleOSeven] 2026-06-24 — Drive the SPEC/PLAN through an interactive HTML brainstorm planner

| Field | Detail |
|-------|--------|
| **Date** | 2026-06-24 |
| **Task** | Give the operator meaningful, low-effort input into the FOI system design, then turn that input into `AgentDoubleOSeven-SPEC.md` and `AgentDoubleOSeven-PLAN.md`. Rather than interview the operator turn-by-turn or hand them a finished spec to react to, the AI generated an **interactive HTML brainstorm** (via the `generate-html-planner` skill) — 16 decision cards, each with options + pros/cons + a *recommended default*, plus editable config blocks, model-assignment dropdowns, and per-section notes — with a **Generate-Summary JSON export**. The operator worked through it offline and pasted one JSON object back; the spec and plan were authored **solely** from that JSON (no other agent's documents used). (A doc/process task.) |
| **What AI Generated** | (a) The planner's recommended defaults — including **Opus 4.8 for the compliance agent**, a HITL gate framed around reviewing the **draft response**, **per-request cost shown at the gate**, an **append-only JSONL** audit log, and a proposed triage taxonomy and result-JSON schema. (b) On reading the returned JSON, the AI initially treated the `orchestration: code_supervisor` radio value as settled. |
| **What You Changed + Why** | The JSON export captured five concrete operator overrides that materially shaped the spec, each made by accepting/editing a specific card rather than describing changes in prose: (1) **Downgraded compliance Opus 4.8 → Sonnet 4.6** (operator's dropdown) — cost/quality call the AI would not have made unprompted. (2) **Re-centred the HITL gate on the *decision*, not the draft** ("make sure the decision is center-stage… draft is fine to include") — changed the evidence panel ordering in SPEC §5. (3) **Excluded per-request cost from the gate but mandated it in the logs** (toggle `show_cost:false` + note) — split the cost surface between UI and audit. (4) **Switched the audit log from JSONL to `.txt`** (note) — human-readable audit format. (5) **Deferred the triage taxonomy to the AI** and **required runnable dummy data** (notes) — kept the AI's proposed taxonomy but flagged it provisional, and added Phase-0 dummy requests exercising s40/s12/release paths. Separately, the operator's `notes_orchestration` **contradicted their own radio** — selected plain Python + Anthropic SDK but wrote that they were leaning LangChain and asked the AI to choose. The AI did **not** silently take the radio value: it surfaced the conflict and recommended plain Python + Anthropic SDK (framework abstractions fight the very things the rubric scores — per-call cost capture, the interactive pause, deterministic fallbacks — for a fixed 4-stage pipeline), marking it **confirm-pending** in SPEC §0 so the operator can flip it in one place. The net effect: the HTML planner converted an open-ended "design this" into a set of discrete, attributable decisions the operator could accept, override, or annotate per-item — yielding genuine human authorship of the spec without the operator having to draft it. |

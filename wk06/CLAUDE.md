# wk06 — Intelligent Automation System (FOI Multi-Agent CLI)

This file governs all work in `wk06/`. It covers the project goal, the week-specific
working rules, the model-choice rules, and this week's `AI_LOG.md` format. **Repo-wide
conventions — agent identity, git workflow, and commit format — live in the
repository-root `CLAUDE.md`; follow that as well, and this file does not repeat them.**
The detailed design (architecture, file layout, pipeline, feature behaviour) lives in
`SPEC.md` and `PLAN.md`, added later — keep architecture and coding decisions out of
this file.

## Project goal

Build a CLI multi-agent system that automates the repeatable parts of UK Freedom of
Information (FOI) request handling. It processes a folder of FOI request files and,
for each one: a **triage** agent classifies it, a **compliance** agent checks it
against policy documents using RAG, a **response** agent drafts a reply, and a
**supervisor** orchestrates the pipeline and enforces a human-in-the-loop approval
gate — no response is finalised without human approval. Every LLM call is
cost-tracked and every decision is logged to an audit trail.

Aim for the top ("Excellent") band on every axis of the assessment rubric.

## Source of truth & scope

- **`context/slides/` is authoritative** for the brief, requirements, Minimum Viable
  Submission, and assessment rubric. Read it first and build to it.
- `context/LAB_README.md` and `starter/` are beginner-oriented **reference only**.
  Their structure, file layout, and stub signatures are **not** a required template —
  design a cleaner architecture. Copy sample request/policy documents from them if
  useful.
- The detailed design lives in `SPEC.md` and `PLAN.md` (added later) — not here.

## Working rules

- Do all work in `solution/`. Treat `starter/` and `context/` as **read-only**: copy
  from them if useful, but never edit, create, or delete anything inside them.
- When using any library, framework, or CLI (the `anthropic` SDK, ChromaDB, etc.),
  use **Context7 MCP** to confirm current syntax before writing code — at both the
  planning and implementation stages. Do not rely on training data alone for
  library-specific APIs.
- Before calling any task done, run the type checker, tests, and linter.
- When something goes wrong, stop and re-plan — do not keep pushing.
- Prefer editing existing files over creating new ones.

## Model rules

- **Provider: Claude only**, via the official `anthropic` SDK. Never use another
  provider.
- Two-tier model policy:
  - **Best model — `claude-sonnet-4-6`:** for quality-critical, reasoning-heavy work.
  - **Cheapest model — `claude-haiku-4-5`:** for simple, well-scoped work.
- Default to the cheapest model that does the job well; escalate to the best model
  only where the reasoning warrants it. On error or a cost-threshold breach, model
  fallback steps **down** to the cheapest model.
- Reasoning effort / thinking levels are set per use at implementation discretion.

## AI assistance log (`AI_LOG.md`)

Record every meaningful AI-assisted task (generating, refactoring, or debugging code,
or producing a plan, design, or decision) in this week's `AI_LOG.md`. Four fields per
entry — **Date / Task / What AI Generated / What You Changed + Why** — concrete enough
to follow without reading the code. Format each as
`## Prompt N: [AgentName] <short description>`, numbered sequentially (Prompt 0 is the
seeded example). Add the entry as the **last step before committing**, in the same
commit as the work it documents. (`[AgentName]` is the identifier given at the start
of the session — see the repository-root `CLAUDE.md`.)

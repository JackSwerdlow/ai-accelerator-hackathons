# wk09 — Getting "Consultation Insights" Prototype Production Ready
This file governs all work in `wk09/`. It covers the project goal, the week-specific
working rules, the model-choice rules, and this week's `AI_LOG.md` format. **Repo-wide
conventions — agent identity, git workflow, and commit format — live in the
repository-root `CLAUDE.md`; follow that as well, and this file does not repeat them.**

## Source of truth & scope

- **`context/hackathon-brief-2-consultation-insights.pdf` is authoritative** for the brief, requirements, etc.
- **`context/slides_context.md`** provides additional context.

## Specs and plans (concurrent team workflow)

Multiple agents work in parallel producing separate spec and plan documents before any
implementation begins.

New outputs should be named based on the agent that produces them to minimise merge conflicts.

## Working rules

- Do all work in `solution/`. Treat `starter/` and `context/` as **read-only**: copy
  from them if useful, but never edit, create, or delete anything inside them.
- When using any library, framework, or CLI (the `anthropic` SDK, etc.),
  use **Context7 MCP** to confirm current syntax before writing code — at both the
  planning and implementation stages. Do not rely on training data alone for
  library-specific APIs.
- Before calling any task done, run the type checker, tests, and linter.
- When something goes wrong, stop and re-plan — do not keep pushing.
- Prefer editing existing files over creating new ones.

## AI assistance log (`AI_LOG.md`)

This week's log lives at `solution/AI_LOG.md` (the `starter/AI_LOG.md` copy is a
read-only template; all work happens in `solution/`). It records the **AI-assistance
trajectory** for the work — see the
repository-root `CLAUDE.md` for how this differs from, and complements, commit
messages.

**What to log.** Every *meaningful* AI-assisted task, covering **both code and
doc/process changes** (generating, refactoring, or debugging code; and producing or
amending a plan, design, spec, or these `CLAUDE.md`/log files themselves).
"Meaningful" means **anything that was not a one-shot success** — a task that took
substantive iteration or a change of direction. If the AI got it right first time,
the commit message already covers it and no entry is needed. A typo fix on the
second try is not a decision; reworking an agent's output format is.

**Fields.** Each entry has **Date / Task / What AI Generated / What You Changed +
Why** — concrete enough to follow without reading the code. "What You Changed + Why"
is the important one: it captures the corrections the human steered, which is exactly
what git cannot show.

**Header format.** `## [AgentName] YYYY-MM-DD — <short description>`. Do **not** use
global sequential numbering: parallel agents on different machines would collide on
the same number and conflict on merge. Attributed + dated headers need no central
counter and can be appended in any order. (`[AgentName]` is the identifier given at
the start of the session — see the repository-root `CLAUDE.md`.)

Add the entry as the **last step before committing**, in the same commit as the work
it documents.

## Cost tracking

Our API spend is production spend and must be tracked accurately. Maintain a `ai-spend-log.csv`
file that records **all** AI token usage. At the end of the project we should be able to see
how and where AI API spect was used.

Fields should include:
- Timestamp
- AgentName
- Call type  - ClaudeCode/Claude API
- Purpose  - e.g. Codebase review, plan generation, research, code generation/edits
- Model
- Upload tokens
- Download tokens
- Cost [£]

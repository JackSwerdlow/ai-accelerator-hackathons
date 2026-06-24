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

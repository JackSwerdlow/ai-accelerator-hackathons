# Repository Instructions

## Current Project

wk03 is complete; **wk06 is in progress — do all work inside `wk06/`.**

## Repository Layout

This root file holds the **repo-wide conventions** that apply to every week: agent
identity, git workflow, and commit format. Each week additionally has its own
`wkNN/CLAUDE.md` holding that week's goal, working rules, model rules, and `AI_LOG.md`
format. Read both the root file and the active week's file — they are complementary
and deliberately do not repeat each other.

## Agent Identity

Before doing anything else in this repo, ask the user for an identifying name (e.g. Agent1, Agent-Jack). Use this identifier in:
- Every commit message (prefix with `[AgentName]`)
- Every AI_LOG.md entry
- Any notes or instructions left for other agents in plans or documents

## Git Workflow

This repo is shared — multiple agents commit and push simultaneously. Follow this sequence for every task, without exception.

### 1. Before making any file changes
- Run `git pull --rebase`
- If there are conflicts, resolve them preserving both agents' intent — never discard another agent's work
- If a conflict is large or ambiguous, discuss with the user before resolving

### 2. Do the work

### 3. Before committing
- Add an AI_LOG.md entry if the task requires one (see the active week's CLAUDE.md for the AI_LOG format)

### 4. Commit
- Stage only the relevant files — never `git add .` without checking `git status` first
- Every commit message must:
  - Start with `[AgentName]` followed by a short summary (first line under 72 chars)
  - Include a body explaining what changed and why (one bullet per file or concern is fine)

### 5. Push
- Run `git pull --rebase` once more before pushing, in case another agent pushed while you were working
- Push immediately — do not leave commits sitting unpushed

## Commit Message Example

```
[AgentName] Add eligibility logic and unit tests

- src/utils/eligibility.js: pure function implementing 5 priority-ordered
  rules from the content plan; returns { result, measures }
- src/utils/eligibility.test.js: 7 tests covering all ineligible paths,
  eligible path, partial-renter path, and measures logic
```

## Two Records, Two Jobs: Commit Messages vs AI_LOG

This repo keeps two written records. They are **complementary, not duplicates** —
never copy rationale from one into the other.

- **Commit messages are the collaboration audit log.** They capture the
  *final-state rationale*: why the committed code or docs look the way they do.
  Git is the right home for this because it is distributed, attributed,
  timestamped, immutable once pushed, and conflict-free on history — exactly what
  parallel agents on different machines need to reconstruct who changed what, why,
  and in what order. Use `git log`, `git blame`, and `git log -- <path>`.

- **AI_LOG.md is the AI-assistance trajectory.** It captures what git cannot: the
  *path to* the final state — what the AI first generated, what was wrong or
  incomplete about it, and what the human changed and why. The AI's rejected first
  draft never becomes a commit, so this provenance lives nowhere else. It covers
  **both code and doc/process changes**, and is required by the project rubric.
  The per-entry format lives in the active week's `wkNN/CLAUDE.md`.

Rule of thumb: if a task was a **one-shot success**, the commit message says
everything and no AI_LOG entry is needed. If it took **meaningful iteration**
(substantive correction or change of direction — not a typo fix), log the
trajectory in AI_LOG.md.

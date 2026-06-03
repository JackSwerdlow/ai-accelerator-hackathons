# Repository Instructions

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
- Add an AI_LOG.md entry if the task requires one (see project-level CLAUDE.md for rules)

### 4. Commit
- Stage only the relevant files — never `git add .` without checking `git status` first
- Every commit message must:
  - Start with `[AgentName]` followed by a short summary (first line under 72 chars)
  - Include a body explaining what changed and why (one bullet per file or concern is fine)
  - End with: `Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>`

### 5. Push
- Run `git pull --rebase` once more before pushing, in case another agent pushed while you were working
- Push immediately — do not leave commits sitting unpushed

## Commit Message Example

```
[Agent-Jack] Add eligibility logic and unit tests

- src/utils/eligibility.js: pure function implementing 5 priority-ordered
  rules from the content plan; returns { result, measures }
- src/utils/eligibility.test.js: 7 tests covering all ineligible paths,
  eligible path, partial-renter path, and measures logic

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

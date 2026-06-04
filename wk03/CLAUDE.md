# wk03 Project Instructions

## Before Starting Any Work

1. Run `git pull --rebase` (required — see repo-level CLAUDE.md)
2. Read all entries in `starter/AI_LOG.md` added since you last worked
3. If another agent's recent entries conflict with your planned approach, discuss with the user before proceeding

## AI Assistance Log

Every meaningful AI-assisted task must be recorded in `starter/AI_LOG.md`. Add the entry **as the last step before committing** — the log entry and the work it documents must always be in the same commit.

### What counts as a new entry

Add an entry when AI generated, refactored, or debugged code, or produced a meaningful output such as a plan, content design, architecture decision, or test suite.

### What does NOT count as a new entry

Do not add an entry for follow-up clarifications, selecting between options the AI offered, or minor corrections to a previous response.

### Required format — four fields per entry

```markdown
## Prompt N: [AgentName] <short description of task>

| Field | Detail |
|-------|--------|
| **Date** | YYYY-MM-DD |
| **Task** | What you asked the AI to do |
| **What AI Generated** | Specific description of the output — be concrete enough that another agent can understand what was built without reading the code or the plan |
| **What You Changed + Why** | What you modified before committing, and why. If nothing was changed, say so explicitly and state why the output was accepted as-is. |
```

### Numbering

Entries are numbered sequentially across all agents. Before adding your entry, check the last entry number in the file and increment by one. (Prompt 0 is the seeded example.)

## Plan

The final implementation plan is in docs/PLAN.md, the other docs in plans/ and research/ can usually be ignored as the relevent infomation and choices have been outlined in docs/PLAN.md.
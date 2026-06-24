# David — Agent Preferences

This file is specific to **David** and should only be consulted by agents
running in a session where the user identifies as David (DfE). Do not
apply these preferences in sessions run by other team members.

## User Profile

- **Name:** David
- **Organisation:** Department for Education (DfE)
- **Agent name:** agent-david

## Working Preferences

- **Concise communication:** keep responses short and direct — no padding,
  no trailing summaries, no AI-sounding phrasing
- **Don't over-explain:** skip the "here's what I'm about to do" narration;
  just do it and report what happened
- **Autonomous git workflow:** handle all git operations (pull --rebase,
  commit, push) without prompting — David does not want to manage this manually
- **Plain writing:** docs and specs should read like a human wrote them —
  short sentences, no corporate filler, not verbose

## Git Workflow

- Always run `git pull --rebase` before any commit
- Always run `git pull --rebase` again before pushing
- Push immediately after committing — do not leave commits unpushed
- Use `gh auth setup-git` if credential errors occur on push
- Agent name prefix for all commits: `[agent-david]`

## Session Setup

- At session start, confirm which CLAUDE.md files are in scope
- Agent name is `agent-david` — use this in all commits and AI_LOG entries

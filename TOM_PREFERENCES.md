# Tom Farley — Agent Preferences

This file is specific to **Tom Farley** and should only be consulted by agents
running in a session where `git config user.name` returns "Tom Farley". Do not
apply these preferences in sessions run by other team members.

## User Profile

- **Name:** Tom Farley
- **Role:** Data Engineer (2 years experience)
- **Employer:** UK Health Security Agency (UK Civil Service)
- **Background:** Physicist, nuclear fusion PhD
- **Strengths:** Python, pytest, pandas
- **Less experienced in:** front-end development, APIs, SQL, networking, security

## Working Preferences

- **Pedagogical explanations:** explain concepts before writing code, show
  working examples, and flag subtle contradictions or gotchas explicitly.
- **Plan first:** always plan an activity first, surfacing unknowns and asking
  clarifying questions with multiple choices and a recommended option, presenting
  one question at a time.
- **Challenge assumptions:** make sure we are asking the right questions and
  using the right tooling or methods before investing in an approach.
- **Document:** add detailed comments to aid learning, particularly in areas
  where Tom lacks experience; give analogies to Python/data engineering where
  appropriate.

## Conversation Management

- At the start of a session, tell Tom which instruction files are being
  referenced (e.g. root `CLAUDE.md`, `wk06/CLAUDE.md`, this file).
- If the model is set to an expensive model (e.g. Opus), confirm with Tom
  whether to switch for standard tasks. Conversely, if the session involves
  complex research or planning, prompt that a more powerful model may be
  appropriate if not already selected.
- If the conversation veers suddenly off topic, suggest the prompt might be
  better handled in a separate session.

## Learning Outputs

Where complex topics arise in sessions, produce concise learning resources
(cheat sheets, primers, worked examples) and save them to `learning_materials/`
at the repo root. Include diagrams where helpful. Particularly focus on areas
with back-and-forth clarification exchanges, as these signal genuine learning
gaps worth capturing. Maintain an index of resources produced and a note of
areas that warrant future exploration.

Note: `docs/research/` (inside each week folder) is for project-related
research materials, not personal learning outputs.

## Git Workflow

- Always run `git pull --rebase` before any commit
- Always run `git pull --rebase` again before pushing
- Push immediately after committing — do not leave commits unpushed
- Use `gh auth setup-git` if credential errors occur on push
- Agent name prefix for all commits: `[agent-tom]`

## Meta-Reviews

At 1–2 natural pause points per project (e.g. end of a sprint, after a major
deliverable, and at project close), conduct a structured meta-review. The goal
is not just to reflect, but to produce actionable updates to instruction files,
workflows, and learning materials so that future projects start better than this
one did.

### When to trigger

- After completing a major milestone or deliverable (mid-project check-in)
- At project close, before the next project starts

### What to cover

**AI usage**
- Which prompt patterns worked well and which needed repeated correction?
  (Recurring AI_LOG corrections signal a systematic gap worth fixing in CLAUDE.md)
- Were the right models selected for each task? (Did we reach for Opus when
  Haiku would have sufficed, or vice versa?)
- Were agents given enough upfront context, or did sessions lose time to
  re-establishing background?
- Were there tasks that should have been delegated to subagents but weren't, or
  tasks where subagents added overhead without benefit?

**Project workflow**
- Where did rework or churn appear in the commit history? What caused it?
- Which conventions (git workflow, naming, file layout) were followed cleanly,
  and which were missed or inconsistently applied?
- Was the research/documentation store used effectively, or did agents
  re-research things already captured?
- What setup or scaffolding, done earlier, would have saved the most time?

**Learning**
- Which topics generated back-and-forth clarification (a signal of genuine
  gaps)? Are those now covered in `learning_materials/`?
- What analogies or mental models proved useful for bridging background
  knowledge (physics/data engineering) to new domains?
- What would a concise "lessons learned" primer for the next project look like?

**Configuration carry-forward**
- Should any CLAUDE.md rules be added, sharpened, or retired based on what
  actually happened?
- Should skills be created or updated?
- Should reference documents like `LOCAL_DEV_SETUP.md` or `ORGANISATION_CONTEXT.md` be created or updated?
- Are there new permission allowlist entries worth adding to reduce friction?
- Should `TOM_PREFERENCES.md` be updated to reflect refined individual working preferences?

### Output

A meta-review should produce concrete artifacts, not just observations:
- Updated `CLAUDE.md` or `wkNN/CLAUDE.md` entries where rules were missing
- New or updated entries in `learning_materials/` for identified gaps
- A brief written summary (saved to `docs/` or `learning_materials/`) capturing
  the 3–5 highest-leverage changes for next time — concise enough to read at
  the start of the next project

## Session Setup

- At session start, confirm which CLAUDE.md files are in scope
- Agent name is `agent-tom` — use this in all commits and AI_LOG entries
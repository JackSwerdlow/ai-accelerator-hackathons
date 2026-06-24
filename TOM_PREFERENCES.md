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
(cheat sheets, primers, worked examples) and save them to the relevant week's
`docs/research/` folder. Include diagrams where helpful. Particularly focus on
areas with back-and-forth clarification exchanges, as these signal genuine
learning gaps worth capturing. Maintain an index of resources produced and a
note of areas that warrant future exploration.

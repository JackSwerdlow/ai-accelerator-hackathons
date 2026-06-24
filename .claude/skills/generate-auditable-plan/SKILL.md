---
name: generate-auditable-plan
description: Build a self-contained, single-file HTML "plan wizard" the user can open in a browser to step through a plan one decision at a time, tick tasks, make single choices (with conditional branches), capture notes, edit config blocks, optionally assign owners to a team, and write those changes back into the file itself (choices, tasks, notes, and config in a markdown block; names/owners in a JSON block) or export deterministic JSON. Use for ANY kind of plan — project plans, runbooks, checklists, decision guides, onboarding, event planning, research protocols — whenever the user wants an auditable, interactive, shareable plan in one HTML file. The plan content is plain markdown; styling and whether there is a team are user preferences you must ask about.
---

# generate-auditable-plan

Produce ONE self-contained `.html` file: an interactive wizard whose content is an
auditable markdown document. The reader steps through it one screen at a time, makes
choices and ticks tasks, and their answers are written back into the file (or exported as
JSON). The HTML/CSS/JS is **machinery**; the plan is plain markdown anyone can read
top-to-bottom in a diff.

## What you must do

### 1. Ask the user first (do not assume)
Before writing anything, settle these — they change the output:
- **Is there a team?** If no, it is a solo plan: no names panel, no owner dropdowns, no
  `team` in the JSON. If yes, **how many people**, and their names if known.
- **Styling.** Styling is the user's preference, not fixed. Offer a sensible default
  (the template ships a clean neutral theme) and ask if they want a specific look
  (brand colours, a design system, dark, minimal). **Every colour is a CSS variable in
  `:root`** — restyle by overriding those tokens (`--ink`, `--bg`, `--surface`,
  `--surface-sel`, `--accent`, `--on-accent`, `--muted`, …); don't hunt literals. Keep the
  class names. The verifier computes real WCAG contrast for body text, the primary button,
  the selected option and muted text — all must be ≥4.5:1 (see requirement 9).
- **The subject** of the plan and its decisions/steps, if not already clear.

(When a parent agent has already supplied these in your task prompt, use them and skip the
questions.)

### 2. Build from the template
Copy `template.html` (in this skill folder) to the target path. Fill the placeholders:
- `{{TITLE}}`, `{{HEADER_TITLE}}`, `{{BANNER_TAG}}`, `{{BANNER_TEXT}}` — short labels.
- `{{CONFIG_JSON}}` — the team config, e.g. `{ "hasTeam": true, "members": ["Alex","Sam","Jo"] }`
  or `{ "hasTeam": false, "members": [] }` for a solo plan.
- `{{PLAN_MARKDOWN}}` — the plan, written with the conventions below.
- Restyle the `<style>` block per the user's preference.
- **Never edit the final machinery `<script>` block** (the big one). It is identical across
  every plan this skill makes; all variation lives in the markdown, the `#config`, and the
  styling. Editing it breaks grading and the proven behaviour.

### 3. Markdown conventions (this is the whole content model)
````markdown
# Plan title
First non-blank line after the title becomes the lede (sits under the H1).

## A step heading
Prose paragraphs, **bold**, *italic*, `code`, [links](https://example.com), and
- plain bullets.

## A single-choice step
- ( ) {optionA} First option — the {id} in braces names it.
- (x) {optionB} Second option — (x) marks the default selection.

## A conditional step @if=optionA
*One-line note: this step only appears when "First option" is chosen above. The
`@if=optionA` marker is what makes it conditional; if that option isn't chosen the section
stays in the file but its boxes reset.*
- [ ] A task shown only on that branch

## A task list with owners {assign}
- [ ] First task — {assign} adds an owner dropdown per task (no-op when there is no team).
- [x] A task that starts ticked.

## A notes field
```note Reviewer notes
Use a fenced `note` block when the reader should be able to add free-text context.
Whatever they type is written back into this fenced block on save.
```

## An editable config block
```config yaml Proposed config
output_dir: ./publication_outputs
fail_on_warning: true
```
````
Rules:
- The plan content lives ONLY in the markdown block. Do **not** hand-write
  fieldset/checkbox/radio HTML anywhere. (You may freely use the *words* "checkbox",
  "radio", etc. in prose — only literal `<fieldset>`/`<input type="radio|checkbox">` tags are
  banned.)
- ` ```note [label...]` renders a textarea. The optional text after `note` becomes the field
  label. The block body is the saved note content.
- ` ```config [format] [label...]` renders a monospace textarea for editable structured text.
  The optional first token after `config` is treated as the format (`yaml`, `json`, etc.);
  any remaining text becomes the field label. The block body is written back into the file
  on save.
- Every `@if=` conditional step MUST carry a note that **explains the condition** (use words
  like "only", "appears when", "shown if … is chosen"), so the file stays auditable read
  top-to-bottom. A throwaway sentence that doesn't mention the condition fails verification.
- Use `{assign}` only when there is a team; on a solo plan it simply renders nothing. The
  owner dropdowns default to members in the **document order of the checkboxes** under that
  heading (1st task → member 1, …, wrapping round), so don't reorder tasks expecting owners
  to follow.
- `{assign}` and `@if=` MAY appear on the same heading
  (`## Title {assign} @if=someId`) — they're independent and compose.
- Give every choice option a `{id}`; reference those ids in `@if=`.

### 4. Verify before you finish
Run the verifier from this skill folder against your file:
```
.\.venv\Scripts\python.exe .github\skills\generate-auditable-plan\verify.py <path-to-your-file.html>
```
It prints PASS/FAIL per requirement. Fix every FAIL. Do not report success until it prints
`0 failed`. The verifier checks structure, that the machinery is unaltered, that the markdown
parses into the conventions, that team config is consistent, real colour contrast, and it
simulates the JSON export and write-back to confirm completeness, editable note/config
round-tripping, hidden-step pruning and title-first ordering.

If you generate a temporary smoke-test HTML file while validating, write it with Python using
UTF-8 output rather than a PowerShell string write. PowerShell can alter punctuation in the
generated file and cause false `MACH` or `R14` failures even when the template machinery is
correct.

The verifier prints **19** rows: the 18 numbered requirements below plus one `MACH` row — an
integrity gate confirming the machinery `<script>` is byte-for-byte the template's (after
whitespace normalisation). "Met all requirements" means the run ends with `0 failed`.

The most reliable workflow is to copy `template.html` to the target file, then make *targeted*
edits to the placeholders / `#config` / `#plan` / `<style>` only. Authoring the file from
scratch risks drifting the machinery and failing `MACH`.

## Requirements (the rubric — every one must hold)
1. **One auditable markdown block.** Exactly one `<script type="text/markdown" id="plan">`
   holding all plan content as plain markdown, readable top-to-bottom. Plus exactly one
   `<script type="application/json" id="state">` (machinery: names/owners only) and one
   `<script type="application/json" id="config">` (team config).
2. **Markdown-driven wizard.** Steps/choices/conditionals/assign/checkboxes come from the
   markdown conventions above — no hand-written question markup.
3. **Self-contained.** Inline CSS + inline vanilla JS only. No `<script src=>`, no external
   stylesheet `<link>`, no network dependency. Opens from `file://`.
4. **Team is configurable.** `#config` drives it: a team shows a names panel + owner
   dropdowns + a `team` array in the JSON; a solo plan shows none of those. (You must have
   asked the user, or used what the parent supplied.)
5. **Owner dropdowns** appear on `{assign}` steps when there is a team.
6. **JSON export** present.
7. **One combined "Generate & copy JSON" button** (no separate copy button).
8. **No "Download JSON" button.**
9. **Styling is user preference**, applied in the `<style>` block; still accessible
   (visible focus, usable at 320px, full keyboard nav) and **contrast ≥4.5:1 — enforced**.
   The verifier computes the real WCAG ratio for body text (`--ink` on `--bg`) AND for the
   primary button (`.btn` text on `.btn` background). White button text needs a genuinely
   dark accent — many mid-tone reds, teals, greens and oranges land at ~3–4:1 with white and
   will FAIL. Fixes: darken the accent until `.btn` text hits 4.5:1, or set `.btn { color }`
   to a dark ink and use a light accent. The shipped default (`--accent: #2b5fd9`, white
   text → 5.6:1) passes; re-check after every recolour with the verifier.
10. **Write-back.** "Save to this file" writes ticks, choices, notes, and editable config
  blocks into the markdown markers and names & owners into the `#state` block.
11. **File is the single source of truth.** No `localStorage`/`sessionStorage` for plan
  state; ticks, choices, notes, and editable config blocks come from the markdown,
  names & owners from `#state`.
12. **Session-only save target.** The save handle is picked fresh each session and never
    reused as the save target across sessions.
13. **Picker positioning only.** A remembered folder (IndexedDB) positions the picker; it is
    never the save target. First run defaults to home/Documents.
14. **Save works** in Chrome/Edge (File System Access API) with a graceful message where
    unsupported.
15. **Conditional sections kept + reset + noted.** Inactive `@if=` sections stay in the file
    (auditable), their boxes reset, and each carries an explanatory note.
16. **No hidden-step leakage.** Ticks on hidden steps never appear in the JSON or the saved
    markdown (`pruneHidden`).
17. **Complete JSON.** Every visible step's choice (id + label), every checkbox (label +
  done, plus owner on `{assign}` steps with a team), and every visible `note` / `config`
  block.
18. **Title-first deterministic JSON.** `step` before `choice`/`tasks`; `task` before
    `done`/`owner`; same selections → byte-identical output (document order, no timestamps,
    no randomness).

## Files in this skill
- `template.html` — copy this; fill placeholders, restyle, write the markdown.
- `verify.py` — `.\.venv\Scripts\python.exe .github\skills\generate-auditable-plan\verify.py <file>`; grades against all 18 requirements plus the `MACH` integrity check.

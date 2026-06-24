---
name: generate-html-plan
description: 'Generate interactive HTML planning documents for refactors, new features, or similar multi-phase work. Produces two HTML files: a design brainstorm for gathering decisions (with radio options, editable text, dropdowns, notes fields, and JSON export) and a combined plan viewer (tabbed PRD / analysis / task list / config) with live-editable sections. Use when the user asks to create a plan, spec, PRD, task list, or analysis as HTML, or when they want an interactive planning document they can edit and paste back into chat.'
argument-hint: 'Describe the project or refactor you want to plan, what documents you need (PRD, analysis, task list), and any design decisions still open.'
user-invocable: true
---

# Generate Interactive HTML Plan

## What This Skill Does

Produces one or two standalone HTML files that let a human review, annotate, and feed back on a
plan without leaving the browser:

1. **Design Brainstorm** (`design_brainstorm.html`) — an interactive questionnaire for
   gathering open design decisions before the plan is finalised.
2. **Combined Plan Viewer** (`{project}_plan.html`) — a tabbed reference document that
   combines the PRD, analysis, task list, and any config/schema documentation into one
   navigable page with live-editable fields.

Both files are self-contained (no external dependencies) and work offline in any modern browser.

## Use This Skill When

- The user asks for a "plan", "spec", "PRD", "task list", or "analysis" as an HTML document.
- The user wants an interactive planning document they can edit and paste back into chat.
- A multi-phase refactor or feature needs a design brainstorm before implementation.
- The user wants to consolidate several markdown planning docs into one navigable HTML view.

## Do Not Use This Skill When

- The user wants a single markdown file (use normal file creation).
- The task is a one-step code change that does not need planning documents.
- The user asks for a slide deck, PDF, or other non-HTML format.

## Companion Files

- Load the [HTML component library](./references/html-components.md) for the reusable HTML/CSS/JS
  patterns for each interactive element.
- Load the [design lessons learned](./references/design-lessons.md) for feedback-driven rules on
  what works and what to avoid in these documents.

## Procedure

### Step 1: Determine which documents are needed

Ask or infer which combination the user needs:

| Scenario | Documents to produce |
|----------|---------------------|
| Open design decisions remain | Design Brainstorm + Combined Plan Viewer |
| Design is settled, need implementation plan | Combined Plan Viewer only |
| User wants to review options before committing | Design Brainstorm only |

### Step 2: Gather context

Before generating HTML, collect:
- Project name and one-line summary.
- The open design decisions (for the brainstorm).
- The core features, bug fixes, acceptance criteria (for the plan viewer).
- The task list with phases, checkpoints, and verification steps.
- Any config schemas, data models, or API contracts.
- Any existing markdown docs to consolidate.

### Step 3: Generate the Design Brainstorm HTML

Use the component patterns from the companion reference file. The brainstorm HTML must include:

#### Required interactive elements

Use the component patterns from the [HTML component library](./references/html-components.md).
The brainstorm HTML must include all of these, as appropriate to the design decisions being gathered:

| Element | Purpose |
|---------|--------|
| **Radio option cards** | Choose between design alternatives |
| **Free-text notes** | One textarea per section |
| **Dropdown overrides** | Fine-tune sub-decisions (with per-row notes) |
| **Checkbox toggles** | Enable/disable rules or features |
| **Editable config/schema** | Free-text `<textarea>` with proposed config |
| **Generate Summary + Copy to Clipboard** | JSON export with toast |
| **JSON output panel** | Dark code block, hidden until generated |
| **Save button** | Self-save mechanism (see component library) |

For detailed rules on each element (required fields, badge placement, description depth), see
the [design lessons learned](./references/design-lessons.md).

#### Self-save mechanism

Every HTML planning document must include a Save button so the user can close the browser and
reopen later with all state intact. The implementation (syncing live form values into DOM
attributes before serializing `outerHTML` as a downloadable Blob) is defined in the
[Self-Save component](./references/html-components.md).

#### Section structure and design rules

Follow the [design lessons learned](./references/design-lessons.md) for section layout, notes
placement, config editing, validation rule descriptions, and all anti-patterns to avoid.
Key principles: numbered section cards, notes textarea in every decision section, config as
free-text textarea, group related decisions (max ~5 options per radio group).

#### JSON output fidelity

The generated JSON must be a **faithful, complete snapshot of every user-editable element in the
HTML**. It must be possible to reconstruct the exact state of the page from the JSON alone. If a
new interactive element is added to the HTML, a corresponding key must appear in the JSON — no
element may be silently omitted.

For the full JSON output rules (key naming, empty-value stripping, scroll-to-output), see the
[design lessons learned](./references/design-lessons.md). For the collection JS template, see
the [Generate + Copy component](./references/html-components.md).

### Step 4: Generate the Combined Plan Viewer HTML

The plan viewer consolidates the finalised documents into a tabbed, navigable HTML page.

#### Required tabs

Include whichever tabs are relevant to the project:

| Tab | Content | Interactive elements |
|-----|---------|---------------------|
| **Overview** | Summary stats, module diagram, workflow flow, core features, bug fixes (if any) | None (read-only reference) |
| **Analysis** | Code inventory, existing test coverage, function extraction map, validation rules, data models | Editable notes fields for each section |
| **PRD** | User stories, key user flows, data models, logging format, comparison/output formats, risks, acceptance criteria, conventions | Editable notes fields; AC tables should be in this tab |
| **Task List** | Phased implementation plan with colour-coded task badges | Editable notes field per phase; task status could be toggleable |
| **Config Schema** | Config examples with syntax highlighting, CLI invocation, output naming | Editable config text blocks |

#### Required visual elements

Use the component patterns from the [HTML component library](./references/html-components.md):

- Top bar (gradient header), tab navigation, summary stat grid
- Module diagram (grid of boxes), workflow flow (horizontal pill chain)
- Colour-coded task badges (consistent set from the component library)
- Phase headers (numbered circle + name + goal + AC refs)
- Striped tables (sticky headers, hover highlight) for ACs, validation rules, data models
- Dark-themed code blocks (CSS classes: `.key`, `.val`, `.comment`)
- Collapsible `<details>/<summary>` for long content

#### Badge colour scheme

Use the badge CSS classes defined in the companion [HTML component library](./references/html-components.md).
The full set of badges (`badge-feature`, `badge-bug`, `badge-phase`, `badge-verify`, `badge-lint`,
`badge-review`, `badge-commit`, `badge-test`, `badge-doc`, `badge-ac`) and their colours are
defined there. Use them consistently across both HTML files.

#### Phase checkpoint order

In the task list, each phase's checkpoint tasks must appear in this order:
1. Lint (`badge-lint`)
2. Human Review (`badge-review`)
3. Commit (`badge-commit`)

State this order in the plan description and enforce it in every phase table.

#### Acceptance criteria

- Define acceptance criteria with testing outcomes for each core feature in the PRD tab.
- Use AC tables with columns: AC ID, Criterion, Verified By (task reference).
- Reference ACs in each phase header of the task list (e.g. "ACs: AC-1.1, AC-1.2, AC-1.3").

#### Editable sections in the plan viewer

The plan viewer is primarily a reference document, but should include these editable elements:

| Element | Where | Purpose |
|---------|-------|---------|
| Notes textarea | Bottom of each card/section | Let the reviewer add comments or change requests |
| Editable config blocks | Config Schema tab | Let the user modify proposed configs directly |
| Task status badges | Task List tab (optional) | Let the user mark tasks as done/skipped |

Include a "Generate Feedback" button, copy-to-clipboard, and a **Save** button at the bottom of
each tab. The Generate Feedback button collects all notes, modified configs, and status changes
into JSON for pasting back into chat. The Save button persists the current state into the HTML
file using the same self-save mechanism described for the brainstorm document.

### Step 5: Write the files

- Save the Design Brainstorm to the location the user specifies (default: `tmp_test_logs/design_brainstorm.html`).
- Save the Combined Plan Viewer to the location the user specifies (default: `tmp_test_logs/{project}_plan.html`).
- Confirm creation and suggest opening them in a browser.

## HTML Quality Rules

### Mandatory

- Self-contained: no external CSS, JS, or font dependencies.
- Responsive: must work on mobile (use `max-width`, flex-wrap, responsive grid).
- Accessible: all interactive elements must be keyboard-navigable; use semantic HTML.
- No framework dependencies: vanilla HTML + CSS + JS only.
- Print-friendly: code blocks and tables should not overflow when printed.

### Strongly preferred

CSS custom properties for colours, consistent font stacks (see component library), smooth
transitions (150ms), toast notifications for copy/save, scroll-to-output after generation.

## Anti-Patterns to Avoid

See the detailed anti-pattern tables and design rules in the companion
[design lessons learned](./references/design-lessons.md) file. That file is the single source of
truth for what worked, what failed, and the specific fixes. Do not duplicate those rules here;
instead, load that file and follow it.

## Success Checks

- [ ] Both HTML files open correctly in a browser with no console errors.
- [ ] All interactive elements (radios, checkboxes, dropdowns, textareas) work correctly.
- [ ] "Generate Summary" produces valid JSON with all user inputs captured.
- [ ] The JSON is a faithful, complete snapshot — every interactive element has a corresponding key.
- [ ] "Copy to Clipboard" works and shows a toast.
- [ ] "Save" persists all current state into the HTML file and the file reopens correctly.
- [ ] The plan viewer tabs switch correctly and all content is visible.
- [ ] Badge colours are consistent between both files.
- [ ] Phase checkpoints appear in lint → review → commit order.
- [ ] Acceptance criteria appear in the PRD tab with task references.
- [ ] Config schema sections use editable textareas, not field-rename tables.
- [ ] Every section with sub-decisions includes a notes textarea.
- [ ] The HTML is self-contained and works offline.

## Scope Notes

- This skill produces the HTML files only. It does not create the underlying markdown planning
  documents (PRD, analysis, task list). If those are needed, create them first, then use this
  skill to generate the HTML consolidation.
- The skill can be used iteratively: generate a brainstorm first, collect feedback, then generate
  the plan viewer with the finalised decisions.
- Keep the HTML focused on the planning content. Do not add features like authentication,
  server-side persistence, or multi-user collaboration. Client-side self-save is the only
  persistence mechanism.

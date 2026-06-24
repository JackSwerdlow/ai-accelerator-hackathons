# Design Lessons Learned

Feedback-driven rules from previous HTML planning documents. Apply these when generating any
interactive planning HTML.

## What Worked Well

These elements received positive feedback and should be included in future documents:

| Element | Why it worked |
|---------|--------------|
| Workflow flow component (horizontal pill chain) | Clear visual overview of the process. Easy to understand at a glance. |
| Acceptance criteria tables with "Verified By" column | Made the relationship between ACs and tasks concrete and traceable. |
| Colour-coded task category badges | Made it easy to scan a long task list and identify task types visually. |
| Config Schema tab with syntax-highlighted examples | Users liked having a dedicated tab for config with real examples. |
| Free-text notes fields in every section | Allowed users to provide nuanced feedback rather than just choosing options. |
| JSON export with copy-to-clipboard | Made it trivial to paste decisions back into chat for the agent to act on. |
| Editable text inputs for clarifications | Gave users a natural way to modify proposals without having to describe changes in words. |
| Tab navigation for long documents | Prevented information overload by splitting content into logical sections. |

## What Did Not Work

These elements received negative feedback. Avoid or improve them:

| Anti-pattern | Feedback | Fix |
|-------------|----------|-----|
| "What this refactor does" cards in Overview tab | "A bit naff" — too vague, marketing-style language | Use concrete feature descriptions with specific scope. Show module names and file counts, not abstract benefits. |
| "Bug fixes" section in Overview tab | "A bit uninformative" — listed issues but not what the fix actually does | Add a "Fix description" column explaining the concrete change, not just the symptom. |
| Validation rules section with just checkbox names | "Insufficient detail on the rules implemented" | Include a description for each rule: what it validates, what error it prevents, and what the error message looks like. |
| Config schema as table of individual field name inputs | "Should just have a free-text config file which I can modify at will" | Replace with a single editable `<textarea>` pre-filled with the full proposed config. Let the user restructure it freely. |
| Sub-decision table without per-row notes | "Maybe should have allowed notes for every override" | Add a notes column (text input) to every override row, or at minimum a textarea per section. |
| Acceptance criteria in Overview tab | Contextually belongs in the PRD. Users had to switch tabs to find related information. | Place AC tables in the PRD tab alongside the features they verify. |

## Decision Input Design Rules

1. **Every radio group needs all four parts**: title, description, at least one pro, and at least
   one con. Options without pros/cons feel unsubstantiated.

2. **Pre-select a recommended default** for every radio group. Add a `Recommended` badge.
   Include a `Current` badge if the option matches existing behaviour.

3. **Notes fields are mandatory, not optional**. Every section that asks the user to make a
   decision must include a notes textarea. Users consistently use these to provide context that
   cannot be captured by radio buttons alone.

4. **Per-row notes for sub-decisions**. When a table presents multiple fine-grained overrides,
   add a notes column so the user can explain individual choices. A single textarea at the bottom
   of a large table is insufficient.

5. **Config editing must be free-form**. Do not present config schemas as tables of individual
   field renames. Present the full config as an editable textarea with monospace font and
   syntax-appropriate formatting. Users want to restructure, add comments, and rearrange freely.

6. **Validation rule descriptions must be specific**. Include: what the rule checks, what happens
   when it fails (error message or behaviour), and an example of invalid input. A checkbox with
   just `reject_empty_fields` tells the user nothing.

## Plan Viewer Design Rules

1. **Stat cards must be concrete**. Only use stat grids for genuinely informative numbers:
   task count, phase count, AC count, module count. Do not use them for vague metrics like
   "3 Design Principles" or "5 Key Benefits".

2. **Bug fix descriptions must explain the fix**, not just identify the bug. Include columns for:
   Issue, Location (module/function), Fix Description (what changes).

3. **Phase checkpoints always follow lint → review → commit order**. This matches the team's
   actual workflow and was specifically requested.

4. **AC tables belong in the PRD tab**, not the Overview tab. Each core feature section should
   include its own AC table.

5. **Task badges should use consistent colours** across all tabs and both document types.
   See the badge colour scheme in the SKILL.md file.

6. **Collapsible sections for long content**. Use `<details>/<summary>` when a section would
   otherwise be more than ~20 rows. This keeps the page scannable.

7. **Each tab should have its own Generate Feedback + Copy button** so the user can submit
   feedback for one section without scrolling to the bottom of the entire document.

## JSON Output Rules

1. **Strip empty values**. Do not include keys with empty string values or empty objects in the
   generated JSON. This makes the output cleaner for pasting into chat.

2. **Use descriptive keys**. The JSON key should match the section or decision name, not an
   internal element ID. Use `module_structure` not `sec-modules-radio`.

3. **Include all input types**. The JSON must capture: radio selections, checkbox states,
   dropdown values, textarea content, and editable config block content.

4. **Scroll to output**. After generating the JSON, smooth-scroll to the output panel so the
   user can see it immediately.

5. **Toast on copy**. Show a brief green toast confirmation when the JSON is copied to clipboard.
   Use a 2-second timeout.

6. **Exact fidelity between HTML and JSON**. The JSON output must be a complete, faithful
   snapshot of every user-editable element in the HTML. If a second agent were given only the
   JSON, it should be able to reproduce every selection, override, note, and config edit the
   user made. If a new interactive element is added to the HTML, a corresponding key must
   appear in the JSON — no element may be silently omitted.

## Self-Save Rules

1. **Every planning HTML must include a Save button**. The user must be able to close the
   browser, reopen the saved file, and find all their work intact.

2. **Sync live form state into DOM attributes before serializing**. `outerHTML` captures
   original markup, not current values. The `prepareForSave()` function must walk all
   `<input>`, `<textarea>`, and `<select>` elements and set their attributes to match the
   live state. See the Self-Save component in the HTML component library for the implementation.

3. **Also sync visual CSS classes**. `.selected` on option cards and `.checked` on checkbox
   cards must be synced so styling is preserved on reload.

4. **Download, not overwrite**. The Save button triggers a browser download of the modified
   HTML. It does not attempt to overwrite the original file (which is not possible from a
   browser without a server). The user replaces the original file manually if they wish.

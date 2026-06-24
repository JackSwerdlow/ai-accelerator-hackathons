# HTML Component Library

Reusable HTML/CSS/JS patterns for interactive planning documents.

## CSS Variables

Every planning HTML file must define this `:root` block. Colours can be adjusted per project but
the variable names must be consistent.

```css
:root {
  --bg: #f8f9fa; --card: #fff; --border: #dee2e6;
  --accent: #0d6efd; --accent-light: #e7f1ff;
  --text: #212529; --muted: #6c757d;
  --green: #198754; --green-light: #d1e7dd;
  --red: #dc3545; --red-light: #f8d7da;
  --amber: #ffc107; --amber-light: #fff3cd;
  --purple: #6f42c1; --purple-light: #e8dff5;
  --teal: #20c997; --teal-light: #d2f4ea;
  --pink: #d63384; --pink-light: #f7d6e6;
  --orange: #fd7e14; --orange-light: #ffe5d0;
}
```

## Base Styles

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6;
  padding: 2rem 1rem;
}
.container { max-width: 960px; margin: 0 auto; }
```

---

## Component: Radio Option Card

Use for mutually exclusive design choices.

### HTML pattern

```html
<div class="option-group" data-name="decision_name">
  <label class="option-card" onclick="selectRadio(this)">
    <input type="radio" name="decision_name" value="option_a" checked>
    <div class="option-body">
      <div class="option-title">Option A — Short label <span class="badge badge-rec">Recommended</span></div>
      <div class="option-desc">One-sentence description of what this option means.</div>
      <div class="option-pro">+ Benefit of choosing this option</div>
      <div class="option-con">− Drawback of choosing this option</div>
    </div>
  </label>
  <!-- more options ... -->
</div>
```

### CSS

```css
.option-group { margin-bottom: 1rem; }
.option-card {
  border: 2px solid var(--border); border-radius: 6px;
  padding: .85rem 1rem; margin-bottom: .5rem; cursor: pointer;
  transition: border-color .15s, background .15s;
  display: flex; align-items: flex-start; gap: .75rem;
}
.option-card:hover { border-color: var(--accent); background: var(--accent-light); }
.option-card.selected { border-color: var(--accent); background: var(--accent-light); }
.option-card input[type="radio"] { margin-top: .25rem; flex-shrink: 0; accent-color: var(--accent); }
.option-card .option-body { flex: 1; }
.option-card .option-title { font-weight: 600; font-size: .95rem; }
.option-card .option-pro { color: var(--green); font-size: .85rem; }
.option-card .option-con { color: var(--red); font-size: .85rem; }
.option-card .option-desc { color: var(--muted); font-size: .85rem; }
```

### JS

```js
function selectRadio(card) {
  const group = card.closest('.option-group');
  group.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  card.querySelector('input[type="radio"]').checked = true;
}
```

---

## Component: Checkbox Toggle Card

Use for independent on/off switches (validation rules, feature flags).

### HTML pattern

```html
<div class="checkbox-group">
  <label class="checkbox-card checked" onclick="toggleCheck(this)">
    <input type="checkbox" data-rule="rule_name" checked>
    <span>Rule description (not just the name)</span>
  </label>
  <!-- more checkboxes ... -->
</div>
```

### CSS

```css
.checkbox-group { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; }
.checkbox-card {
  border: 1px solid var(--border); border-radius: 4px;
  padding: .4rem .75rem; cursor: pointer; font-size: .85rem;
  display: flex; align-items: center; gap: .4rem;
  transition: border-color .15s, background .15s;
}
.checkbox-card:hover { border-color: var(--accent); }
.checkbox-card.checked { border-color: var(--accent); background: var(--accent-light); }
.checkbox-card input { accent-color: var(--accent); }
```

### JS

```js
function toggleCheck(card) {
  const cb = card.querySelector('input[type="checkbox"]');
  cb.checked = !cb.checked;
  card.classList.toggle('checked', cb.checked);
}
```

---

## Component: Notes Textarea

Use in every section that asks the user to make a decision.

### HTML pattern

```html
<div class="text-input-group">
  <label for="section_notes">Notes / modifications</label>
  <textarea id="section_notes" placeholder="e.g. specific concern or alternative idea…"></textarea>
</div>
```

### CSS

```css
.text-input-group { margin-bottom: 1rem; }
.text-input-group label { display: block; font-weight: 600; font-size: .9rem; margin-bottom: .3rem; }
.text-input-group textarea {
  width: 100%; border: 1px solid var(--border); border-radius: 4px;
  padding: .5rem .75rem; font-size: .9rem; font-family: inherit;
  min-height: 70px; resize: vertical;
}
.text-input-group .hint { color: var(--muted); font-size: .8rem; margin-top: .2rem; }
```

---

## Component: Editable Config Block

Use for config schemas, YAML/JSON files, or any structured text the user may want to modify
directly. Always prefer this over a table of individual field name inputs.

### HTML pattern

```html
<div class="config-edit-group">
  <label for="config_yaml">Proposed config (edit freely):</label>
  <textarea id="config_yaml" class="config-editor"># comparison_config.yaml
source_type: local
import_folder_1: ./data/old
import_folder_2: ./data/new
local_output_folder: ./output

pairing:
  mode: by_name
  include_files:
    - summary.xlsx
    - detail.xlsx</textarea>
</div>
```

### CSS

```css
.config-editor {
  width: 100%; min-height: 200px; resize: vertical;
  background: #1e1e1e; color: #d4d4d4; border-radius: 6px;
  padding: 1rem; font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: .82rem; line-height: 1.5; border: none; tab-size: 2;
}
```

---

## Component: Dropdown Override (Sub-decision Table)

Use within a section when there are multiple fine-grained sub-decisions to make.

### Rules

- Include a description of each rule (not just a name).
- Include a notes column or a per-group textarea for explanations.

### HTML pattern

```html
<table class="validation">
  <thead><tr><th>Rule</th><th>Description</th><th>Current</th><th>Override</th><th>Notes</th></tr></thead>
  <tbody>
    <tr>
      <td>rule_name</td>
      <td>What this rule validates and the error it prevents</td>
      <td>Fail fast</td>
      <td><select data-decision="rule_name">
        <option value="fail_fast" selected>Fail fast</option>
        <option value="warn_skip">Warn &amp; skip</option>
      </select></td>
      <td><input type="text" data-note="rule_name" placeholder="Reason…" style="width:140px;"></td>
    </tr>
  </tbody>
</table>
```

---

## Component: Tab Navigation

Use for the combined plan viewer.

### HTML pattern

```html
<div class="tab-bar">
  <button class="tab active" onclick="switchTab('overview')">Overview</button>
  <button class="tab" onclick="switchTab('analysis')">Analysis</button>
  <button class="tab" onclick="switchTab('prd')">PRD</button>
  <button class="tab" onclick="switchTab('tasks')">Task List</button>
  <button class="tab" onclick="switchTab('config')">Config Schema</button>
</div>

<div class="tab-content active" id="tab-overview">...</div>
<div class="tab-content" id="tab-analysis">...</div>
<!-- etc -->
```

### CSS

```css
.tab-bar {
  display: flex; gap: 0; border-bottom: 2px solid var(--border);
  margin-bottom: 1.5rem; overflow-x: auto;
}
.tab {
  padding: .6rem 1.2rem; border: none; background: none;
  font-size: .9rem; font-weight: 600; cursor: pointer;
  color: var(--muted); border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: color .15s, border-color .15s;
  white-space: nowrap;
}
.tab:hover { color: var(--accent); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-content { display: none; }
.tab-content.active { display: block; }
```

### JS

```js
function switchTab(tabId) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
  document.querySelector(`[onclick="switchTab('${tabId}')"]`).classList.add('active');
  document.getElementById('tab-' + tabId).classList.add('active');
}
```

---

## Component: Summary Stat Grid

Use in the Overview tab for key numbers.

### HTML pattern

```html
<div class="stat-grid">
  <div class="stat-card"><div class="stat-number">7</div><div class="stat-label">Phases</div></div>
  <div class="stat-card"><div class="stat-number">68</div><div class="stat-label">Tasks</div></div>
  <div class="stat-card"><div class="stat-number">28</div><div class="stat-label">Acceptance Criteria</div></div>
</div>
```

### CSS

```css
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
.stat-card {
  background: var(--card); border: 1px solid var(--border); border-radius: 8px;
  padding: 1rem; text-align: center;
}
.stat-number { font-size: 2rem; font-weight: 700; color: var(--accent); }
.stat-label { font-size: .85rem; color: var(--muted); }
```

---

## Component: Workflow Flow

Horizontal step chain.

### HTML pattern

```html
<div class="flow">
  <div class="flow-step">Load Config</div>
  <div class="flow-arrow">→</div>
  <div class="flow-step">Validate</div>
  <div class="flow-arrow">→</div>
  <div class="flow-step">Resolve Sources</div>
  <div class="flow-arrow">→</div>
  <div class="flow-step">Compare</div>
  <div class="flow-arrow">→</div>
  <div class="flow-step">Write Output</div>
</div>
```

### CSS

```css
.flow { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin: 1rem 0; }
.flow-step {
  background: var(--accent-light); color: var(--accent); border-radius: 20px;
  padding: .4rem 1rem; font-size: .85rem; font-weight: 600;
}
.flow-arrow { color: var(--muted); font-size: 1.2rem; }
```

---

## Component: Colour-Coded Task Badge

### CSS

```css
.badge { display: inline-block; font-size: .7rem; padding: .15rem .45rem; border-radius: 3px; font-weight: 600; vertical-align: middle; margin-left: .4rem; }
.badge-feature  { background: var(--accent-light); color: var(--accent); }
.badge-bug      { background: var(--red-light);    color: var(--red); }
.badge-phase    { background: var(--purple-light);  color: var(--purple); }
.badge-verify   { background: var(--green-light);   color: var(--green); }
.badge-lint     { background: var(--amber-light);   color: #664d03; }
.badge-review   { background: var(--pink-light);    color: var(--pink); }
.badge-commit   { background: #e9ecef;              color: #495057; }
.badge-test     { background: var(--teal-light);    color: #0a6847; }
.badge-doc      { background: var(--orange-light);  color: #8a4106; }
.badge-ac       { background: var(--accent-light);  color: var(--accent); }
.badge-rec      { background: var(--green-light);   color: var(--green); }
.badge-current  { background: var(--amber-light);   color: #664d03; }
```

---

## Component: Phase Header (Task List)

### HTML pattern

```html
<div class="phase-header">
  <div class="phase-number">1</div>
  <div class="phase-info">
    <h3>Phase Name <span class="badge badge-phase">Phase 1</span></h3>
    <p class="phase-goal">One-line goal of this phase.</p>
    <p class="phase-acs">Acceptance criteria: <span class="badge badge-ac">AC-1.1</span> <span class="badge badge-ac">AC-1.2</span></p>
  </div>
</div>
```

### CSS

```css
.phase-header { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
.phase-number {
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--accent); color: #fff; display: flex;
  align-items: center; justify-content: center; font-weight: 700;
  font-size: 1.1rem; flex-shrink: 0;
}
.phase-info h3 { font-size: 1.1rem; margin-bottom: .2rem; }
.phase-goal { font-size: .9rem; color: var(--muted); }
.phase-acs { font-size: .85rem; margin-top: .3rem; }
```

---

## Component: AC Table

### HTML pattern

```html
<table class="ac-table">
  <thead><tr><th>AC ID</th><th>Criterion</th><th>Verified By</th></tr></thead>
  <tbody>
    <tr><td><span class="badge badge-ac">AC-1.1</span></td><td>Description of what must be true</td><td>Task 1.3, Task 1.5</td></tr>
  </tbody>
</table>
```

### CSS

```css
.ac-table { width: 100%; border-collapse: collapse; font-size: .85rem; margin: .75rem 0; }
.ac-table th, .ac-table td { text-align: left; padding: .5rem .6rem; border-bottom: 1px solid var(--border); }
.ac-table th { background: var(--bg); font-weight: 600; position: sticky; top: 0; }
.ac-table tr:hover { background: var(--accent-light); }
```

---

## Component: Generate + Copy Buttons

### HTML pattern

```html
<div class="btn-row">
  <button class="btn btn-primary" onclick="generateSummary()">Generate Summary</button>
  <button class="btn btn-secondary" onclick="copyToClipboard()">Copy to Clipboard</button>
  <button class="btn btn-save" onclick="saveHtml()">Save</button>
</div>

<div id="output-section">
  <h2>Generated Summary</h2>
  <pre id="output-json"></pre>
</div>

<div class="copied-toast" id="toast">Copied to clipboard</div>
```

### CSS (additional)

```css
.btn-save { background: var(--green); color: #fff; }
.btn-save:hover { background: #157347; }
```

### JS (Generate Summary template)

The generate function must be a **faithful, complete snapshot** of every user-editable element in
the HTML. If a user can see it, click it, or type into it, the JSON must capture it. A second
agent given only the JSON output should be able to reproduce every selection, override, note, and
config edit the user made. When adding new interactive elements to the HTML, always add a
corresponding collection step here.

```js
function generateSummary() {
  const result = {};

  // Collect radio selections
  document.querySelectorAll('.option-group').forEach(group => {
    const name = group.dataset.name;
    const checked = group.querySelector('input[type="radio"]:checked');
    if (checked) result[name] = checked.value;
  });

  // Collect textareas
  document.querySelectorAll('.text-input-group textarea').forEach(ta => {
    if (ta.value.trim()) result[ta.id] = ta.value.trim();
  });

  // Collect checkboxes
  document.querySelectorAll('.checkbox-card input[type="checkbox"]').forEach(cb => {
    const key = cb.dataset.rule || cb.dataset.feature;
    if (key) result[key] = cb.checked;
  });

  // Collect dropdowns
  document.querySelectorAll('select[data-decision]').forEach(sel => {
    result[sel.dataset.decision] = sel.value;
  });

  // Collect editable config blocks
  document.querySelectorAll('.config-editor').forEach(editor => {
    if (editor.value.trim()) result[editor.id] = editor.value.trim();
  });

  // Display
  const outputEl = document.getElementById('output-json');
  outputEl.textContent = JSON.stringify(result, null, 2);
  document.getElementById('output-section').classList.add('visible');
  outputEl.scrollIntoView({ behavior: 'smooth' });
}

function copyToClipboard() {
  const text = document.getElementById('output-json').textContent;
  navigator.clipboard.writeText(text).then(() => {
    const toast = document.getElementById('toast');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2000);
  });
}
```

---

## Component: Collapsible Detail

### HTML pattern

```html
<details>
  <summary>Click to expand detailed breakdown</summary>
  <div class="detail-content">
    <!-- Long content here -->
  </div>
</details>
```

### CSS

```css
details { margin: .75rem 0; }
details summary {
  cursor: pointer; font-weight: 600; font-size: .9rem;
  color: var(--accent); padding: .3rem 0;
}
details .detail-content { padding: .75rem 0 .25rem 1rem; }
```

---

## Component: Section Card

### HTML pattern

```html
<div class="section">
  <h2>Section Title</h2>
  <p class="description">One-line description of what this section covers.</p>
  <!-- content -->
</div>
```

### CSS

```css
.section {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;
}
.section h2 { font-size: 1.2rem; margin-bottom: .25rem; color: var(--accent); }
.section .description { color: var(--muted); font-size: .9rem; margin-bottom: 1rem; }
```

---

## Component: Striped Table

### CSS

```css
.data-table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.data-table th, .data-table td { text-align: left; padding: .5rem .6rem; border-bottom: 1px solid var(--border); }
.data-table th { background: var(--bg); font-weight: 600; position: sticky; top: 0; }
.data-table tbody tr:nth-child(even) { background: #f8f9fa; }
.data-table tbody tr:hover { background: var(--accent-light); }
```

---

## Component: Toast Notification

### CSS

```css
.copied-toast {
  position: fixed; bottom: 2rem; right: 2rem;
  background: var(--green); color: #fff;
  padding: .6rem 1.2rem; border-radius: 6px;
  font-weight: 600; opacity: 0; transition: opacity .3s;
  pointer-events: none; z-index: 999;
}
.copied-toast.show { opacity: 1; }
```

---

## Component: Self-Save

Every planning HTML must include a Save button that persists all current state (selections,
notes, config edits) directly into a downloadable copy of the HTML file. When the user reopens
the saved file, all their work is intact — no server required.

### How it works

`outerHTML` captures the original markup, not live form state. Before serializing, the
`prepareForSave()` function walks every interactive element and syncs the live `.value` /
`.checked` properties into DOM attributes so they survive the round-trip.

### JS

```js
function prepareForSave() {
  // Sync text inputs and textareas
  document.querySelectorAll('input[type="text"], textarea').forEach(el => {
    el.setAttribute('value', el.value);        // for <input>
    el.textContent = el.value;                  // for <textarea>
  });

  // Sync radio buttons and checkboxes
  document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(el => {
    if (el.checked) el.setAttribute('checked', 'checked');
    else el.removeAttribute('checked');
  });

  // Sync <select> dropdowns
  document.querySelectorAll('select').forEach(sel => {
    sel.querySelectorAll('option').forEach(opt => {
      if (opt.selected) opt.setAttribute('selected', 'selected');
      else opt.removeAttribute('selected');
    });
  });

  // Sync visual state classes on option cards and checkbox cards
  document.querySelectorAll('.option-card').forEach(card => {
    const radio = card.querySelector('input[type="radio"]');
    if (radio && radio.checked) card.classList.add('selected');
    else card.classList.remove('selected');
  });
  document.querySelectorAll('.checkbox-card').forEach(card => {
    const cb = card.querySelector('input[type="checkbox"]');
    card.classList.toggle('checked', cb && cb.checked);
  });
}

function saveHtml() {
  prepareForSave();
  const html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
  const blob = new Blob([html], { type: 'text/html' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  // Use the current page title as the filename, falling back to 'plan.html'
  const title = document.title.replace(/[^a-z0-9_\- ]/gi, '').replace(/\s+/g, '_');
  a.download = (title || 'plan') + '.html';
  a.click();
  URL.revokeObjectURL(a.href);
  // Show toast
  const toast = document.getElementById('toast');
  toast.textContent = 'Saved';
  toast.classList.add('show');
  setTimeout(() => { toast.classList.remove('show'); toast.textContent = 'Copied to clipboard'; }, 2000);
}
```

### Important notes

- `<textarea>` elements need `el.textContent = el.value` (not `setAttribute`) because their
  content is stored as child text, not an attribute.
- The function also syncs `.selected` / `.checked` CSS classes so the visual card states are
  preserved on reload.
- The download filename is derived from `document.title` for convenience.
- No external dependencies or server required.

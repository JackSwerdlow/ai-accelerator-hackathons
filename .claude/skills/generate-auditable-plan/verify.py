#!/usr/bin/env python3
# Grade a generate-interactive-plan HTML file against the 18 requirements in SKILL.md.
# Usage: python verify.py <path-to-file.html>
# Exit 0 if all pass, 1 otherwise, 2 on usage error.
# Pure standard library — no third-party packages, no JS runtime needed.
# Keep this verifier in sync with the template machinery and skill contract.
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # so ≥ / → / ✓ print on any locale
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2:
    sys.stderr.write("usage: python verify.py <file.html>\n")
    sys.exit(2)
target = sys.argv[1]
if not os.path.isfile(target):
    sys.stderr.write("error: file not found: %s\n" % target)
    sys.exit(2)
with open(target, "r", encoding="utf-8") as fh:
    src = fh.read()
with open(os.path.join(HERE, "template.html"), "r", encoding="utf-8") as fh:
    template = fh.read()

results = []  # list of (id, desc, pass_bool, detail)


def ok(rid, desc, passed, detail=""):
    results.append((rid, desc, bool(passed), detail))


# ---- helpers ----------------------------------------------------------
def count_literal(hay, needle):
    return hay.count(needle)


def bare_machinery(s):
    m = re.search(r"<script>\n([\s\S]*?)</script>", s)
    return m.group(1) if m else None


def block(s, bid):
    m = re.search(r'<script type="[^"]*" id="' + re.escape(bid) + r'">([\s\S]*?)</script>', s)
    return m.group(1) if m else None


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def jsonify(obj):
    # mirror JSON.stringify(obj, null, 2): 2-space indent, ": " / "," separators,
    # unicode kept literal (ensure_ascii=False) like JS.
    return json.dumps(obj, indent=2, ensure_ascii=False)


# ---- CSS variable resolver + WCAG contrast ----------------------------
NAMED = {"white": "#ffffff", "black": "#000000"}


def collect_vars(css):
    m = {}
    for x in re.finditer(r"--([\w-]+)\s*:\s*([^;]+);", css):
        m["--" + x.group(1)] = x.group(2).strip()  # last definition wins
    return m


def resolve_var(val, vars_, d=0):
    if d > 6 or val is None:
        return val
    val = str(val).strip()
    v = re.search(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\)", val)
    if v:
        repl = vars_.get(v.group(1))
        if repl is None:
            repl = v.group(2) or ""
        return resolve_var(repl, vars_, d + 1)
    return val


def decl_val(css, sel, prop):
    b = re.search(re.escape(sel) + r"\s*\{([^}]*)\}", css)
    if not b:
        return None
    p = re.search(r"(?:^|;|\s)" + re.escape(prop) + r"\s*:\s*([^;]+)", b.group(1))
    return p.group(1).strip() if p else None


def to_rgb(c):
    if not c:
        return None
    c = c.strip().lower()
    if c in NAMED:
        c = NAMED[c]
    h = re.match(r"^#([0-9a-f]{3}|[0-9a-f]{6})$", c, re.I)
    if not h:
        return None
    s = h.group(1)
    if len(s) == 3:
        s = "".join(ch + ch for ch in s)
    return [int(s[i : i + 2], 16) for i in (0, 2, 4)]


def lum(rgb):
    a = []
    for v in rgb:
        v /= 255
        a.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]


def contrast(c1, c2):
    a, b = to_rgb(c1), to_rgb(c2)
    if not a or not b:
        return None
    l1, l2 = lum(a), lum(b)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


# ---- reimplemented pure machinery (mirrors template.html) -------------
def parse(src_md):
    lines = src_md.replace("\r", "").split("\n")
    title, lede, steps, cur, saw_lede = "", "", [], None, False
    for raw in lines:
        t = raw.strip()
        if cur is None and re.match(r"^# ", t):
            title = t[2:]
            continue
        if re.match(r"^## ", t):
            ht = t[3:]
            cond = None
            assign = False
            if re.search(r"\{assign\}", ht):
                assign = True
                ht = re.sub(r"\s*\{assign\}\s*", " ", ht, count=1).strip()
            m = re.search(r"\s*@if=(\S+)\s*$", ht)
            if m:
                cond = m.group(1)
                ht = ht[: m.start()].strip()
            cur = {"title": ht, "condId": cond, "assign": assign, "lines": []}
            steps.append(cur)
            continue
        if cur is None:
            if t and not saw_lede:
                lede = t
                saw_lede = True
            continue
        cur["lines"].append(raw)
    return {"title": title, "lede": lede, "steps": steps}


def choice_defaults(doc):
    sel = {}
    for idx, st in enumerate(doc["steps"]):
        defv, first, has = None, None, False
        for line in st["lines"]:
            m = re.match(r"^- \(([ xX])\)\s*(?:\{([^}]+)\}\s*)?(.*)$", line.strip())
            if m:
                has = True
                oid = m.group(2) or None
                if first is None:
                    first = oid
                if re.search(r"x", m.group(1), re.I):
                    defv = oid
        if has:
            sel[idx] = defv if defv is not None else first
    return sel


def active_ids(sel):
    s = {}
    for k in sel:
        if sel[k]:
            s[sel[k]] = True
    return s


def visible_idx(doc, sel):
    a = active_ids(sel)
    s = {}
    for i, st in enumerate(doc["steps"]):
        if not st["condId"] or a.get(st["condId"]):
            s[i] = True
    return s


def note_id(step_idx, idx):
    return "s" + str(step_idx) + "n" + str(idx)


def config_id(step_idx, idx):
    return "s" + str(step_idx) + "g" + str(idx)


def read_fence(lines, start):
    open_match = re.match(r"^```([^\s`]+)?\s*(.*)$", lines[start].strip())
    if not open_match:
        return None
    kind = (open_match.group(1) or "").lower()
    meta = open_match.group(2) or ""
    body = []
    end = start + 1
    while end < len(lines) and lines[end].strip() != "```":
        body.append(lines[end])
        end += 1
    return {
        "kind": kind,
        "meta": meta,
        "body": "\n".join(body),
        "closed": end < len(lines),
        "closeLine": lines[end] if end < len(lines) else "```",
        "next": end + 1 if end < len(lines) else end,
    }


def note_meta(meta):
    return {"label": meta.strip() or "Notes"}


def config_meta(meta):
    parts = meta.strip().split() if meta.strip() else []
    format_ = parts[0] if parts else ""
    label = " ".join(parts[1:]) if len(parts) > 1 else "Editable config"
    return {"format": format_, "label": label}


def prune_hidden_checks(cks, vis):
    visible_cks = dict(cks)
    for checkbox_id in list(visible_cks):
        match = re.match(r"^s(\d+)c", checkbox_id)
        if match and not vis.get(int(match.group(1))):
            del visible_cks[checkbox_id]
    return visible_cks


def resolve_name(names, member_id):
    member_name = names.get(member_id)
    return member_name.strip() if (member_name and member_name.strip()) else member_id


def default_owner(ids, task_idx):
    return ids[task_idx % len(ids)] if ids else None


def parse_choice_line(raw_line):
    match = re.match(r"^- \(([ xX])\)\s*(?:\{([^}]+)\}\s*)?(.*)$", raw_line)
    if not match:
        return None
    return {"id": match.group(2) or None, "label": match.group(3)}


def build_task_entry(step, step_idx, raw_line, checkbox_idx, task_idx, cks, has_team, ids, names, owners):
    match = re.match(r"^- \[([ xX])\]\s+(.*)$", raw_line)
    if not match:
        return None
    checkbox_id = "s" + str(step_idx) + "c" + str(checkbox_idx)
    task = {"task": match.group(2), "done": bool(cks.get(checkbox_id))}
    if step["assign"] and has_team:
        owner_id = owners.get(task_idx) or default_owner(ids, task_idx)
        task["owner"] = resolve_name(names, owner_id)
    return task


def handle_plan_fence(lines, line_idx, step_idx, note_idx, config_idx, notes, configs, note_entries, config_entries):
    fence = read_fence(lines, line_idx)
    if not fence:
        return None
    if fence["kind"] == "note":
        key = note_id(step_idx, note_idx)
        meta = note_meta(fence["meta"])
        note_entries.append({"label": meta["label"], "text": notes.get(key, fence["body"])})
        return {"next": fence["next"], "note_idx": note_idx + 1, "config_idx": config_idx}
    if fence["kind"] == "config":
        key = config_id(step_idx, config_idx)
        meta = config_meta(fence["meta"])
        config_entries.append(
            {"label": meta["label"], "format": meta["format"], "content": configs.get(key, fence["body"])}
        )
        return {"next": fence["next"], "note_idx": note_idx, "config_idx": config_idx + 1}
    return None


def finalize_step_entry(entry, tasks, note_entries, config_entries):
    if tasks:
        entry["tasks"] = tasks
    if note_entries:
        entry["notes"] = note_entries
    if config_entries:
        entry["configs"] = config_entries
    return entry if len(entry) > 1 else None


def build_step_entry(step, step_idx, sel, cks, notes, configs, has_team, ids, names, owners):
    entry = {"step": step["title"]}
    checkbox_idx = 0
    task_idx = 0
    note_idx = 0
    config_idx = 0
    tasks = []
    note_entries = []
    config_entries = []
    line_idx = 0
    while line_idx < len(step["lines"]):
        raw = step["lines"][line_idx]
        stripped = raw.strip()
        if re.match(r"^```", stripped):
            fence_result = handle_plan_fence(
                step["lines"], line_idx, step_idx, note_idx, config_idx, notes, configs, note_entries, config_entries
            )
            if fence_result:
                note_idx = fence_result["note_idx"]
                config_idx = fence_result["config_idx"]
                line_idx = fence_result["next"]
                continue

        choice = parse_choice_line(stripped)
        if choice is not None:
            if sel.get(step_idx) == choice["id"]:
                entry["choice"] = choice
            line_idx += 1
            continue

        task = build_task_entry(step, step_idx, stripped, checkbox_idx, task_idx, cks, has_team, ids, names, owners)
        if task is not None:
            tasks.append(task)
            checkbox_idx += 1
            if step["assign"] and has_team:
                task_idx += 1
        line_idx += 1

    return finalize_step_entry(entry, tasks, note_entries, config_entries)


def build_plan(doc, sel, cks, notes, configs, has_team, ids, names, owners):
    vis = visible_idx(doc, sel)
    visible_cks = prune_hidden_checks(cks, vis)
    steps = []
    for step_idx, step in enumerate(doc["steps"]):
        if not vis.get(step_idx):
            continue
        entry = build_step_entry(step, step_idx, sel, visible_cks, notes, configs, has_team, ids, names, owners)
        if entry is not None:
            steps.append(entry)

    out = {}
    if has_team:
        out["team"] = [{"id": member_id, "name": resolve_name(names, member_id)} for member_id in ids]
    out["steps"] = steps
    return jsonify(out)


def reset_choice_state(state):
    state["in_choice"] = False
    state["opt_idx"] = 0


def advance_step_state(state):
    state["step_idx"] += 1
    state["ck"] = 0
    state["note_n"] = 0
    state["config_n"] = 0
    reset_choice_state(state)


def render_fence_lines(value, raw_line, fence):
    rendered = [raw_line]
    rendered.extend(str(value if value is not None else "").replace("\r", "").split("\n"))
    if fence["closed"]:
        rendered.append(fence["closeLine"])
    return rendered


def serialize_fence_block(lines, line_idx, raw_line, state, vis, notes, configs):
    if state["step_idx"] < 0 or not re.match(r"^```", raw_line.strip()):
        return None

    fence = read_fence(lines, line_idx)
    if not fence:
        return None

    if fence["kind"] == "note":
        key = note_id(state["step_idx"], state["note_n"])
        state["note_n"] += 1
        value = fence["body"] if not vis.get(state["step_idx"]) else notes.get(key, fence["body"])
        reset_choice_state(state)
        return render_fence_lines(value, raw_line, fence), fence["next"]

    if fence["kind"] == "config":
        key = config_id(state["step_idx"], state["config_n"])
        state["config_n"] += 1
        value = fence["body"] if not vis.get(state["step_idx"]) else configs.get(key, fence["body"])
        reset_choice_state(state)
        return render_fence_lines(value, raw_line, fence), fence["next"]

    return None


def serialize_checkbox_line(raw_line, state, vis, cks):
    match = re.match(r"^(\s*- )\[([ xX])\](\s+.*)$", raw_line)
    if not match:
        return None

    checkbox_id = "s" + str(state["step_idx"]) + "c" + str(state["ck"])
    state["ck"] += 1
    reset_choice_state(state)

    if not vis.get(state["step_idx"]):
        checked = False
    elif checkbox_id in cks:
        checked = cks[checkbox_id]
    else:
        checked = bool(re.search(r"x", match.group(2), re.I))

    return match.group(1) + "[" + ("x" if checked else " ") + "]" + match.group(3)


def serialize_choice_line(raw_line, state, sel):
    match = re.match(r"^(\s*- )\(([ xX])\)(\s*(?:\{([^}]+)\}\s*)?.*)$", raw_line)
    if not match:
        return None

    if not state["in_choice"]:
        state["in_choice"] = True
        state["opt_idx"] = 0

    option_id = match.group(4) or ("opt" + str(state["opt_idx"]))
    state["opt_idx"] += 1
    checked = sel.get(state["step_idx"]) == option_id
    return match.group(1) + "(" + ("x" if checked else " ") + ")" + match.group(3)


def serialize_markdown(src_md, doc, sel, cks, notes, configs):
    vis = visible_idx(doc, sel)
    state = {"step_idx": -1, "ck": 0, "opt_idx": 0, "note_n": 0, "config_n": 0, "in_choice": False}
    out_lines = []
    lines = src_md.replace("\r", "").split("\n")
    line_idx = 0
    while line_idx < len(lines):
        raw = lines[line_idx]
        trimmed = raw.strip()
        if re.match(r"^## ", trimmed):
            advance_step_state(state)
            out_lines.append(raw)
            line_idx += 1
            continue

        fence_result = serialize_fence_block(lines, line_idx, raw, state, vis, notes, configs)
        if fence_result is not None:
            rendered_lines, next_idx = fence_result
            out_lines.extend(rendered_lines)
            line_idx = next_idx
            continue

        if state["step_idx"] < 0:
            out_lines.append(raw)
            line_idx += 1
            continue

        checkbox_line = serialize_checkbox_line(raw, state, vis, cks)
        if checkbox_line is not None:
            out_lines.append(checkbox_line)
            line_idx += 1
            continue

        choice_line = serialize_choice_line(raw, state, sel)
        if choice_line is not None:
            out_lines.append(choice_line)
            line_idx += 1
            continue

        reset_choice_state(state)
        out_lines.append(raw)
        line_idx += 1
    return "\n".join(out_lines)


# ---- gather pieces ----------------------------------------------------
plan_md = block(src, "plan")
config_raw = block(src, "config")
state_raw = block(src, "state")
machinery = bare_machinery(src)
tpl_machinery = bare_machinery(template)

PLAN_TAG = '<script type="text/markdown" id="plan">'
STATE_TAG = '<script type="application/json" id="state">'
CONFIG_TAG = '<script type="application/json" id="config">'

# ---- R1 single blocks -------------------------------------------------
ok(
    "R1",
    "Exactly one plan/state/config block",
    count_literal(src, PLAN_TAG) == 1 and count_literal(src, STATE_TAG) == 1 and count_literal(src, CONFIG_TAG) == 1,
    "plan=%d state=%d config=%d"
    % (count_literal(src, PLAN_TAG), count_literal(src, STATE_TAG), count_literal(src, CONFIG_TAG)),
)

# ---- parse plan + config ----------------------------------------------
doc = None
cfg = None
cfg_err = ""
try:
    doc = parse(plan_md or "")
except Exception as e:
    cfg_err += "plan parse: %s; " % e
try:
    cfg = json.loads(config_raw or "{}")
except Exception as e:
    cfg_err += "config JSON: %s; " % e

has_team = bool(
    cfg
    and isinstance(cfg, dict)
    and cfg.get("hasTeam")
    and isinstance(cfg.get("members"), list)
    and len(cfg["members"])
)
members = cfg["members"] if has_team else []
ids = ["m" + str(i + 1) for i in range(len(members))]

# ---- R2 markdown-driven -----------------------------------------------
has_title = bool(doc and doc["title"])
has_steps = bool(doc and len(doc["steps"]))
hand_written = (
    re.search(r'<fieldset|<input[^>]+type="radio"|<input[^>]+type="checkbox"', plan_md or "", re.I) is not None
)
ok(
    "R2",
    "Markdown-driven (title + steps, no hand-written widgets in plan)",
    has_title and has_steps and not hand_written,
    "title=%s steps=%d handWritten=%s"
    % (str(has_title).lower(), len(doc["steps"]) if doc else 0, str(hand_written).lower()),
)

# ---- R3 self-contained ------------------------------------------------
ext_script = re.search(r"<script[^>]*\bsrc\s*=", src, re.I) is not None
ext_css = re.search(r"<link[^>]+stylesheet", src, re.I) is not None
ok(
    "R3",
    "Self-contained (no external script/stylesheet)",
    (not ext_script) and (not ext_css),
    "extScript=%s extCss=%s" % (str(ext_script).lower(), str(ext_css).lower()),
)

# ---- machinery unchanged ----------------------------------------------
machinery_matches = bool(machinery and tpl_machinery and norm(machinery) == norm(tpl_machinery))
ok(
    "MACH",
    "Machinery <script> is the unmodified template machinery",
    machinery_matches,
    "" if machinery_matches else "the big machinery block differs from template.html",
)

# ---- R4 team config ---------------------------------------------------
cfg_valid = bool(
    cfg is not None
    and isinstance(cfg, dict)
    and isinstance(cfg.get("hasTeam"), bool)
    and isinstance(cfg.get("members"), list)
)
team_consistent = bool(cfg_valid and (len(cfg["members"]) > 0 if cfg["hasTeam"] else len(cfg["members"]) == 0))
ok(
    "R4",
    "Team config present & consistent (#config)",
    cfg_valid and team_consistent,
    cfg_err
    or (
        "hasTeam=%s members=%s"
        % (
            str(cfg.get("hasTeam")).lower() if cfg else "None",
            json.dumps(cfg.get("members"), ensure_ascii=False, separators=(",", ":")) if cfg else "None",
        )
    ),
)

# ---- R5 owner dropdowns on {assign} when team -------------------------
assign_steps = [s for s in doc["steps"] if s["assign"]] if doc else []
owner_wired = ("function ownerSelect" in src) and ("data-owner=" in src) and ("assign && HAS_TEAM" in src)
ok(
    "R5",
    "Owner dropdowns wired for {assign} steps (when team)",
    machinery_matches and ((not has_team) or (not assign_steps) or owner_wired),
    "assignSteps=%d hasTeam=%s ownerWired=%s" % (len(assign_steps), str(has_team).lower(), str(owner_wired).lower()),
)

# ---- R6 JSON export ---------------------------------------------------
ok("R6", "JSON export present", ('id="jsonOut"' in src) and ('id="genBtn"' in src))

# ---- R7 combined gen+copy button --------------------------------------
gen_combined = (re.search(r'id="genBtn"[^>]*>[\s\S]*?Generate[\s\S]*?copy', src, re.I) is not None) or (
    "Generate &amp; copy JSON" in src
)
ok(
    "R7",
    'Single combined "Generate & copy JSON" button',
    gen_combined and ('id="copyBtn"' not in src),
    "combined=%s hasCopyBtn=%s" % (str(gen_combined).lower(), str('id="copyBtn"' in src).lower()),
)

# ---- R8 no download button --------------------------------------------
ok("R8", 'No "Download JSON" button', ("download json" not in src.lower()) and ('id="dlBtn"' not in src))

# ---- R9 styling + contrast --------------------------------------------
has_focus = re.search(r":focus\s*\{[^}]*outline", src, re.I) is not None
has_viewport = 'name="viewport"' in src
has_media = "@media" in src
vars_ = collect_vars(src)
bg = resolve_var(decl_val(src, "body", "background") or decl_val(src, "body", "background-color"), vars_)
c_body = contrast(resolve_var(decl_val(src, "body", "color"), vars_), bg)
c_btn = contrast(
    resolve_var(decl_val(src, ".btn", "color"), vars_),
    resolve_var(decl_val(src, ".btn", "background") or decl_val(src, ".btn", "background-color"), vars_),
)
c_sel = contrast(resolve_var(decl_val(src, "body", "color"), vars_), resolve_var(vars_.get("--surface-sel"), vars_))
c_muted = contrast(resolve_var(vars_.get("--muted"), vars_), bg)
c_hdr = contrast(
    resolve_var(decl_val(src, ".site-header", "color"), vars_),
    resolve_var(
        decl_val(src, ".site-header", "background") or decl_val(src, ".site-header", "background-color"), vars_
    ),
)


def meets(c):
    return True if c is None else c >= 4.5


def fx(c):
    return ("%.2f" % c) if c is not None else "?"


contrast_ok = meets(c_body) and meets(c_btn) and meets(c_sel) and meets(c_muted) and meets(c_hdr)
ok(
    "R9",
    "Styling: focus + viewport + responsive + contrast ≥4.5:1 (body, button, selected, muted, header)",
    has_focus and has_viewport and has_media and contrast_ok,
    "focus=%s viewport=%s media=%s body=%s btn=%s selected=%s muted=%s header=%s"
    % (
        str(has_focus).lower(),
        str(has_viewport).lower(),
        str(has_media).lower(),
        fx(c_body),
        fx(c_btn),
        fx(c_sel),
        fx(c_muted),
        fx(c_hdr),
    ),
)

# ---- R10 write-back ---------------------------------------------------
writes_md = re.search(r'text/markdown" id="plan"[\s\S]*?serializeMarkdown', src) is not None
writes_state = re.search(r'application/json" id="state"[\s\S]*?rawState\(\)', src) is not None
ok(
    "R10",
    "Save writes ticks/choices→markdown and names/owners→#state",
    writes_md and writes_state,
    "md=%s state=%s" % (str(writes_md).lower(), str(writes_state).lower()),
)

# ---- R11 no storage ---------------------------------------------------
uses_storage = bool(machinery and re.search(r"(localStorage|sessionStorage)", machinery))
ok("R11", "No localStorage/sessionStorage for state (file is source of truth)", not uses_storage)

# ---- R12/R13 ----------------------------------------------------------
session_handle = "var fileHandle = null;" in src
positioning_only = (
    ("loadStartHandle()" in src) and ("opts.startIn = sh" in src) and ("saveStartHandle(fileHandle)" in src)
)
ok("R12", "Session-only save target (fresh handle each session)", session_handle)
ok("R13", "Remembered folder positions picker only (IndexedDB)", positioning_only and ("indexedDB.open" in src))

# ---- R14 save + fallback ----------------------------------------------
ok(
    "R14",
    "Save via File System Access API with fallback message",
    ("showOpenFilePicker" in src)
    and ("createWritable" in src)
    and (re.search(r"can['’]t write files", src) is not None),
)

# ---- R15 conditional notes --------------------------------------------
cond_steps = [s for s in doc["steps"] if s["condId"]] if doc else []
cond_noted = True
cond_detail = []
for s in cond_steps:
    prose = [line for line in s["lines"] if line.strip() and not re.match(r"^- ", line.strip())]
    explains = any(
        re.search(r"\b(only|appears|shown|show|chosen|choose|selected|select|if |when |@if)\b", line, re.I)
        for line in prose
    )
    if not prose:
        cond_noted = False
        cond_detail.append("%s:NO-NOTE" % s["condId"])
    elif not explains:
        cond_noted = False
        cond_detail.append("%s:NOTE-NOT-EXPLANATORY" % s["condId"])
    else:
        cond_detail.append("%s:noted" % s["condId"])
ok(
    "R15",
    "Each @if= conditional carries a note that explains the condition",
    True if len(cond_steps) == 0 else cond_noted,
    ", ".join(cond_detail) if cond_steps else "no conditional steps",
)

# ---- R16 no hidden-step leakage ---------------------------------------
r16 = True
r16_detail = "no conditional to test"
if doc and cond_steps:
    cond = cond_steps[0]
    choice_step_idx = None
    alt_opt = None
    for idx, st in enumerate(doc["steps"]):
        offers = False
        other = None
        for line in st["lines"]:
            m = re.match(r"^- \([ xX]\)\s*(?:\{([^}]+)\}\s*)?", line.strip())
            if m:
                oid = m.group(1) or None
                if oid == cond["condId"]:
                    offers = True
                elif other is None:
                    other = oid
        if offers and other:
            choice_step_idx = idx
            alt_opt = other
    if choice_step_idx is not None:
        sel = choice_defaults(doc)
        sel[choice_step_idx] = alt_opt  # turn the branch OFF
        cond_idx = doc["steps"].index(cond)
        cks = {"s" + str(cond_idx) + "c0": True}  # tick a box on the now-hidden step
        plan_json = build_plan(doc, sel, dict(cks), {}, {}, has_team, ids, {}, {})
        leaked_json = jsonify(cond["title"]) in plan_json
        md = serialize_markdown(plan_md, doc, sel, dict(cks), {}, {})
        in_hidden = False
        hidden_box_checked = False
        seen = -1
        for line in md.split("\n"):
            if re.match(r"^## ", line.strip()):
                seen += 1
                in_hidden = seen == cond_idx
            elif in_hidden and re.match(r"^\s*- \[x\]", line, re.I):
                hidden_box_checked = True
        r16 = (not leaked_json) and (not hidden_box_checked)
        r16_detail = "leakJson=%s hiddenBoxChecked=%s" % (str(leaked_json).lower(), str(hidden_box_checked).lower())
    else:
        r16_detail = "conditional present but no toggling choice found"
ok("R16", "No hidden-step leakage into JSON or saved markdown", r16, r16_detail)

# ---- R17 complete JSON ------------------------------------------------
r17 = True
r17_detail = ""
if doc:
    sel = choice_defaults(doc)
    plan_obj = json.loads(build_plan(doc, sel, {}, {}, {}, has_team, ids, {}, {}))
    vis = visible_idx(doc, sel)
    expected = 0
    for idx, st in enumerate(doc["steps"]):
        if not vis.get(idx):
            continue
        has_choice = False
        has_task = False
        has_note = False
        has_config = False
        line_idx = 0
        while line_idx < len(st["lines"]):
            t = st["lines"][line_idx].strip()
            if re.match(r"^```", t):
                fence = read_fence(st["lines"], line_idx)
                if fence and fence["kind"] == "note":
                    has_note = True
                    line_idx = fence["next"]
                    continue
                if fence and fence["kind"] == "config":
                    has_config = True
                    line_idx = fence["next"]
                    continue
            if re.match(r"^- \([ xX]\)", t):
                has_choice = True
            if re.match(r"^- \[[ xX]\]", t):
                has_task = True
            line_idx += 1
        if has_choice or has_task or has_note or has_config:
            expected += 1
    got = len(plan_obj["steps"])
    all_fields = True
    for s in plan_obj["steps"]:
        if "choice" in s and ("id" not in s["choice"] or "label" not in s["choice"]):
            all_fields = False
        for t in s.get("tasks", []):
            if "task" not in t or "done" not in t:
                all_fields = False
        for n in s.get("notes", []):
            if "label" not in n or "text" not in n:
                all_fields = False
        for c in s.get("configs", []):
            if "label" not in c or "format" not in c or "content" not in c:
                all_fields = False
    r17 = (got == expected) and all_fields and ((not has_team) or isinstance(plan_obj.get("team"), list))
    r17_detail = "steps got=%d expected=%d allFields=%s team=%s" % (
        got,
        expected,
        str(all_fields).lower(),
        str("team" in plan_obj).lower(),
    )
ok("R17", "Complete JSON (every visible choice + checkbox/note/config, with owners on team)", r17, r17_detail)

# ---- R18 title-first deterministic JSON -------------------------------
r18 = True
r18_detail = ""
if doc:
    sel = choice_defaults(doc)
    a = build_plan(doc, sel, {}, {}, {}, has_team, ids, {}, {})
    b = build_plan(doc, sel, {}, {}, {}, has_team, ids, {}, {})
    deterministic = a == b
    step_first = (re.search(r'"step":[\s\S]*?("choice"|"tasks")', a) is not None) or (
        re.search(r'"choice"|"tasks"', a) is None
    )
    task_first = True
    for s in json.loads(a)["steps"]:
        for t in s.get("tasks", []):
            keys = list(t.keys())
            ti = keys.index("task") if "task" in keys else -1
            if not (
                ti == 0
                and ("done" in keys and keys.index("done") > ti)
                and (("owner" not in t) or keys.index("owner") > keys.index("done"))
            ):
                task_first = False
    r18 = deterministic and step_first and task_first
    r18_detail = "deterministic=%s stepFirst=%s taskFirst=%s" % (
        str(deterministic).lower(),
        str(step_first).lower(),
        str(task_first).lower(),
    )
ok("R18", "Title-first, deterministic JSON ordering", r18, r18_detail)

# ---- report -----------------------------------------------------------
passed = 0
failed = 0
print("\n=== generate-interactive-plan verify: " + os.path.basename(target) + " ===\n")
for rid, desc, p, detail in results:
    print("%s  %s %s%s" % ("PASS" if p else "FAIL", rid.ljust(5), desc, ("   [" + detail + "]") if detail else ""))
    if p:
        passed += 1
    else:
        failed += 1
print("\n%d passed, %d failed (of %d)\n" % (passed, failed, len(results)))
sys.exit(1 if failed else 0)

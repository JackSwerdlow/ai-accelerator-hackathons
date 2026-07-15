#!/usr/bin/env python3
"""
Claude Code Stop hook — auto-logs per-turn spend to ai-spend-log-{AGENT_NAME}.csv.

Do not run directly. Installed via install_hook.sh, which adds it to
~/.claude/settings.json so Claude Code calls it automatically at the end
of every response.
"""
import csv, json, os, socket, sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve the solution/ directory from this file's location so imports and
# the CSV path work regardless of the working directory the hook runs from.
_SPEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SPEND_DIR.parent))

try:
    from spend.pricing import cost_gbp
except ImportError:
    # Fallback if the package isn't on sys.path — avoids silent failures
    def cost_gbp(model, inp, out):
        rates = {
            "claude-sonnet-4-6": (3.00, 15.00),
            "claude-opus-4-8":   (5.00, 25.00),
            "claude-haiku-4-5":  (1.00,  5.00),
        }
        r = rates.get(model, (3.00, 15.00))
        return round((inp * r[0] + out * r[1]) / 1_000_000 * 0.79, 4)

AGENT_NAME = os.environ.get("AGENT_NAME", socket.gethostname())
LOG_PATH = _SPEND_DIR / f"ai-spend-log-{AGENT_NAME}.csv"
STATE_FILE = Path.home() / ".claude" / "spend_tracking_state.json"

_HEADERS = [
    "Timestamp", "AgentName", "CallType", "Purpose",
    "Model", "UploadTokens", "DownloadTokens", "CostGBP",
]


def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state):
    STATE_FILE.write_text(json.dumps(state))


def _read_new_entries(transcript_path, from_line):
    entries = []
    total = from_line
    with open(transcript_path) as f:
        for i, raw in enumerate(f):
            total = i + 1
            if i < from_line or not raw.strip():
                continue
            try:
                entries.append(json.loads(raw))
            except json.JSONDecodeError:
                pass
    return entries, total


def _parse_usage(entries):
    """Sum input/output tokens from new assistant messages, deduplicating by message ID."""
    inp = out = 0
    model = "claude-sonnet-4-6"
    seen = set()
    for entry in entries:
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message", {})
        msg_id = msg.get("id", "")
        if msg_id and msg_id in seen:
            continue  # same turn, multiple tool-use steps — count once
        seen.add(msg_id)
        usage = msg.get("usage", {})
        inp += usage.get("input_tokens", 0)
        out += usage.get("output_tokens", 0)
        if msg.get("model"):
            model = msg["model"]
    return inp, out, model


# Keyword map used to auto-detect purpose category from last assistant message.
# Ordered: first match wins. Keep higher-specificity patterns earlier.
# Categories mirror the table in wk09/CLAUDE.md — keep in sync if you add one.
_CATEGORY_KEYWORDS = [
    ("Debugging",     ["error", "exception", "traceback", "bug", "fix", "broken", "fail", "crash",
                       "not working", "incorrect", "wrong output"]),
    ("Testing",       ["test", "pytest", "unittest", "assertion", "coverage", "eval", "evaluate",
                       "quality check", "regression"]),
    ("Refactoring",   ["refactor", "clean up", "reorganis", "reorganiz", "restructur", "simplif",
                       "rename", "extract", "move", "deduplic"]),
    ("Planning",      ["plan", "design", "architecture", "spec", "approach", "brainstorm",
                       "strategy", "breakdown", "roadmap", "decide"]),
    ("Research",      ["research", "investigat", "look up", "documentation", "how to", "what is",
                       "compare", "option", "alternative", "library", "framework"]),
    ("Documentation", ["readme", "docstring", "comment", "document", "ai_log", "claude.md",
                       "write up", "notes"]),
    ("Configuration", ["config", "setup", "install", "dependency", "requirement", "environment",
                       "settings", "docker", "ci", "workflow", "git"]),
    ("Code review",   ["review", "explain", "understand", "walk me through", "what does",
                       "how does", "read through", "audit"]),
    ("Data analysis", ["analys", "result", "batch", "csv", "dataset", "summarise", "summarize",
                       "insight", "theme", "sentiment"]),
    ("Implementation",["implement", "add", "create", "write", "build", "generat", "new function",
                       "new class", "new file", "feature"]),
]


def _infer_purpose(last_message: str) -> str:
    """Return the best-matching category from last_message, or 'Other'."""
    text = last_message.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(kw in text for kw in keywords):
            return category
    return "Other"


def _write_row(purpose, model, inp, out):
    write_header = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(_HEADERS)
        w.writerow([
            datetime.now(timezone.utc).isoformat(),
            AGENT_NAME, "ClaudeCode", purpose,
            model, inp, out, cost_gbp(model, inp, out),
        ])


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    session_id = data.get("session_id", "unknown")
    transcript_path = data.get("transcript_path", "")
    last_message = data.get("last_assistant_message", "")
    cwd = data.get("cwd", "")

    if not transcript_path or not Path(transcript_path).exists():
        return

    # Guard: only log when Claude Code is running inside this repo.
    # Prevents accidental logging if the hook ever ends up in global settings.
    # (Checks the repo root, not _SPEND_DIR, so it fires whether Claude
    # Code was launched from the repo root, wk09/, wk09/solution/, or
    # wk09/solution/spend/.)
    cwd_path = Path(cwd).resolve() if cwd else Path.cwd()
    repo_root = _SPEND_DIR.parent.parent.parent
    if cwd_path != repo_root and repo_root not in cwd_path.parents:
        return

    state = _load_state()
    from_line = state.get(session_id, 0)

    new_entries, total_lines = _read_new_entries(transcript_path, from_line)
    inp, out, model = _parse_usage(new_entries)

    if inp > 0 or out > 0:
        purpose = _infer_purpose(last_message)
        _write_row(purpose, model, inp, out)

    state[session_id] = total_lines
    _save_state(state)


if __name__ == "__main__":
    main()

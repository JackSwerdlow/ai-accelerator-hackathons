#!/usr/bin/env python3
"""
Claude Code Stop hook — auto-logs per-turn spend to ai-spend-log-{AGENT_NAME}.csv.

Do not run directly. Installed via install_hook.sh, which adds it to
~/.claude/settings.json so Claude Code calls it automatically at the end
of every response.
"""
import csv, fcntl, json, os, socket, subprocess, sys
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
    def cost_gbp(model, inp, out, cache_creation_tokens=0, cache_read_tokens=0):
        rates = {
            "claude-sonnet-4-6": (3.00, 15.00),
            "claude-sonnet-5":   (2.00, 10.00),
            "claude-opus-4-8":   (5.00, 25.00),
            "claude-haiku-4-5":  (1.00,  5.00),
        }
        r = rates.get(model, (3.00, 15.00))
        usd = (inp * r[0] + cache_creation_tokens * r[0] * 1.25
               + cache_read_tokens * r[0] * 0.1 + out * r[1]) / 1_000_000
        return round(usd * 0.79, 4)

AGENT_NAME = os.environ.get("AGENT_NAME", socket.gethostname())
LOG_PATH = _SPEND_DIR / f"ai-spend-log-{AGENT_NAME}.csv"
STATE_FILE = Path.home() / ".claude" / "spend_tracking_state.json"
LOCK_FILE = Path.home() / ".claude" / "spend_tracking_state.lock"

# How many recently-billed message ids to remember per session. Duplicates
# in practice cluster tightly (empirically, no message id has been observed
# more than ~20 transcript lines from its first occurrence), so this is a
# generous safety margin, not a tight fit - it bounds state file growth for
# very long sessions without needing to remember every id ever billed.
MAX_BILLED_IDS_PER_SESSION = 2000

_HEADERS = [
    "Timestamp", "AgentName", "CallType", "Purpose", "Description",
    "Model", "UploadTokens", "DownloadTokens", "CostGBP",
]


class _StateLock:
    """Exclusive file lock covering the whole load-modify-save cycle.

    Multiple Claude Code sessions/worktrees in this environment share one
    ~/.claude/spend_tracking_state.json. Without this, two hook invocations
    (even for different sessions) can race: both read the same on-disk
    state, both compute an update, and whichever writes last silently
    discards the other's update — corrupting the OTHER session's line
    cursor, not just this one's. This previously caused a session's
    from_line to regress, which reprocessed a huge already-billed swath of
    the transcript and inflated a logged row to tens of millions of tokens
    (see AI_LOG.md for the incident and diagnosis).
    """

    def __enter__(self):
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._fd = open(LOCK_FILE, "w")
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        self._fd.close()


def _load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state):
    # Write-then-rename so a crash or a concurrent reader mid-write can
    # never observe a truncated/corrupt state file.
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(STATE_FILE)


def _session_state(state, session_id):
    """Return (from_line, billed_ids_set) for a session, migrating the old
    {session_id: int} format (line cursor only, no billed-id tracking)
    transparently."""
    raw = state.get(session_id)
    if isinstance(raw, dict):
        return raw.get("from_line", 0), set(raw.get("billed_ids", []))
    if isinstance(raw, int):
        return raw, set()
    return 0, set()


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


def _parse_usage(entries, already_billed):
    """Sum token usage from new assistant messages, deduplicating by
    message ID against BOTH this batch and the persisted `already_billed`
    set from prior invocations.

    The persisted set is the safety net: `from_line`-based slicing is the
    normal-case optimisation (avoids re-reading the whole transcript every
    time), but if it's ever stale or wrong - a lost state update, an
    off-by-one - re-including already-billed lines must not re-bill them.
    Line-cursor correctness alone was exactly the assumption that broke
    (see AI_LOG.md); this makes correctness independent of it.

    Includes cache_creation_input_tokens/cache_read_input_tokens - in a long
    Claude Code session almost all "input" is served from the prompt cache
    (each turn resends the growing conversation history), so input_tokens
    alone captures only a tiny fraction of true input volume/cost. Omitting
    the cache fields was a real bug here, not just an approximation - it
    undercounted logged spend by roughly an order of magnitude.
    """
    inp = out = cache_creation = cache_read = 0
    model = "claude-sonnet-4-6"
    newly_billed = set()
    for entry in entries:
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message", {})
        msg_id = msg.get("id", "")
        if msg_id and (msg_id in already_billed or msg_id in newly_billed):
            continue  # same turn, multiple tool-use steps, or already billed previously
        if msg_id:
            newly_billed.add(msg_id)
        usage = msg.get("usage", {})
        inp += usage.get("input_tokens", 0)
        out += usage.get("output_tokens", 0)
        cache_creation += usage.get("cache_creation_input_tokens", 0)
        cache_read += usage.get("cache_read_input_tokens", 0)
        if msg.get("model"):
            model = msg["model"]
    return inp, out, cache_creation, cache_read, model, newly_billed


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


def _extract_description(last_message: str, max_len: int = 120) -> str:
    """Return the first meaningful line of last_assistant_message as a one-liner."""
    for line in last_message.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:max_len]
    return ""


def _write_row(purpose, description, model, inp, out, cache_creation, cache_read):
    cost = cost_gbp(model, inp, out, cache_creation_tokens=cache_creation, cache_read_tokens=cache_read)
    # UploadTokens is the true total input-side volume (fresh + cache write +
    # cache read), matching the convention spend_logger.log_analysis_run uses -
    # the cache split isn't lost, it's priced differently inside cost_gbp().
    total_input = inp + cache_creation + cache_read
    write_header = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(_HEADERS)
        w.writerow([
            datetime.now(timezone.utc).isoformat(),
            AGENT_NAME, "ClaudeCode", purpose, description,
            model, total_input, out, cost,
        ])


def _git_push_log(repo_root: Path) -> None:
    """Stage, commit, rebase, and push the spend CSV. Silently skips on any error."""
    try:
        repo = str(repo_root)
        subprocess.run(
            ["git", "-C", repo, "add", str(LOG_PATH)],
            check=True, capture_output=True,
        )
        # Nothing staged means the CSV didn't change — skip the commit.
        if subprocess.run(
            ["git", "-C", repo, "diff", "--cached", "--quiet"],
            capture_output=True,
        ).returncode == 0:
            return
        subprocess.run(
            ["git", "-C", repo, "commit", "-m",
             f"auto: [{AGENT_NAME}] Update spend log"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", repo, "pull", "--rebase", "--autostash"],
            check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "-C", repo, "push"],
            check=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # never crash the hook


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

    with _StateLock():
        state = _load_state()
        from_line, already_billed = _session_state(state, session_id)

        new_entries, total_lines = _read_new_entries(transcript_path, from_line)
        inp, out, cache_creation, cache_read, model, newly_billed = _parse_usage(new_entries, already_billed)

        if inp > 0 or out > 0 or cache_creation > 0 or cache_read > 0:
            purpose = _infer_purpose(last_message)
            description = _extract_description(last_message)
            _write_row(purpose, description, model, inp, out, cache_creation, cache_read)

        billed_ids = list(already_billed | newly_billed)[-MAX_BILLED_IDS_PER_SESSION:]
        state[session_id] = {"from_line": total_lines, "billed_ids": billed_ids}
        _save_state(state)
    _git_push_log(repo_root)


if __name__ == "__main__":
    main()

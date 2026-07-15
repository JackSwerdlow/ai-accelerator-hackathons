#!/usr/bin/env bash
# One-time setup: adds a Claude Code Stop hook scoped to this project only.
#
# The hook is written to wk09/.claude/settings.json (project-local, gitignored)
# so it fires ONLY when Claude Code is opened from within the wk09/ directory.
# Other projects are unaffected.
#
# Usage (run from anywhere inside the repo):
#   bash solution/spend/install_hook.sh Agent-Tom
#
# Re-running is safe — it overwrites any previous entry.

set -euo pipefail

AGENT_NAME="${1:-}"
if [[ -z "$AGENT_NAME" ]]; then
    echo "Usage: $0 <AgentName>   (e.g. Agent-Tom, Agent-Alice)" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/log_claude_code_session.py"
HOOK_CMD="AGENT_NAME=${AGENT_NAME} python3 ${SCRIPT_PATH}"

# Project-local settings: wk09/.claude/settings.local.json
# settings.local.json is the per-machine override file; it is gitignored and
# never committed, so each teammate's install stays private.
WK09_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SETTINGS_FILE="${WK09_DIR}/.claude/settings.local.json"

mkdir -p "$(dirname "$SETTINGS_FILE")"
if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo '{}' > "$SETTINGS_FILE"
fi

python3 - "$SETTINGS_FILE" "$HOOK_CMD" <<'PYEOF'
import json, sys

path, cmd = sys.argv[1], sys.argv[2]
with open(path) as f:
    settings = json.load(f)

new_hook  = {"type": "command", "command": cmd}
new_entry = {"hooks": [new_hook]}

hooks      = settings.setdefault("hooks", {})
stop_hooks = hooks.setdefault("Stop", [])

updated = False
for i, entry in enumerate(stop_hooks):
    for h in entry.get("hooks", []):
        if "log_claude_code_session.py" in h.get("command", ""):
            stop_hooks[i] = new_entry
            updated = True
            break

if not updated:
    stop_hooks.append(new_entry)

with open(path, "w") as f:
    json.dump(settings, f, indent=2)
PYEOF

echo "Hook installed for AGENT_NAME=${AGENT_NAME}"
echo "Settings written to: ${SETTINGS_FILE}  (project-local, not global)"
echo "Claude Code will log spend only when opened from: ${WK09_DIR}"
echo ""
echo "If you previously ran an older version that wrote to ~/.claude/settings.json,"
echo "run remove_hook.sh to clean that up."

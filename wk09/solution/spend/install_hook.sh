#!/usr/bin/env bash
# One-time setup: adds a Claude Code Stop hook so every response is logged
# automatically to ai-spend-log-{AGENT_NAME}.csv.
#
# Usage:
#   bash solution/spend/install_hook.sh Agent-Tom
#
# Run once per machine. Re-running is safe — it overwrites the previous entry.

set -euo pipefail

AGENT_NAME="${1:-}"
if [[ -z "$AGENT_NAME" ]]; then
    echo "Usage: $0 <AgentName>   (e.g. Agent-Tom, Agent-Alice)" >&2
    exit 1
fi

SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/log_claude_code_session.py"
HOOK_CMD="AGENT_NAME=${AGENT_NAME} python3 ${SCRIPT_PATH}"
SETTINGS_FILE="${HOME}/.claude/settings.json"

mkdir -p "$(dirname "$SETTINGS_FILE")"

# If settings file doesn't exist, start from an empty object
if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo '{}' > "$SETTINGS_FILE"
fi

# Use Python to safely merge the hook into existing settings (avoids jq dependency)
python3 - "$SETTINGS_FILE" "$HOOK_CMD" <<'PYEOF'
import json, sys

path, cmd = sys.argv[1], sys.argv[2]
with open(path) as f:
    settings = json.load(f)

new_hook = {"type": "command", "command": cmd}
new_entry = {"hooks": [new_hook]}

hooks = settings.setdefault("hooks", {})
stop_hooks = hooks.setdefault("Stop", [])

# Replace any existing spend-tracking entry, add if absent
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

echo "Installed Stop hook for AGENT_NAME=${AGENT_NAME}"
echo "Hook command: ${HOOK_CMD}"
echo "Settings: ${SETTINGS_FILE}"
echo ""
echo "Claude Code will now log every response to:"
echo "  $(dirname "$SCRIPT_PATH")/ai-spend-log-${AGENT_NAME}.csv"

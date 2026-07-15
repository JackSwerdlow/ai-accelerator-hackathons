#!/usr/bin/env bash
# Removes the spend-tracking Stop hook from both the project-local and global
# Claude Code settings files.
#
# Run this if you no longer want spend logging, or to clean up a previous
# global install made by an older version of install_hook.sh.
#
# Usage:
#   bash solution/spend/remove_hook.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WK09_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

remove_from() {
    local settings_file="$1"
    if [[ ! -f "$settings_file" ]]; then
        return
    fi
    python3 - "$settings_file" <<'PYEOF'
import json, sys

path = sys.argv[1]
with open(path) as f:
    settings = json.load(f)

stop_hooks = settings.get("hooks", {}).get("Stop", [])
filtered = [
    entry for entry in stop_hooks
    if not any(
        "log_claude_code_session.py" in h.get("command", "")
        for h in entry.get("hooks", [])
    )
]

if len(filtered) == len(stop_hooks):
    print(f"  No spend-tracking hook found in {path}")
    sys.exit(0)

settings["hooks"]["Stop"] = filtered
if not settings["hooks"]["Stop"]:
    del settings["hooks"]["Stop"]
if not settings["hooks"]:
    del settings["hooks"]

with open(path, "w") as f:
    json.dump(settings, f, indent=2)

print(f"  Removed from {path}")
PYEOF
}

echo "Removing spend-tracking hook..."
remove_from "${WK09_DIR}/.claude/settings.json"
remove_from "${HOME}/.claude/settings.json"
echo "Done."

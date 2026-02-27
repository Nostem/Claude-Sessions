#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME="$HOME/.obsidian-agent"

echo "=== Obsidian Collaborator Setup ==="

mkdir -p "$RUNTIME/repos" "$RUNTIME/logs"

# Copy config template if not present
if [ ! -f "$RUNTIME/config.json" ]; then
    cp "$SCRIPT_DIR/config.json" "$RUNTIME/config.json"
    echo ""
    echo "Config copied to $RUNTIME/config.json"
    echo "Edit it now — set vault_path, daily_notes_folder, output_folder."
    echo "Press Enter when ready..."
    read
fi

echo ""
read -rsp "ANTHROPIC_API_KEY: " ANTHROPIC_KEY; echo
read -rsp "BRAVE_API_KEY (Enter to skip): " BRAVE_KEY; echo

# Write API keys to runtime config (merge into existing JSON)
python3 - <<PYEOF
import json, os
path = os.path.expanduser("~/.obsidian-agent/config.json")
c = json.load(open(path))
c["anthropic_api_key"] = "$ANTHROPIC_KEY"
if "$BRAVE_KEY":
    c["brave_api_key"] = "$BRAVE_KEY"
json.dump(c, open(path, "w"), indent=2)
PYEOF

# Install Python dependencies in a virtual environment
VENV="$RUNTIME/venv"
python3 -m venv "$VENV"
"$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next step: configure the Shell Commands plugin in Obsidian."
echo ""
echo "1. Open Obsidian → Settings → Community plugins → Browse"
echo "   Search 'Shell Commands' (by Taitava), install & enable."
echo ""
echo "2. In Shell Commands settings, click '+ New shell command' and enter:"
echo ""
echo "   $VENV/bin/python3 $SCRIPT_DIR/obsidian-watcher.py \"{{file_path:absolute}}\""
echo ""
echo "3. Click the clock icon next to the command → enable:"
echo "   'After saving a file'"
echo ""
echo "4. Done. Write '- #research some topic' in today's daily note, save,"
echo "   and the agent will respond."
echo ""
echo "Logs: $RUNTIME/logs/"

#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME="$HOME/.obsidian-agent"
LOGS="$RUNTIME/logs"
PLIST_SRC="$SCRIPT_DIR/launch_agent/ai.obsidian.agent.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/ai.obsidian.agent.plist"

echo "=== Obsidian Collaborator Setup ==="

mkdir -p "$RUNTIME/repos" "$LOGS"

# Copy config template if not present
if [ ! -f "$RUNTIME/config.json" ]; then
    cp "$SCRIPT_DIR/config.json" "$RUNTIME/config.json"
    echo ""
    echo "Config copied to $RUNTIME/config.json"
    echo "Edit it now — set vault_path, daily_notes_folder, output_folder."
    echo "Press Enter when ready..."
    read
fi

# Read vault + daily notes path from config
VAULT=$(python3 -c "import json,os; c=json.load(open('$RUNTIME/config.json')); print(os.path.expanduser(c['vault_path']))")
DAILY=$(python3 -c "import json; c=json.load(open('$RUNTIME/config.json')); print(c.get('daily_notes_folder','Daily Notes'))")
DAILY_PATH="$VAULT/$DAILY"

echo ""
read -rsp "ANTHROPIC_API_KEY: " ANTHROPIC_KEY; echo
read -rsp "BRAVE_API_KEY (Enter to skip): " BRAVE_KEY; echo

# Install Python dependencies
pip3 install -r "$SCRIPT_DIR/requirements.txt" --quiet

# Write plist with real values
sed \
    -e "s|PLACEHOLDER_SCRIPT_PATH|$SCRIPT_DIR/obsidian-watcher.py|g" \
    -e "s|PLACEHOLDER_DAILY_NOTES_PATH|$DAILY_PATH|g" \
    -e "s|PLACEHOLDER_LOG_PATH|$LOGS|g" \
    -e "s|PLACEHOLDER_ANTHROPIC_KEY|$ANTHROPIC_KEY|g" \
    -e "s|PLACEHOLDER_BRAVE_KEY|$BRAVE_KEY|g" \
    "$PLIST_SRC" > "$PLIST_DEST"

launchctl unload "$PLIST_DEST" 2>/dev/null || true
launchctl load "$PLIST_DEST"

echo ""
echo "Done! Obsidian Collaborator is running."
echo "Write '- #research some topic' in today's daily note to test."
echo "Logs: $LOGS/"

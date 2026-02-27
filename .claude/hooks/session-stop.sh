#!/bin/bash
# Stop hook — end-of-session reminder to persist memory patterns.
# Outputs a prompt reminding Claude to store successful patterns via ruflo
# before the session closes, completing the memory-driven workflow loop.

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Check if there are uncommitted changes to warn about
GIT_STATUS=$(git -C "$PROJECT_DIR" status --short 2>/dev/null)
UNCOMMITTED_COUNT=$(echo "$GIT_STATUS" | grep -c '.' 2>/dev/null || echo "0")

echo ""
echo "════════════════════════════════════════"
echo "  SESSION WRAP-UP CHECKLIST"
echo "════════════════════════════════════════"

if [ "$UNCOMMITTED_COUNT" -gt 0 ]; then
    echo "  [!] $UNCOMMITTED_COUNT uncommitted change(s) detected"
    echo "      Run /commit or git commit before closing"
fi

echo "  [ ] Store successful patterns:"
echo "      memory_store: { pattern, outcome, tags }"
echo "  [ ] Update CHANGELOG.md in relevant project folder"
echo "  [ ] Push branch if work is complete"
echo "════════════════════════════════════════"
echo ""

exit 0

#!/bin/bash
# PreCompact hook — saves task context before conversation is compressed.
# Writes a snapshot to .claude/context-snapshot.md so the session can
# resume with full awareness of in-progress work.

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
SNAPSHOT_FILE="$PROJECT_DIR/.claude/context-snapshot.md"

TIMESTAMP=$(date -u '+%Y-%m-%d %H:%M UTC')

# Gather git state
GIT_BRANCH=$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_STATUS=$(git -C "$PROJECT_DIR" status --short 2>/dev/null | head -20 || echo "no changes")
RECENT_COMMITS=$(git -C "$PROJECT_DIR" log --oneline -5 2>/dev/null || echo "no commits")

cat > "$SNAPSHOT_FILE" <<EOF
# Context Snapshot — $TIMESTAMP

## Active Branch
\`$GIT_BRANCH\`

## Recent Commits
\`\`\`
$RECENT_COMMITS
\`\`\`

## Uncommitted Changes
\`\`\`
$GIT_STATUS
\`\`\`

## Session Notes
_Snapshot created automatically before context compression._
_Review this file at session start or after compaction to restore context._

## Workspace
- Project: Claude-Sessions
- Subprojects: OpenClaw, Polygun-trading
- MCP: ruflo (claude-flow) active
EOF

echo "[pre-compact] Context snapshot saved to .claude/context-snapshot.md" >&2
exit 0

#!/bin/bash
# SessionStart hook — installs claude-flow (ruflo) for Claude Code on the web
set -euo pipefail

# Only run in remote (web) sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

echo "[session-start] Installing claude-flow (ruflo) dependencies..."
npm install --prefer-offline --no-audit --no-fund 2>&1

echo "[session-start] Verifying ruflo CLI..."
npx ruflo --version 2>/dev/null || npx ruflo@alpha --version 2>/dev/null || echo "[session-start] ruflo version check skipped (alpha build)"

# Persist useful env vars for the session
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export CLAUDE_FLOW_ENABLED=true' >> "$CLAUDE_ENV_FILE"
  echo 'export NODE_PATH="./node_modules"' >> "$CLAUDE_ENV_FILE"
fi

echo "[session-start] claude-flow ready."

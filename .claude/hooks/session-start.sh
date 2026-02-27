#!/bin/bash
# SessionStart hook — installs claude-flow (ruflo) + superpowers skills for Claude Code on the web
set -euo pipefail

# Only run in remote (web) sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# ── 1. claude-flow (ruflo) ────────────────────────────────────────────────────
echo "[session-start] Installing claude-flow (ruflo) dependencies..."
npm install --prefer-offline --no-audit --no-fund 2>&1

echo "[session-start] Verifying ruflo CLI..."
npx ruflo --version 2>/dev/null || npx ruflo@alpha --version 2>/dev/null || echo "[session-start] ruflo version check skipped (alpha build)"

# ── 2. superpowers skills ─────────────────────────────────────────────────────
SKILLS_DIR="${HOME}/.claude/skills"
SUPERPOWERS_MARKER="${SKILLS_DIR}/.superpowers-installed"

if [ ! -f "$SUPERPOWERS_MARKER" ]; then
  echo "[session-start] Installing superpowers skills..."
  mkdir -p "$SKILLS_DIR"

  TMP=$(mktemp -d)
  curl -fsSL "https://github.com/obra/superpowers/archive/refs/heads/main.tar.gz" \
    | tar -xz -C "$TMP" 2>&1

  # Copy all skill directories into ~/.claude/skills/
  cp -r "$TMP/superpowers-main/skills/"* "$SKILLS_DIR/"
  rm -rf "$TMP"

  # Write marker so subsequent sessions skip the download (cached container state)
  echo "installed $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$SUPERPOWERS_MARKER"
  echo "[session-start] superpowers skills installed (brainstorming, TDD, debugging, and 11 more)."
else
  echo "[session-start] superpowers skills already present, skipping download."
fi

# ── 3. Environment vars ───────────────────────────────────────────────────────
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo 'export CLAUDE_FLOW_ENABLED=true' >> "$CLAUDE_ENV_FILE"
  echo 'export NODE_PATH="./node_modules"' >> "$CLAUDE_ENV_FILE"
fi

echo "[session-start] All systems ready (claude-flow + superpowers)."

#!/bin/bash
# PreToolUse: secret-scanner
# Intercepts Write, Edit, and Bash tool calls and blocks any that contain
# patterns matching API keys, tokens, or credentials.

set -uo pipefail

INPUT=$(cat)

# Extract the content to scan based on tool name
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_name', ''))
except:
    print('')
" 2>/dev/null)

CONTENT=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', {})
    tool = d.get('tool_name', '')
    if tool == 'Write':
        print(inp.get('content', ''))
    elif tool == 'Edit':
        print(inp.get('new_string', ''))
    elif tool == 'Bash':
        print(inp.get('command', ''))
    else:
        print('')
except:
    print('')
" 2>/dev/null)

if [ -z "$CONTENT" ]; then
    exit 0
fi

# Secret patterns to block
PATTERNS=(
    'sk-[a-zA-Z0-9]{20,}'
    'AKIA[0-9A-Z]{16}'
    'ghp_[a-zA-Z0-9]{36}'
    'ghs_[a-zA-Z0-9]{36}'
    'ghr_[a-zA-Z0-9]{36}'
    'AIza[0-9A-Za-z_-]{35}'
    'xoxb-[0-9]{11}-[0-9]{11}-[a-zA-Z0-9]{24}'
    'xoxp-[0-9-]{50,}'
    '[Aa][Nn][Tt][Hh][Rr][Oo][Pp][Ii][Cc]_API_KEY\s*=\s*["\x27]?sk-'
    'OPENAI_API_KEY\s*=\s*["\x27]?sk-'
    'AWS_SECRET_ACCESS_KEY\s*=\s*["\x27][a-zA-Z0-9/+=]{40}'
    '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
)

MATCHED=""
for PATTERN in "${PATTERNS[@]}"; do
    if echo "$CONTENT" | grep -qP "$PATTERN" 2>/dev/null; then
        MATCHED="$PATTERN"
        break
    fi
done

if [ -n "$MATCHED" ]; then
    echo "[secret-scanner] BLOCKED: Potential secret detected matching pattern: $MATCHED" >&2
    echo "[secret-scanner] Remove the credential before proceeding. Never commit secrets." >&2
    exit 1
fi

exit 0

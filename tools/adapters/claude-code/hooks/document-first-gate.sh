#!/bin/bash
# HC-001: Document-First Gate
# Claude Code PreToolUse hook for Write/Edit tools
#
# Checks that focus.task or focus.issue is set in SNAPSHOT.yaml
# before allowing code file edits (excludes docs/, tools/, SNAPSHOT.yaml, CLAUDE.md).
#
# Exit 0 = allow (no output or empty output)
# To block: exit 0 with JSON containing permissionDecision: "deny"

# Read the tool input (passed via stdin as JSON)
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
if [ -z "$FILE_PATH" ]; then
  # Fallback for non-jq environments
  FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')
fi

# If no file path found, allow (not a file operation)
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Allow edits to documentation and config files
case "$FILE_PATH" in
  */docs/*|*/tools/*|*SNAPSHOT.yaml|*CLAUDE.md|*CONTEXT.md|*README.md|*AGENTS.md|*LLM_BRIEF.md|*.cursor/*|*/.claude/*|*/.github/*|*.prettierrc|*.markdownlint*|*.yamllint*|*.gitignore|*.project-os-sync)
    exit 0
    ;;
esac

# Check SNAPSHOT.yaml for active focus. The TARGET file's repo governs the edit
# (cross-repo edits must gate against the target's snapshot, not the session repo's).
PROJECT_DIR=""
DIR=$(dirname "$FILE_PATH")
while [ -n "$DIR" ] && [ "$DIR" != "/" ] && [ "$DIR" != "." ]; do
  if [ -f "$DIR/SNAPSHOT.yaml" ]; then
    PROJECT_DIR="$DIR"
    break
  fi
  DIR=$(dirname "$DIR")
done
if [ -z "$PROJECT_DIR" ]; then
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
fi
SNAPSHOT="$PROJECT_DIR/SNAPSHOT.yaml"
if [ ! -f "$SNAPSHOT" ]; then
  # No SNAPSHOT.yaml — not a project-os repo, allow
  exit 0
fi

# Template placeholder snapshot (template.replace_me: true) cannot carry focus; allow
if grep -qE '^[[:space:]]*replace_me:[[:space:]]*true' "$SNAPSHOT"; then
  exit 0
fi

# Extract task:/issue: from the focus block (from ^focus: to the next top-level key)
focus_value() {
  sed -n '/^focus:/,/^[^[:space:]]/p' "$SNAPSHOT" | grep -E "^[[:space:]]+$1:" | head -1 | sed -E "s/^[[:space:]]+$1:[[:space:]]*//" | sed 's/#.*//' | tr -d '"' | tr -d "'" | tr -d '[:space:]'
}
FOCUS_TASK=$(focus_value task)
FOCUS_ISSUE=$(focus_value issue)

if [ -z "$FOCUS_TASK" ] && [ -z "$FOCUS_ISSUE" ]; then
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Document-first rule (HC-001): No active task or issue in SNAPSHOT.yaml focus. Create or update the relevant task/issue before editing code files."
  }
}
EOF
  exit 0
fi

exit 0

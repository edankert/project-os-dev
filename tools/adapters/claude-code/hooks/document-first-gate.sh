#!/bin/bash
# HC-001: Document-First Gate
# Claude Code PreToolUse hook for Write/Edit tools
#
# Checks that focus.task or focus.issue is set in SNAPSHOT.yaml
# before allowing code file edits (excludes docs/, tools/, SNAPSHOT.yaml, CLAUDE.md).
#
# Exit 0 = allow, Exit 2 = block with message

# Read the file path from the tool input (passed via stdin as JSON)
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')

# If no file path found, allow (not a file operation)
if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Allow edits to documentation and config files
case "$FILE_PATH" in
  */docs/*|*/tools/*|*SNAPSHOT.yaml|*CLAUDE.md|*CONTEXT.md|*README.md|*AGENTS.md|*.cursor/*)
    exit 0
    ;;
esac

# Check SNAPSHOT.yaml for active focus
SNAPSHOT="SNAPSHOT.yaml"
if [ ! -f "$SNAPSHOT" ]; then
  # No SNAPSHOT.yaml — not a project-os repo, allow
  exit 0
fi

FOCUS_TASK=$(grep -A1 '^focus:' "$SNAPSHOT" | grep 'task:' | sed 's/.*task:[[:space:]]*//' | tr -d '"' | tr -d "'")
FOCUS_ISSUE=$(grep -A3 '^focus:' "$SNAPSHOT" | grep 'issue:' | sed 's/.*issue:[[:space:]]*//' | tr -d '"' | tr -d "'")

if [ -z "$FOCUS_TASK" ] && [ -z "$FOCUS_ISSUE" ]; then
  echo "BLOCKED: Document-first rule (HC-001). No active task or issue in SNAPSHOT.yaml focus. Create or update the relevant task/issue before editing code files."
  exit 2
fi

exit 0

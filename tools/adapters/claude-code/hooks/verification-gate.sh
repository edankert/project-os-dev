#!/bin/bash
# HC-003: Verification Gate
# Claude Code PostToolUse hook for Write/Edit tools
#
# Checks if a status transition to done/closed/verified has linked tests that are passing.
# Monitors writes to SNAPSHOT.yaml or note frontmatter that set terminal statuses.
#
# Exit 0 = allow (always — this is a post-hook, advisory only)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')

# Only check SNAPSHOT.yaml or docs/ note edits
case "$FILE_PATH" in
  *SNAPSHOT.yaml|*/docs/*.md)
    ;;
  *)
    exit 0
    ;;
esac

# Check if the edit contains a status transition to a terminal state
CONTENT=$(echo "$INPUT" | grep -o '"new_string"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1)

if echo "$CONTENT" | grep -qE 'status:[[:space:]]*(done|closed|verified)'; then
  echo "NOTE: Status transition to done/closed/verified detected. Ensure all linked TST-* notes are status: passing before finalizing (HC-003 Verification Gate)."
fi

exit 0

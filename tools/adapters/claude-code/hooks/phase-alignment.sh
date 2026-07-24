#!/bin/bash
# HC-004: Phase Alignment
# Claude Code PostToolUse hook for Write/Edit tools
#
# Warns when a task is transitioned to 'doing' and its phase is ahead of focus.phase.
# Advisory only — does not block.
#
# Exit 0 = allow (always)

INPUT=$(cat)
CONTENT=$(echo "$INPUT" | grep -o '"new_string"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1)

if echo "$CONTENT" | grep -qE 'status:[[:space:]]*doing'; then
  PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
  SNAPSHOT="$PROJECT_DIR/SNAPSHOT.yaml"
  if [ -f "$SNAPSHOT" ]; then
    FOCUS_PHASE=$(grep -A1 '^focus:' "$SNAPSHOT" | grep 'phase:' | sed 's/.*phase:[[:space:]]*//' | tr -d '"' | tr -d "'")
    if [ -n "$FOCUS_PHASE" ] && [ "$FOCUS_PHASE" != "" ]; then
      echo "NOTE: Task transitioning to 'doing'. Verify its phase aligns with the active phase ($FOCUS_PHASE) per HC-004 Phase Alignment."
    fi
  fi
fi

exit 0

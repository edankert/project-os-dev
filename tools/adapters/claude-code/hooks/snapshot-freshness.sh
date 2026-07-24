#!/bin/bash
# HC-002: Snapshot Freshness
# Claude Code SessionStart hook
#
# Warns if SNAPSHOT.yaml hasn't been read/verified at session start.
# This is a reminder hook — it does not block.
#
# Exit 0 = allow (always), outputs a reminder message

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
SNAPSHOT="$PROJECT_DIR/SNAPSHOT.yaml"
if [ ! -f "$SNAPSHOT" ]; then
  exit 0
fi

UPDATED=$(grep '^updated:' "$SNAPSHOT" | sed 's/updated:[[:space:]]*//' | tr -d '"' | tr -d "'")

if [ -n "$UPDATED" ]; then
  echo "REMINDER: Read SNAPSHOT.yaml to understand current project state, focus, and active work before proceeding."
fi

exit 0

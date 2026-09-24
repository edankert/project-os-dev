#!/bin/bash
# HC-002: Startup orientation
# Claude Code SessionStart hook
#
# Prints the part of SNAPSHOT.yaml a session needs: focus, counts and in-flight
# items, from tools/scripts/snapshot-slice.py (project-os-dev TASK-0080). It
# replaced a reminder to read the whole file, which agents followed in 5 of 260
# sessions (ISS-0031). The filename is kept so existing settings.json files
# keep resolving.
#
# Fails open: without python3, or if the slice prints nothing, the old reminder
# is printed instead. Never blocks.
#
# Exit 0 = allow (always)

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
SNAPSHOT="$PROJECT_DIR/SNAPSHOT.yaml"
if [ ! -f "$SNAPSHOT" ]; then
  exit 0
fi

SLICE="$PROJECT_DIR/tools/scripts/snapshot-slice.py"
if command -v python3 >/dev/null 2>&1 && [ -f "$SLICE" ]; then
  if python3 "$SLICE" "$PROJECT_DIR" 2>/dev/null; then
    exit 0
  fi
fi

echo "REMINDER: Read SNAPSHOT.yaml to understand current project state, focus, and active work before proceeding."
exit 0

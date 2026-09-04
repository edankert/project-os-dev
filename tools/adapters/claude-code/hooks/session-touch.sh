#!/bin/bash
# HC-006 support: record that this session wrote a file.
# Claude Code PostToolUse hook for Write/Edit/NotebookEdit.
#
# The close-out check blocks a stop while focus.task is set. On its own it
# cannot tell a turn that implemented the focus item from one that answered a
# question, so a repo whose focus is legitimately set paid a forced continuation
# on every turn (project-os-dev ISS-0056). This marker is the missing signal.
#
# close-out-check.sh deletes the marker when it blocks, so the reminder arrives
# once per burst of work rather than once per turn.
#
# Known limit, recorded rather than papered over: only the file-editing tools
# set this. A session that writes through Bash instead leaves no marker and the
# close-out check stays quiet. Guessing which shell commands write would be a
# string match that ages badly; ISS-0056 carries the alternatives.
#
# Exit 0 always. This hook never blocks and never prints.

INPUT=$(cat)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -r "$SCRIPT_DIR/shared/session-marker.sh" ] || exit 0
. "$SCRIPT_DIR/shared/session-marker.sh"

SESSION=$(printf '%s' "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
[ -n "$SESSION" ] || exit 0

MARKER=$(session_marker "$SESSION" "${CLAUDE_PROJECT_DIR:-.}") || exit 0
: > "$MARKER" 2>/dev/null
exit 0

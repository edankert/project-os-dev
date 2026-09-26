#!/bin/bash
# HC-006: Close-out Check
# Claude Code Stop hook
#
# Checks that (a) the docs validator passes (SNAPSHOT<->notes sync, link graph,
# verification invariant) and (b) SNAPSHOT.yaml focus is not still set
# (indicating work in progress that wasn't closed out). If a check fails but
# stop_hook_active is true (we already forced one continuation), allow stopping
# to prevent loops.
#
# The two halves have different strictness on purpose. The validator blocks
# every stop: a broken docs invariant is a real failure, not a reminder. The
# focus half blocks only a stop that follows a write, because a set focus is
# durable project state and says nothing about what this turn did. Blocking on
# it unconditionally cost a forced continuation on every turn -- including
# questions -- in any repo whose focus item was legitimately parked
# (project-os-dev ISS-0056). session-touch.sh records the write; this hook
# consumes the marker, so the reminder comes once per burst of work.
#
# Exit 0 = allow stop (no output or JSON output)

INPUT=$(cat)

# Prevent infinite loops: if this hook already forced continuation, allow stop
STOP_HOOK_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false' 2>/dev/null)
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
SNAPSHOT="$PROJECT_DIR/SNAPSHOT.yaml"
if [ ! -f "$SNAPSHOT" ]; then
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -r "$SCRIPT_DIR/shared/session-marker.sh" ] && . "$SCRIPT_DIR/shared/session-marker.sh"

# Sync the snapshot's derived fields from the notes first, as the pre-commit
# hook does (ADR-0009). Without it, a note that raised a counter blocked the stop
# with an error the next commit would have fixed by itself: in your-trainer a
# background planner created REQ-0221 and the main session's stop failed on
# COUNTER (project-os-dev ISS-0090). The sync writes only when a field is out of
# date, and leaves the file alone if someone else changed it meanwhile.
SYNC="$PROJECT_DIR/tools/scripts/sync-snapshot.py"
if [ -f "$SYNC" ] && command -v python3 >/dev/null 2>&1; then
  python3 "$SYNC" --repo-root "$PROJECT_DIR" --quiet >/dev/null 2>&1 || true
fi

# Mechanical validation first: block stop while the docs invariants are broken (HC-007).
VALIDATOR="$PROJECT_DIR/tools/scripts/validate-docs.sh"
if [ -x "$VALIDATOR" ]; then
  VALIDATION_OUTPUT=$("$VALIDATOR" --repo-root "$PROJECT_DIR" --quiet 2>&1)
  if [ $? -eq 1 ]; then
    SUMMARY=$(echo "$VALIDATION_OUTPUT" | head -10 | tr '\n' ' ' | sed 's/"/\\"/g')
    cat <<EOF
{
  "decision": "block",
  "reason": "Docs validation failed (HC-007): $SUMMARY -- Fix the snapshot/note drift before finishing (run tools/scripts/validate-docs.sh for the full report)."
}
EOF
    exit 0
  fi
fi

# Did this session write anything since the last reminder? An absent marker
# means it did not, so there is no close-out owed and the stop goes through.
#
# Every path that cannot answer the question falls through to blocking, which is
# the behaviour before ISS-0056: no session_id in the payload, no marker helper
# on disk. A check that silently disables itself when its inputs are missing is
# worse than one that nags.
SESSION_MARKER=""
if command -v session_marker >/dev/null 2>&1; then
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
  if [ -n "$SESSION_ID" ]; then
    SESSION_MARKER=$(session_marker "$SESSION_ID" "$PROJECT_DIR")
    if [ ! -e "$SESSION_MARKER" ]; then
      exit 0
    fi
  fi
fi

# Check if focus.task or focus.issue is still set (work in progress). Read the
# whole focus block, so key order does not matter. This used to pipe the value
# through `echo "" | jq -r --arg f ... '$f'`, which never runs the filter on an
# empty input, so both values were always empty and this hook never blocked
# (project-os-dev TASK-0102, found by TST-0007).
focus_value() {
  sed -n '/^focus:/,/^[^[:space:]]/p' "$SNAPSHOT" | grep -E "^[[:space:]]+$1:" | head -1 | sed -E "s/^[[:space:]]+$1:[[:space:]]*//" | sed 's/#.*//' | tr -d '"' | tr -d "'" | tr -d '[:space:]'
}
FOCUS_TASK=$(focus_value task)
FOCUS_ISSUE=$(focus_value issue)

# The focus task's note path, from its snapshot item: block style (`      file:`)
# or an inline flow map (`    TASK-0001: { file: "...", ... }`).
note_path() {
  awk -v id="$1" '
    $0 ~ ("^    " id ":") {
      found = 1
      if ($0 ~ /file:/) { line = $0; sub(/.*file:[[:space:]]*"?/, "", line); sub(/[",}].*/, "", line); print line; exit }
      next
    }
    found && /^    [^ ]/ { exit }
    found && /^      file:/ { line = $0; sub(/^      file:[[:space:]]*"?/, "", line); sub(/".*/, "", line); sub(/[[:space:]]+$/, "", line); print line; exit }
  ' "$SNAPSHOT"
}

# Unticked boxes under the note's "## Definition of Done" and "## Steps" headings,
# one per line, JSON-safe (project-os-dev TASK-0157). The Opus 5.5 prompting
# guide's pattern: when a turn ends with work open, reply by naming what is open.
open_boxes() {
  awk '
    /^```/ { fence = !fence; next }
    fence { next }
    /^## / { insec = ($0 ~ /^## (Definition of Done|Steps)[[:space:]]*$/); next }
    insec && /^[[:space:]]*- \[ \]/ { sub(/^[[:space:]]*- \[ \][[:space:]]*/, ""); if ($0 == "") $0 = "(a box with no text)"; print }
  ' "$1" | tr -d '\r' | tr '\t' ' ' | sed 's/\\/\\\\/g; s/"/\\"/g'
}

# Whether the note has a Definition of Done or Steps section at all. A note with
# neither has no boxes to be ticked, so "every box is ticked" would be false.
has_box_sections() {
  grep -qE '^## (Definition of Done|Steps)[[:space:]]*$' "$1"
}

# A focus task with no snapshot item (never added, or pruned): find its note by
# filename, the one convention every task note follows.
find_note() {
  find "$PROJECT_DIR/docs" -name "$1-*.md" -type f 2>/dev/null | head -1 | sed "s|^$PROJECT_DIR/||"
}

MIDFLIGHT="If you are stopping mid-flight for the user, write the handoff into the task note (HANDOFF.md, Before stopping work: what was done, what is next, approaches set aside, the user's decisions in their words), then stop; this check lets that second stop through."

if [ -n "$FOCUS_TASK" ] && [ "$FOCUS_TASK" != "" ] && [ "$FOCUS_TASK" != "null" ]; then
  # Focus task is still set — might need close-out. Spend the marker: the next
  # stop is silent until something is written again.
  [ -n "$SESSION_MARKER" ] && rm -f "$SESSION_MARKER"
  REASON="Close-out check (HC-006): focus.task is still $FOCUS_TASK in SNAPSHOT.yaml. If the work is complete, set the task status to done and clear focus now. $MIDFLIGHT"
  NOTE="$(note_path "$FOCUS_TASK")"
  { [ -n "$NOTE" ] && [ -f "$PROJECT_DIR/$NOTE" ]; } || NOTE="$(find_note "$FOCUS_TASK")"
  if [ -n "$NOTE" ] && [ -f "$PROJECT_DIR/$NOTE" ] && has_box_sections "$PROJECT_DIR/$NOTE"; then
    BOXES="$(open_boxes "$PROJECT_DIR/$NOTE")"
    OPEN=$(printf '%s' "$BOXES" | grep -c . )
    if [ "$OPEN" -gt 0 ]; then
      LIST="$(printf '%s\n' "$BOXES" | head -5 | awk 'BEGIN { ORS = "" } { if (NR > 1) print "; "; print "\\\"" $0 "\\\"" }')"
      MORE=""
      [ "$OPEN" -gt 5 ] && MORE=" and $((OPEN - 5)) more"
      REASON="Close-out check (HC-006): focus.task is still $FOCUS_TASK, and its note has $OPEN unticked box(es): $LIST$MORE. If work remains, carry on with it. If it is complete, tick each box with its evidence, set the task status to done and clear focus now. $MIDFLIGHT"
    else
      REASON="Close-out check (HC-006): focus.task is still $FOCUS_TASK, and every box in its note is ticked. Set the task status to done and clear focus now. $MIDFLIGHT"
    fi
  fi
  printf '{\n  "decision": "block",\n  "reason": "%s"\n}\n' "$REASON"
  exit 0
fi

if [ -n "$FOCUS_ISSUE" ] && [ "$FOCUS_ISSUE" != "" ] && [ "$FOCUS_ISSUE" != "null" ]; then
  [ -n "$SESSION_MARKER" ] && rm -f "$SESSION_MARKER"
  cat <<EOF
{
  "decision": "block",
  "reason": "Close-out check (HC-006): focus.issue is still $FOCUS_ISSUE in SNAPSHOT.yaml. If the issue is resolved, set its status to fixed and clear focus now. If you are stopping mid-flight for the user, write the handoff into the issue note (HANDOFF.md, Before stopping work), then stop; this check lets that second stop through."
}
EOF
  exit 0
fi

# No active focus — close-out appears complete
exit 0

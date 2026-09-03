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

if [ -n "$FOCUS_TASK" ] && [ "$FOCUS_TASK" != "" ] && [ "$FOCUS_TASK" != "null" ]; then
  # Focus task is still set — might need close-out
  cat <<EOF
{
  "decision": "block",
  "reason": "Close-out check (HC-006): focus.task is still $FOCUS_TASK in SNAPSHOT.yaml. If the work is complete, set the task status to done and clear focus now. If you are stopping mid-flight for the user, write the handoff into the task note (HANDOFF.md, Before stopping work: what was done, what is next, approaches set aside, the user's decisions in their words), then stop; this check lets that second stop through."
}
EOF
  exit 0
fi

if [ -n "$FOCUS_ISSUE" ] && [ "$FOCUS_ISSUE" != "" ] && [ "$FOCUS_ISSUE" != "null" ]; then
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

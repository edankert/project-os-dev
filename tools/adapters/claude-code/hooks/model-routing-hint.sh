#!/bin/bash
# HC-008: Delegation Hint
# Claude Code UserPromptSubmit hook
#
# Emits an advisory line stating where the work stands: the focus item, its
# status and its phase. It recommends the `planner` subagent only for a
# multi-item scaffold or an ambiguous ask (a single issue or task gets its note
# written in the main loop), and the `independent-reviewer` only in review
# states. The hint informs; the harness routes (project-os-dev ADR-0003). It
# stays within 3 lines and 600 characters, asserted by tools/scripts/test-hooks.sh,
# so it never grows into the SessionStart slice.
#
# Exit 0 = allow (always); stdout is injected as context and never blocks.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
SNAPSHOT="$PROJECT_DIR/SNAPSHOT.yaml"
[ -f "$SNAPSHOT" ] || exit 0

# Template placeholder snapshot (template.replace_me: true) carries no real
# focus; stay silent rather than hinting about placeholder state.
if grep -qE '^[[:space:]]*replace_me:[[:space:]]*true' "$SNAPSHOT"; then
  exit 0
fi

# Value of a key inside the top-level focus block, stripped of quotes,
# comments and [[wikilink]] brackets, and reduced to the bare ID — item keys
# under items.* are bare IDs, so "[[FEAT-0039-Some-Slug]]" must match FEAT-0039.
focus_id() {
  awk -v key="$1" '
    /^focus:/ { in_focus=1; next }
    in_focus && /^[^[:space:]]/ { exit }
    in_focus && $1 == key":" { print $2; exit }
  ' "$SNAPSHOT" | sed 's/#.*//' | tr -d '"' | tr -d "'" |
    sed -E 's/^\[\[//; s/\]\]$//; s/^([A-Z]+-[0-9]+).*/\1/'
}

# Status of an item ID under items.* (4-space item key, 6-space status).
# The status match is anchored at 6 spaces so a `status:` nested deeper inside
# the item (e.g. under a tests: list) is never mistaken for the item's own.
status_of() {
  [ -n "$1" ] || return 0
  awk -v id="$1" '
    $0 ~ ("^    " id ":") { found=1; next }
    found && /^    [A-Za-z]/ { exit }
    found && /^      status:[[:space:]]/ { print $2; exit }
  ' "$SNAPSHOT" | sed 's/#.*//' | tr -d '"' | tr -d "'" | tr -d '[:space:]'
}

TASK_ID=$(focus_id task)
ISSUE_ID=$(focus_id issue)
FEAT_ID=$(focus_id feature)
PHASE_ID=$(focus_id phase)
ACTIVE="${TASK_ID:-${ISSUE_ID:-$FEAT_ID}}"
STATUS=$(status_of "$ACTIVE")

WHERE="focus item $ACTIVE is '$STATUS'"
[ -n "$PHASE_ID" ] && WHERE="$WHERE, phase $PHASE_ID"
# The documentation requirement does not change: every change gets its note
# before the code. What changes is who writes it.
PREFLIGHT="A single issue or task gets its note written here before the code; a multi-item scaffold or an ambiguous ask goes to the 'planner' subagent with the user's prompt verbatim and one sentence on what the result enables, while you keep reading the code."

# Status vocabulary per STATUSES.md (tasks, issues, features, requirements).
# `deferred` is deliberately NOT terminal there; it is a parked state.
case "$STATUS" in
  backlog|triage|open|planned|draft|approved|proposed)
    HINT="$WHERE (planning). $PREFLIGHT"
    ;;
  doing|active)
    HINT="$WHERE (execution): implement here. For new work outside it: $PREFLIGHT"
    ;;
  review)
    HINT="$WHERE (review): verification goes to the 'independent-reviewer' subagent, a clean context that starts from the notes and the diff."
    ;;
  deferred)
    HINT="$WHERE (parked, not terminal): re-adopt it per STATUSES.md before working it, or pick other work."
    ;;
  done|fixed|declined|cancelled|superseded|implemented|retired)
    HINT="$WHERE (terminal): nothing in flight. $PREFLIGHT"
    ;;
  *)
    HINT="no focus item resolved: nothing in flight. $PREFLIGHT"
    ;;
esac

echo "project-os: $HINT"
exit 0

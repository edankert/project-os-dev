#!/bin/bash
# HC-008: Model Routing Hint
# Claude Code UserPromptSubmit hook
#
# Emits an advisory hint that routes the prompt to the lifecycle-appropriate
# model: preflight/planning to the `planner` subagent, implementation to the
# session's main model, review to the `independent-reviewer` subagent. The
# subagents carry the model pins (see tools/scripts/generate-adapters.py);
# a hook cannot change the session model, so this only steers delegation.
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
ACTIVE="${TASK_ID:-${ISSUE_ID:-$FEAT_ID}}"
STATUS=$(status_of "$ACTIVE")

# Status vocabulary per STATUSES.md (tasks, issues, features, requirements).
# `deferred` is deliberately NOT terminal there — it is a parked state.
case "$STATUS" in
  backlog|next|triage|open|planned|draft|approved|proposed|reopened)
    HINT="focus item $ACTIVE is '$STATUS' (planning) — delegate preflight (intake / scaffold / task breakdown / impact analysis) to the 'planner' subagent before writing code."
    ;;
  doing|in-progress|active)
    HINT="focus item $ACTIVE is '$STATUS' (execution) — implement in the main loop. If this prompt starts unrelated NEW work, delegate its preflight to the 'planner' subagent first."
    ;;
  in-review|implemented)
    HINT="focus item $ACTIVE is '$STATUS' (review) — delegate verification to the 'independent-reviewer' subagent."
    ;;
  blocked)
    HINT="focus item $ACTIVE is 'blocked' — resolve or re-scope the blocker before implementing; do not quietly work around it."
    ;;
  deferred)
    HINT="focus item $ACTIVE is 'deferred' (parked, not terminal) — re-adopt it per STATUSES.md before working it, or pick different work."
    ;;
  done|fixed|closed|cancelled|superseded|wont-fix|verified|retired)
    HINT="focus item $ACTIVE is '$STATUS' (terminal) — no active work in focus. If this prompt implies new work, delegate preflight to the 'planner' subagent before coding."
    ;;
  *)
    HINT="no active focus item resolved — if this prompt implies new work, delegate preflight to the 'planner' subagent before coding."
    ;;
esac

echo "project-os model routing: $HINT Independent review goes to 'independent-reviewer'. Advisory, not a gate."
exit 0

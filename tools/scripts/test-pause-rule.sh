#!/usr/bin/env bash
# TST-0005 (project-os-dev): one pause rule, stated once, and the stop-points that link it.
#
# FEAT-0024 claims two things a grep can settle. The rule that says when an
# agent pauses for the user is stated in exactly one file, LIFECYCLE.md
# ("When to pause for the user"); and every stop-point that used to phrase its
# own version now names the decision the user owns and links that section.
# The section itself must exist under that heading, or every link dangles. A
# further assertion checks that the generated planner subagent was regenerated
# after its prompt changed, since the planner prompt is one of the sites.
#
# Runs from anywhere: paths resolve from this script's location, so
# project-os-dev's TST-0005 can run it as `bash ../project-os/tools/scripts/test-pause-rule.sh`.
# Exit 0 = every assertion holds; exit 1 = at least one failed, each named.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"

ANCHOR='Pause for the user only when the work genuinely requires them'
LINK='"When to pause for the user"'
HOME_FILE="tools/instructions/LIFECYCLE.md"

assertions=0
failures=0
check() { # check <name> <ok:0|1> [detail]
  assertions=$((assertions + 1))
  if [[ "$2" -ne 0 ]]; then
    failures=$((failures + 1))
    echo "  FAIL $1${3:+: $3}"
  fi
}

# -- 1. exactly one file states the rule, and it is LIFECYCLE.md -------------
hits="$(cd "$ROOT" && { grep -rlF --include='*.md' "$ANCHOR" tools/instructions tools/skills tools/adapters docs/PHASES.md 2>/dev/null; grep -lF "$ANCHOR" tools/scripts/generate-adapters.py 2>/dev/null; } | sort -u)"
count=$(printf '%s\n' "$hits" | sed '/^$/d' | wc -l | tr -d ' ')
check "the pause rule is stated in exactly one file" "$([[ "$count" -eq 1 ]]; echo $?)" "found $count: $(printf '%s' "$hits" | tr '\n' ' ')"
check "the one file is $HOME_FILE" "$([[ "$hits" == "$HOME_FILE" ]]; echo $?)" "got '$hits'"
headings=$(grep -c '^### When to pause for the user$' "$ROOT/$HOME_FILE" 2>/dev/null || true)
check "the section the links name exists as a heading" "$([[ "${headings:-0}" -eq 1 ]]; echo $?)" "found $headings heading(s)"

# -- 2. each stop-point links the rule instead of restating it ---------------
# file:minimum occurrences. LIFECYCLE.md links its own section from two sites
# (impact analysis, phase alignment); issue-intake has two (the ambiguity check
# and the impact-analysis conflict); release-prep has two (open issues, release
# exceptions). docs/PHASES.md is the registry the phase-alignment rule restates.
SITES="tools/instructions/LIFECYCLE.md:2
tools/instructions/HOOKS.md:1
tools/skills/status-transition/SKILL.md:1
tools/skills/issue-intake/SKILL.md:2
tools/skills/feature-scaffold/SKILL.md:1
tools/skills/release-prep/SKILL.md:2
tools/skills/close-out/SKILL.md:1
tools/scripts/generate-adapters.py:1
docs/PHASES.md:1
tools/skills/impact-analysis/SKILL.md:1"
while IFS=: read -r site want; do
  [[ -z "$site" ]] && continue
  got=$(grep -cF "$LINK" "$ROOT/$site" 2>/dev/null || true)
  check "$site links the pause rule" "$([[ "${got:-0}" -ge "$want" ]]; echo $?)" "$got link(s), want at least $want"
done <<< "$SITES"

# The old phrasings must be gone from the sites (a link beside a restatement is
# still a restatement).
stale="$(cd "$ROOT" && grep -rnE 'stop and present resolution options|require explicit user confirmation|stop and request explicit user confirmation|Present the list to the user for decision|document it and discuss before proceeding|stop and return the ambiguities|Stop for user decision' tools/instructions tools/skills tools/scripts/generate-adapters.py docs/PHASES.md 2>/dev/null || true)"
check "no stop-point still carries its own phrasing" "$([[ -z "$stale" ]]; echo $?)" "$stale"

# -- 3. the generated planner matches the generator ---------------------------
if command -v python3 >/dev/null 2>&1; then
  out="$(python3 "$ROOT/tools/scripts/generate-adapters.py" --repo-root "$ROOT" --check 2>&1)"
  check "generated adapters are current (planner regenerated)" "$?" "$(printf '%s' "$out" | tail -1)"
else
  check "python3 available for the generator check" 1 "python3 not on PATH"
fi

echo "test-pause-rule: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

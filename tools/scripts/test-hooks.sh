#!/usr/bin/env bash
# TST-0007 (project-os-dev): the hooks emit what their contracts say they emit.
#
# Three Claude Code hooks read a snapshot and print a message, so they are
# tested directly against fixture repos under a tempdir, never this repo:
#   HC-006 close-out-check.sh   (Stop)             names two actions, not "acknowledge"
#   HC-008 model-routing-hint.sh (UserPromptSubmit) serves focus state; recommends the
#                                                    planner and the reviewer selectively;
#                                                    stays within a size bound
#   HC-001 document-first-gate.sh (PreToolUse)      allows paths outside every project-os
#                                                    repo (project-os-dev ISS-0003)
# Paths resolve from this script's location. Exit 0 = every assertion holds.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
HOOKS="$ROOT/tools/adapters/claude-code/hooks"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

assertions=0; failures=0
check() { # check <name> <ok:0|1> [detail]
  assertions=$((assertions + 1))
  if [[ "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi
}
has()    { printf '%s' "$1" | grep -qF -- "$2"; }
hasnot() { ! printf '%s' "$1" | grep -qF -- "$2"; }

# fixture <dir> <task-id> <task-status> <feature-id> <feature-status> <issue-id>
fixture() {
  mkdir -p "$1"
  cat > "$1/SNAPSHOT.yaml" <<YAML
version: 1
updated: "2026-09-03T00:00Z"
template:
  replace_me: false
counters:
  TASK: 1
focus:
  task: "$2"
  feature: "$4"
  phase: "PHASE-0001"
  issue: "$6"
items:
  features:
    FEAT-0001:
      file: docs/features/x/FEAT-0001.md
      status: $5
  tasks:
    TASK-0001:
      file: docs/features/x/plan/tasks/TASK-0001.md
      status: $3
  issues:
    ISS-0001:
      file: docs/issues/ISS-0001.md
      status: open
YAML
}
stop_hook() { printf '{"stop_hook_active": %s}' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/close-out-check.sh" 2>/dev/null; }
hint()      { printf '{"prompt":"x"}' | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/model-routing-hint.sh" 2>/dev/null; }
gate()      { printf '{"tool_input":{"file_path":"%s"}}' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/document-first-gate.sh" 2>/dev/null; }

# -- HC-006: the Stop hook names two actions ---------------------------------
fixture "$TMP/doing" TASK-0001 doing FEAT-0001 doing ""
out="$(stop_hook "$TMP/doing" false)"
check "stop hook blocks while focus.task is set" "$(has "$out" '"decision": "block"'; echo $?)"
check "stop hook, work complete: set the status and clear focus" "$(has "$out" 'set the task status to done and clear focus now'; echo $?)"
check "stop hook, mid-flight: write the handoff, then stop" "$( { has "$out" 'write the handoff' && has "$out" 'then stop'; }; echo $?)"
check "stop hook no longer says acknowledge to continue" "$(hasnot "$out" 'acknowledge'; echo $?)"
out2="$(stop_hook "$TMP/doing" true)"
check "the loop guard lets the second stop through" "$([[ -z "$out2" ]]; echo $?)" "got: $out2"
fixture "$TMP/issue" "" doing FEAT-0001 doing ISS-0001
out="$(stop_hook "$TMP/issue" false)"
check "stop hook, issue in focus: names the two actions" "$( { has "$out" 'set its status to fixed and clear focus now' && has "$out" 'write the handoff'; }; echo $?)"

# -- HC-008: the hint serves state ------------------------------------------
fixture "$TMP/empty" "" done FEAT-0001 done ""
sed -i.bak 's/^  feature: "FEAT-0001"/  feature: ""/' "$TMP/empty/SNAPSHOT.yaml"; rm -f "$TMP/empty/SNAPSHOT.yaml.bak"
h_empty="$(hint "$TMP/empty")"
check "hint, empty focus: states that nothing is in flight" "$(has "$h_empty" 'nothing in flight'; echo $?)" "$h_empty"
check "hint, empty focus: does not instruct delegation" "$( { hasnot "$h_empty" 'delegate preflight' && hasnot "$h_empty" 'before coding'; }; echo $?)" "$h_empty"
check "hint, empty focus: still says every change gets its note first" "$(has "$h_empty" 'note written here before the code'; echo $?)" "$h_empty"

fixture "$TMP/planning" TASK-0001 backlog FEAT-0001 doing ""
h_plan="$(hint "$TMP/planning")"
check "hint, planning state: names the item, its status and its phase" "$( { has "$h_plan" "TASK-0001 is 'backlog'" && has "$h_plan" 'PHASE-0001'; }; echo $?)" "$h_plan"
check "hint, planning state: recommends the planner for a multi-item scaffold or an ambiguous ask" "$( { has "$h_plan" "'planner'" && has "$h_plan" 'multi-item scaffold or an ambiguous ask'; }; echo $?)" "$h_plan"
check "hint: the delegation carries the prompt verbatim and the reason" "$( { has "$h_plan" 'prompt verbatim' && has "$h_plan" 'what the result enables'; }; echo $?)" "$h_plan"
check "hint: the lead keeps reading while the planner runs" "$(has "$h_plan" 'keep reading the code'; echo $?)" "$h_plan"

fixture "$TMP/review" "" done FEAT-0001 review ""
h_rev="$(hint "$TMP/review")"
check "hint, review state: sends verification to the reviewer" "$(has "$h_rev" "'independent-reviewer'"; echo $?)" "$h_rev"
h_doing="$(hint "$TMP/doing")"
# The three remaining arms of the case statement: blocked, deferred, and the
# terminal list (a focused task at `done`). Review found them unguarded: a
# review sentence inserted into the terminal arm, or a padded blocked arm,
# passed every assertion (TST-0007 round 1, finding 9).
fixture "$TMP/blocked" TASK-0001 blocked FEAT-0001 doing "";   h_blocked="$(hint "$TMP/blocked")"
fixture "$TMP/deferred" TASK-0001 deferred FEAT-0001 doing ""; h_deferred="$(hint "$TMP/deferred")"
fixture "$TMP/terminal" TASK-0001 done FEAT-0001 doing "";     h_terminal="$(hint "$TMP/terminal")"
check "hint, terminal state: says nothing is in flight and who writes the next note" "$( { has "$h_terminal" 'nothing in flight' && has "$h_terminal" "'planner'"; }; echo $?)" "$h_terminal"
check "hint, blocked state: names the blocker, not a delegation" "$( { has "$h_blocked" 'blocker' && hasnot "$h_blocked" "'planner'"; }; echo $?)" "$h_blocked"
check "hint, deferred state: says to re-adopt first" "$(has "$h_deferred" 're-adopt'; echo $?)" "$h_deferred"
for pair in "empty:$h_empty" "planning:$h_plan" "doing:$h_doing" "blocked:$h_blocked" "deferred:$h_deferred" "terminal:$h_terminal"; do
  name="${pair%%:*}"; text="${pair#*:}"
  check "hint, $name state: no review sentence" "$(hasnot "$text" 'independent-reviewer'; echo $?)" "$text"
done

# Size bound (TASK-0103): at most 3 lines and 600 characters in every one of
# the seven states, so the hint never grows into the SessionStart slice
# FEAT-0021 serves.
for pair in "empty:$h_empty" "planning:$h_plan" "doing:$h_doing" "review:$h_rev" "blocked:$h_blocked" "deferred:$h_deferred" "terminal:$h_terminal"; do
  name="${pair%%:*}"; text="${pair#*:}"
  lines=$(printf '%s\n' "$text" | wc -l | tr -d ' '); chars=${#text}
  check "hint, $name state: within 3 lines and 600 characters" "$([[ "$lines" -le 3 && "$chars" -le 600 ]]; echo $?)" "$lines lines, $chars chars"
done

# -- HC-001: the four paths of ISS-0003 ---------------------------------------
fixture "$TMP/proj" "" backlog FEAT-0001 backlog ""
mkdir -p "$TMP/scratch/scratchpad" "$TMP/other/src"
check "gate: a scratch path with no repo above it is allowed" "$([[ -z "$(gate "$TMP/proj" "$TMP/scratch/scratchpad/report.html")" ]]; echo $?)"
check "gate: a path in a repo with no SNAPSHOT.yaml is allowed" "$([[ -z "$(gate "$TMP/proj" "$TMP/other/src/main.py")" ]]; echo $?)"
check "gate: a relative path inside the project is denied" "$(has "$(cd "$TMP/proj" && gate "$TMP/proj" "src/main.py")" '"deny"'; echo $?)"
check "gate: an absolute path inside the project is denied" "$(has "$(gate "$TMP/proj" "$TMP/proj/src/main.py")" '"deny"'; echo $?)"

echo "test-hooks: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

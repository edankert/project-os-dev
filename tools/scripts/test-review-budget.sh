#!/usr/bin/env bash
# The review budget hook against recorded hook inputs (project-os-dev TASK-0128).
# It must leave every other session alone, warn the reviewer once, stop it past
# the budget with an instruction to report, and still let it record a verdict.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/../adapters/claude-code/hooks/review-budget.sh"
failures=0
n=0
check() { # check <description> <command...>
  n=$((n + 1))
  if "${@:2}" >/dev/null 2>&1; then echo "  ok   $1"; else echo "  FAIL $1"; failures=$((failures + 1)); fi
}
AGENT="test-$$-$RANDOM"
TMP="$(python3 -c 'import tempfile; print(tempfile.gettempdir())')"
trap 'rm -f "$TMP"/project-os-review-budget-test-$$-*.json' EXIT
call() { # call <event> <agent_type> <agent_id> <tool> <tool_input json>
  printf '{"hook_event_name":"%s","agent_type":"%s","agent_id":"%s","tool_name":"%s","tool_input":%s}' "$1" "$2" "$3" "$4" "$5" | bash "$HOOK"
}
pre() { call PreToolUse independent-reviewer "$AGENT" "$1" "${2:-{\}}"; }
post() { call PostToolUse independent-reviewer "$AGENT" "$1" '{}'; }

out="$(printf '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"ls"}}' | bash "$HOOK")"
check "a main-session call gets no output" test -z "$out"
out="$(call PreToolUse Explore other-agent Bash '{"command":"ls"}')"
check "another subagent gets no output" test -z "$out"

for i in $(seq 1 35); do pre Bash '{"command":"ls"}' >/dev/null; out="$(post Bash)"; [ -n "$out" ] && echo "  (early warning at call $i)"; done
out="$(pre Bash '{"command":"ls"}')"; check "call 36 is allowed" test -z "$out"
out="$(post Bash)"; check "call 36 is followed by a warning with 4 left" grep -q "4 left" <<<"$out"
for i in $(seq 37 39); do pre Bash '{"command":"ls"}' >/dev/null; done
out="$(pre Bash '{"command":"ls"}')"; check "call 40 is still allowed" test -z "$out"
out="$(pre Read '{"file_path":"src/a.py"}')"
check "call 41 is denied" grep -q '"permissionDecision": "deny"' <<<"$out"
check "the denial tells the reviewer to hand its report back" grep -q "Hand your report back now" <<<"$out"
# The message used to say "You may still record the verdict in the feature note",
# which is the one thing independent-review/SKILL.md forbids a reviewer to do
# (FEAT-0034 round two). A hook must not invite what the skill refuses.
check "the denial does not invite the reviewer to edit a note" bash -c '! grep -q "record the verdict in the feature note" <<<"$0"' "$out"
out="$(pre Edit '{"file_path":"/repo/docs/features/x/FEAT-0001-X.md"}')"
check "a verdict edit to a note is still allowed past the budget" test -z "$out"
out="$(pre Bash '{"command":"./gradlew test"}')"
check "a test run past the budget is denied" grep -q deny <<<"$out"
out="$(pre SubagentHandback '{"report":"the claims table"}')"
check "the reviewer can still hand its report back past the budget" test -z "$out"
for i in $(seq 1 10); do pre Edit '{"file_path":"/repo/docs/x.md"}' >/dev/null; done
out="$(pre Edit '{"file_path":"/repo/docs/x.md"}')"
check "note edits stop after the grace calls" grep -q deny <<<"$out"
out="$(pre SubagentHandback '{"report":"the claims table"}')"
check "the report still gets out after the grace calls are spent" test -z "$out"

AGENT="test-$$-r2"
pre Read '{"file_path":"/tmp/review-packet-FEAT-0001-r2.md"}' >/dev/null
for i in $(seq 2 15); do pre Bash '{"command":"ls"}' >/dev/null; done
out="$(pre Bash '{"command":"ls"}')"
check "round two is denied at call 16" grep -q "round 2" <<<"$out"

# A round-one reviewer that merely MENTIONS an -r2 path keeps its own budget.
# Matching the whole tool input dropped it to 15 for the rest of the run, and
# the switch never flips back (project-os-dev FEAT-0034 review, 2026-09-20).
AGENT="test-$$-mention"
pre Bash '{"command":"ls /tmp/review-packet-FEAT-0001-r2.md"}' >/dev/null
for i in $(seq 2 16); do pre Bash '{"command":"ls"}' >/dev/null; done
out="$(pre Bash '{"command":"ls"}')"
check "naming an -r2 packet in a command does not start round two" test -z "$out"
AGENT="test-$$-grep"
pre Bash '{"command":"grep -rn review-packet-FEAT-0002-r2 docs/"}' >/dev/null
for i in $(seq 2 30); do pre Bash '{"command":"ls"}' >/dev/null; done
out="$(pre Bash '{"command":"ls"}')"
check "a round-one reviewer keeps 40 calls after mentioning one" test -z "$out"

AGENT="test-$$-env"
for i in $(seq 1 5); do PROJECT_OS_REVIEW_BUDGET=5 pre Bash '{}' >/dev/null; done
out="$(PROJECT_OS_REVIEW_BUDGET=5 pre Bash '{}')"
check "a repo can set its own budget" grep -q "(5 tool calls" <<<"$out"

out="$(printf 'not json "independent-reviewer"' | bash "$HOOK")"; rc=$?
check "bad input fails open" test "$rc" -eq 0 -a -z "$out"

# REQ-0027: the budget is stated once. The hook holds the numbers and the skill
# states them in prose for the reviewer to read; nothing else may restate them.
# Before 2026-09-20 the figure 40 sat at five sites and changing it meant editing
# five files (FEAT-0034 review).
budget_one="$(python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('h', '$HERE/../adapters/claude-code/hooks/review-budget.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.budgets()[0])")"
check "the skill states the budget the hook enforces" grep -q "budget is $budget_one tool calls" "$HERE/../skills/independent-review/SKILL.md"
# Two checks, because the budget can be restated in prose or copied into code.
# Prose: no file may repeat the figure the skill states.
others="$(grep -rln "40 tool calls\|15 in round two\|ROUND_ONE_BUDGET = 40" "$HERE/.." "$HERE/../../.claude" "$HERE/../../.codex" 2>/dev/null | grep -v "/test-" | grep -v "independent-review/SKILL.md" | wc -l | tr -d " ")"
check "no other file restates the budget" test "$others" -eq 0
# Code: review-packet.py reads the budget from the hook and keeps no number of
# its own. It carried `return 40, 15` as a fallback, which the prose check could
# not see, and which would have printed 40 on a packet while the hook enforced
# a PROJECT_OS_REVIEW_BUDGET of 30 (FEAT-0034 round two).
check "review-packet.py keeps no budget number of its own" \
  bash -c '! grep -qE "return[[:space:]]+[0-9]+,[[:space:]]*[0-9]+" "$0"' "$HERE/review-packet.py"

echo "test-review-budget: $n assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

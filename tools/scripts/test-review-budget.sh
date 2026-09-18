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
check "the denial tells the reviewer to write its report" grep -q "Write your report now" <<<"$out"
out="$(pre Edit '{"file_path":"/repo/docs/features/x/FEAT-0001-X.md"}')"
check "a verdict edit to a note is still allowed past the budget" test -z "$out"
out="$(pre Bash '{"command":"./gradlew test"}')"
check "a test run past the budget is denied" grep -q deny <<<"$out"
for i in $(seq 1 10); do pre Edit '{"file_path":"/repo/docs/x.md"}' >/dev/null; done
out="$(pre Edit '{"file_path":"/repo/docs/x.md"}')"
check "note edits stop after the grace calls" grep -q deny <<<"$out"

AGENT="test-$$-r2"
pre Read '{"file_path":"/tmp/review-packet-FEAT-0001-r2.md"}' >/dev/null
for i in $(seq 2 15); do pre Bash '{"command":"ls"}' >/dev/null; done
out="$(pre Bash '{"command":"ls"}')"
check "round two is denied at call 16" grep -q "round 2" <<<"$out"

AGENT="test-$$-env"
for i in $(seq 1 5); do PROJECT_OS_REVIEW_BUDGET=5 pre Bash '{}' >/dev/null; done
out="$(PROJECT_OS_REVIEW_BUDGET=5 pre Bash '{}')"
check "a repo can set its own budget" grep -q "(5 tool calls" <<<"$out"

out="$(printf 'not json "independent-reviewer"' | bash "$HOOK")"; rc=$?
check "bad input fails open" test "$rc" -eq 0 -a -z "$out"

echo "test-review-budget: $n assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

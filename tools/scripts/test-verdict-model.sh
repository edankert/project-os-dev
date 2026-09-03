#!/usr/bin/env bash
# TST-0008 (project-os-dev): an executable test records no verdict (ADR-0025).
#
# Four assertions against fixture repos under a tempdir:
#   1. a done task whose linked command: test sits at `active` passes the gate;
#   2. the same test at `passing` with last_run: draws COMMAND-VERDICT as a
#      warning (a dated promotion under ADR-0011), and the validator still exits 0;
#   3. a manual test (no command:) at `ready` under a done task still fails the
#      gate, so the change loosened nothing for manual tests;
#   4. run-tests.py leaves every note byte-identical, exits 1 when a command
#      fails, and rejects --write.
# Paths resolve from this script's location. Exit 0 = every assertion holds.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
VALIDATOR="$ROOT/tools/scripts/validate-docs.py"
RUNNER="$ROOT/tools/scripts/run-tests.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

# fixture <dir> <test frontmatter extra lines> [command-line]
fixture() {
  local d="$1" extra="$2" cmdline="${3-command: \"true\"}"
  mkdir -p "$d/docs/features/x/plan/tasks" "$d/docs/tests"
  cat > "$d/SNAPSHOT.yaml" <<YAML
version: 1
updated: "2026-09-03T00:00Z"
template:
  replace_me: false
counters:
  FEAT: 1
  TASK: 1
  TST: 1
focus:
  task: ""
  feature: ""
  phase: ""
  issue: ""
items:
  features:
    FEAT-0001:
      file: docs/features/x/FEAT-0001-X.md
      title: "X"
      status: done
      owner: user:fixture
      tasks: [TASK-0001]
  tasks:
    TASK-0001:
      file: docs/features/x/plan/tasks/TASK-0001-X.md
      title: "X"
      status: done
      owner: user:fixture
      parent: FEAT-0001
      tests: [TST-0001]
  tests:
    TST-0001:
      file: docs/tests/TST-0001-X.md
      title: "X"
      status: STATUS_PLACEHOLDER
      owner: user:fixture
      scope: system
      level: unit
YAML
  cat > "$d/docs/features/x/FEAT-0001-X.md" <<'MD'
---
type: "[[feature]]"
id: FEAT-0001
title: "X"
status: done
owner: user:fixture
tasks: ["[[TASK-0001]]"]
acceptance_exception: "fixture"
---

# X
MD
  cat > "$d/docs/features/x/plan/tasks/TASK-0001-X.md" <<'MD'
---
type: "[[task]]"
id: TASK-0001
title: "X"
status: done
owner: user:fixture
parent: "[[FEAT-0001]]"
tests: ["[[TST-0001]]"]
---

# X
MD
  {
    printf -- '---\ntype: "[[test]]"\nid: TST-0001\ntitle: "X"\nowner: user:fixture\nscope: system\nlevel: unit\n%s\n%s\n---\n\n# X\n' "$cmdline" "$extra"
  } > "$d/docs/tests/TST-0001-X.md"
  local st; st=$(grep -m1 '^status:' "$d/docs/tests/TST-0001-X.md" | sed 's/status: *//')
  sed -i.bak "s/STATUS_PLACEHOLDER/$st/" "$d/SNAPSHOT.yaml"; rm -f "$d/SNAPSHOT.yaml.bak"
}
validate() { python3 "$VALIDATOR" --repo-root "$1" 2>&1; }

# 1. command: test at active under a done task: the gate is satisfied by CI
fixture "$TMP/active" $'status: active'
out="$(validate "$TMP/active")"; code=$?
check "a done task with a command: test at active passes the gate" "$code" "$(printf '%s' "$out" | grep ERROR | head -2 | tr '\n' ' ')"
check "no VERIFY error names the command: test" "$(printf '%s' "$out" | grep -q 'VERIFY\].*TST-0001'; [[ $? -ne 0 ]]; echo $?)"

# 1b. the same, at level: acceptance: automated by its command:, so no mark is owed
fixture "$TMP/acceptance" $'status: active'
sed -i.bak 's/^level: unit$/level: acceptance/' "$TMP/acceptance/docs/tests/TST-0001-X.md" "$TMP/acceptance/SNAPSHOT.yaml"; rm -f "$TMP/acceptance"/*.bak "$TMP/acceptance"/docs/tests/*.bak
out="$(validate "$TMP/acceptance")"; code=$?
check "an acceptance-level command: test at active owes no mark" "$(printf '%s' "$out" | grep -q 'VERIFY-ACCEPTANCE'; [[ $? -ne 0 ]]; echo $?)" "$(printf '%s' "$out" | grep VERIFY | head -1)"

# 2. the same test stamped passing with last_run: COMMAND-VERDICT warns, exit 0
fixture "$TMP/stamped" $'status: passing\nlast_run: "2026-09-03T00:00Z"\nexit_code: 0'
out="$(validate "$TMP/stamped")"; code=$?
check "a stamped command: test draws COMMAND-VERDICT" "$(printf '%s' "$out" | grep -q 'COMMAND-VERDICT'; echo $?)" "$(printf '%s' "$out" | tail -2 | tr '\n' ' ')"
check "COMMAND-VERDICT is a warning before the cutover" "$(printf '%s' "$out" | grep -q 'WARN.*COMMAND-VERDICT'; echo $?)"
check "the stamped fixture still exits 0" "$code"

# 3. a manual test at ready under a done task still fails the gate
fixture "$TMP/manual" $'status: ready' 'entrypoint: ""'
out="$(validate "$TMP/manual")"; code=$?
check "a manual test at ready under a done task still fails the gate" "$([[ $code -ne 0 ]]; echo $?)"
check "the failure is the VERIFY gate" "$(printf '%s' "$out" | grep -q 'VERIFY\].*TST-0001'; echo $?)" "$(printf '%s' "$out" | grep ERROR | head -2 | tr '\n' ' ')"
# 3b. the template's default is `command: ""`; an empty command is no command
# (a skip keyed on the key's presence passed 12 of 12: review finding 3)
fixture "$TMP/manual-empty" $'status: ready' 'command: ""'
out="$(validate "$TMP/manual-empty")"; code=$?
check "an empty command: is a manual test; at ready it still fails the gate" "$( { [[ $code -ne 0 ]] && printf '%s' "$out" | grep -q 'VERIFY\].*TST-0001'; }; echo $?)"
# 3c. a manual test at passing with a fresh last_verified: passes; a stale one fails
fixture "$TMP/manual-fresh" "status: passing
last_verified: \"$(date -u +%Y-%m-%d)\"" 'entrypoint: ""'
out="$(validate "$TMP/manual-fresh")"; code=$?
check "a manual test at passing with a fresh last_verified passes the gate" "$code" "$(printf '%s' "$out" | grep ERROR | head -1)"
fixture "$TMP/manual-stale" $'status: passing\nlast_verified: "2025-01-01"' 'entrypoint: ""'
out="$(validate "$TMP/manual-stale")"; code=$?
check "a manual test at passing but stale still fails the gate" "$( { [[ $code -ne 0 ]] && printf '%s' "$out" | grep -q 'stale'; }; echo $?)"

# 4. the runner writes nothing and exits 1 on a failure
fixture "$TMP/run" $'status: active' 'command: "false"'
before="$(cat "$TMP/run/docs/tests/TST-0001-X.md")"
python3 "$RUNNER" --repo-root "$TMP/run" >/dev/null 2>&1; code=$?
check "the runner exits 1 when a command fails" "$([[ $code -eq 1 ]]; echo $?)" "exit $code"
check "the runner leaves the note byte-identical" "$([[ "$before" == "$(cat "$TMP/run/docs/tests/TST-0001-X.md")" ]]; echo $?)"
python3 "$RUNNER" --repo-root "$TMP/run" --write >/dev/null 2>&1; code=$?
check "the runner rejects --write" "$([[ $code -eq 2 ]]; echo $?)" "exit $code"
fixture "$TMP/run-ok" $'status: active' 'command: "true"'
before="$(cat "$TMP/run-ok/docs/tests/TST-0001-X.md")"
python3 "$RUNNER" --repo-root "$TMP/run-ok" >/dev/null 2>&1; code=$?
check "the runner exits 0 when every command passes" "$code"
check "the runner leaves a passing test's note byte-identical too" "$([[ "$before" == "$(cat "$TMP/run-ok/docs/tests/TST-0001-X.md")" ]]; echo $?)"
# 4b. in CI an unrunnable command is a red build, because nothing else will
# notice (review finding 4); locally it stays an environment gap
fixture "$TMP/run-missing" $'status: active' 'command: "bash ../nonexistent/x.sh"'
CI=1 python3 "$RUNNER" --repo-root "$TMP/run-missing" >/dev/null 2>&1; code=$?
check "in CI an unrunnable test fails the run" "$([[ $code -eq 1 ]]; echo $?)" "exit $code"
env -u CI python3 "$RUNNER" --repo-root "$TMP/run-missing" >/dev/null 2>&1; code=$?
check "locally an unrunnable test is an environment gap" "$code" "exit $code"

echo "test-verdict-model: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

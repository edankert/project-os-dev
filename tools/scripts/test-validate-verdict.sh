#!/usr/bin/env bash
# validate-docs.sh ends with one verdict for every step it ran (project-os-dev
# ISS-0089, TASK-0170). In your-trainer the validator printed "validate-docs:
# OK", the walk check then failed, and a session that read the output instead
# of the exit status took the OK for the whole answer. Here the walk check is a
# stub that fails on demand, and the notes are this template's own, which pass.
# Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

# A copy of the template, so the stub walk check can sit beside the script.
rsync -a --exclude .git "$ROOT/" "$TMP/repo/"
R="$(cd "$TMP/repo" && pwd -P)"   # the validator prints the resolved path (/var is /private/var on macOS)
cat > "$R/tools/scripts/walk-sheet.py" <<'PY'
import os, sys
code = int(os.environ.get("WALK_EXIT", "0"))
if code:
    print("ERROR [WALK] walk-sheet --check (testbed): step 3 quotes text the check no longer has", file=sys.stderr)
sys.exit(code)
PY
run() { bash "$R/tools/scripts/validate-docs.sh" --repo-root "$R" "$@" 2>&1; }

out="$(run)"; code=$?
check "all steps pass: exit 0, and the last line says OK for notes and walk procedures" \
  "$( { [[ $code -eq 0 ]] && [[ "$(printf '%s\n' "$out" | tail -1)" == "validate-docs: OK ($R: notes and walk procedures)" ]]; }; echo $?)" "exit $code: $out"
check "the validator's own line says it covers only the notes" \
  "$(printf '%s\n' "$out" | grep -q '^validate-docs \[notes\]: OK'; echo $?)" "$out"

# The your-trainer case: the notes pass and the walk check fails.
out="$(WALK_EXIT=1 run)"; code=$?
check "the walk check fails after passing notes: exit 1" "$([[ $code -eq 1 ]]; echo $?)" "exit $code"
check "the last line says FAIL and names the failing step" \
  "$([[ "$(printf '%s\n' "$out" | tail -1)" == "validate-docs: FAIL (notes: OK; walk procedures: FAIL)" ]]; echo $?)" "$out"
check "no line of the output reads as a plain passing verdict" \
  "$(! printf '%s\n' "$out" | grep -q '^validate-docs: OK'; echo $?)" "$out"
check "filtering for ERROR finds the walk failure" \
  "$(printf '%s\n' "$out" | grep -E '^ERROR' | grep -q 'WALK'; echo $?)" "$out"

out="$(WALK_EXIT=2 run)"; code=$?
check "a walk check that cannot run is reported as such" \
  "$( { [[ $code -eq 2 ]] && [[ "$(printf '%s\n' "$out" | tail -1)" == "validate-docs: FAIL (notes: OK; walk procedures: could not run, exit 2)" ]]; }; echo $?)" "exit $code: $out"

# Failing notes: a task note with no parent.
mkdir -p "$R/docs/features/x/plan/tasks"
printf -- '---\ntype: "[[task]]"\nid: TASK-9999\nstatus: doing\n---\n# Orphan\n' > "$R/docs/features/x/plan/tasks/TASK-9999-Orphan.md"
out="$(run)"; code=$?
check "failing notes with a passing walk: the last line names the notes" \
  "$( { [[ $code -eq 1 ]] && [[ "$(printf '%s\n' "$out" | tail -1)" == "validate-docs: FAIL (notes: FAIL; walk procedures: OK)" ]]; }; echo $?)" "exit $code: $out"
out="$(run --quiet)"; code=$?
check "--quiet still prints a failing verdict last" \
  "$( { [[ $code -eq 1 ]] && printf '%s\n' "$out" | tail -1 | grep -q '^validate-docs: FAIL'; }; echo $?)" "$out"
rm -rf "$R/docs/features/x"

out="$(run --quiet)"; code=$?
check "--quiet prints nothing when everything passes" "$( { [[ $code -eq 0 ]] && [[ -z "$out" ]]; }; echo $?)" "$out"

# Run on its own, the validator keeps its plain line: the cockpit and people run it directly.
out="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1 | tail -1)"
check "validate-docs.py run directly still says validate-docs: OK" "$([[ "$out" == "validate-docs: OK ($R)" ]]; echo $?)" "$out"

echo "test-validate-verdict: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

#!/usr/bin/env bash
# FOCUS-MEMBERSHIP and TASK-MEMBERSHIP (project-os-dev ISS-0084): work in
# progress has a snapshot entry of its own. Runs the validator over a fixture
# repo in a tempdir and reads only these two gates; everything else the
# fixture trips is irrelevant here. Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$HERE/validate-docs.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

assertions=0; failures=0
check() { # check <name> <ok:0|1> [detail]
  assertions=$((assertions + 1))
  if [[ "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi
}
note() { # note <path> <id> <type> <status> [parent]
  mkdir -p "$TMP/$(dirname "$1")"
  printf -- '---\ntype: "[[%s]]"\nid: %s\nstatus: %s\n%s---\n\n# %s\n' "$3" "$2" "$4" "${5:+parent: \"[[$5]]\"
}" "$2" > "$TMP/$1"
}
# snapshot <focus-task> <feature-status> <task entries...>
snapshot() {
  local focus="$1" fstatus="$2"; shift 2
  {
    printf 'version: 1\nupdated: "2026-09-24T00:00Z"\ntemplate:\n  replace_me: false\ncounters:\n  FEAT: 1\n  TASK: 4\n'
    printf 'focus:\n  task: "%s"\n  feature: "FEAT-0001"\n  phase: ""\n  issue: ""\n' "$focus"
    printf 'items:\n  features:\n    FEAT-0001:\n      file: docs/features/x/FEAT-0001-X.md\n      status: %s\n      tasks: [TASK-0001, TASK-0002, TASK-0003]\n  tasks:\n' "$fstatus"
    for t in "$@"; do printf '    %s:\n      file: docs/features/x/plan/tasks/%s-X.md\n      status: %s\n      parent: FEAT-0001\n' "${t%%=*}" "${t%%=*}" "${t#*=}"; done
  } > "$TMP/SNAPSHOT.yaml"
}
run() { python3 "$VALIDATOR" --repo-root "$TMP" 2>&1; }

note docs/features/x/FEAT-0001-X.md FEAT-0001 feature doing
note docs/features/x/plan/tasks/TASK-0001-X.md TASK-0001 task doing FEAT-0001
note docs/features/x/plan/tasks/TASK-0002-X.md TASK-0002 task backlog FEAT-0001
note docs/features/x/plan/tasks/TASK-0003-X.md TASK-0003 task done FEAT-0001
note docs/features/x/plan/tasks/TASK-0004-X.md TASK-0004 task doing FEAT-0001

# Correct: every in-flight task has an entry; the done one may be pruned.
snapshot TASK-0001 doing TASK-0001=doing TASK-0002=backlog
out="$(run)"
check "a correct snapshot: no FOCUS-MEMBERSHIP" "$(! grep -q 'FOCUS-MEMBERSHIP' <<<"$out"; echo $?)" "$(grep MEMBERSHIP <<<"$out")"
check "a correct snapshot: no TASK-MEMBERSHIP" "$(! grep -q 'TASK-MEMBERSHIP' <<<"$out"; echo $?)" "$(grep MEMBERSHIP <<<"$out")"

# The 2026-09-24 case: the feature lists the tasks, the tasks have no entries.
snapshot TASK-0002 doing TASK-0001=doing
out="$(run)"
check "focus.task with a note but no entry is FOCUS-MEMBERSHIP" "$(grep -q 'FOCUS-MEMBERSHIP.*focus.task = TASK-0002' <<<"$out"; echo $?)" "$out"
check "a backlog task an in-flight feature lists, with no entry, is TASK-MEMBERSHIP" "$(grep -q 'TASK-MEMBERSHIP.*TASK-0002' <<<"$out"; echo $?)" "$(grep MEMBERSHIP <<<"$out")"
check "a done task a feature lists may be pruned" "$(! grep -q 'TASK-MEMBERSHIP.*TASK-0003' <<<"$out"; echo $?)" "$(grep MEMBERSHIP <<<"$out")"
check "a task no snapshot entry lists is not this check's concern" "$(! grep -q 'TASK-MEMBERSHIP.*TASK-0004' <<<"$out"; echo $?)" "$(grep MEMBERSHIP <<<"$out")"
check "each missing task is reported once" "$([[ $(grep -c 'TASK-MEMBERSHIP.*TASK-0002' <<<"$out") -eq 1 ]]; echo $?)" "$(grep -c 'TASK-MEMBERSHIP.*TASK-0002' <<<"$out")"

# A settled parent keeps its list as history: nothing is reported.
snapshot "" done TASK-0001=doing
out="$(run)"
check "a done feature's list is history, not work in progress" "$(! grep -q 'TASK-MEMBERSHIP' <<<"$out"; echo $?)" "$(grep MEMBERSHIP <<<"$out")"

# Both gates warn until their promotion date (ADR-0011 clause 3).
python3 - "$VALIDATOR" >/dev/null 2>&1 <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
sys.exit(0 if {"TASK-MEMBERSHIP", "FOCUS-MEMBERSHIP"} <= set(vd.PROMOTIONS) else 1)
PY
check "both gates are dated in PROMOTIONS" "$?"

echo "test-snapshot-membership: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

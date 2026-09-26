#!/usr/bin/env bash
# archive-notes.py (project-os-dev ISS-0091, TASK-0180, ADR-0048): finished
# tickets whose release is out move to docs/archive/, leave the snapshot, keep
# resolving, and draw only structural findings. Fixture git repo with a
# released tag. Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1 PROJECT_OS_NO_CACHE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"; rsync -a --exclude .git "$ROOT/" "$R/"
sed -i.bak 's/^  replace_me: true$/  replace_me: false/' "$R/SNAPSHOT.yaml"; rm -f "$R/SNAPSHOT.yaml.bak"
mkdir -p "$R/docs/features/x/plan/tasks" "$R/docs/issues" "$R/docs/changes" "$R/docs/releases" "$R/docs/tests/acceptance"
note() { local path="$1"; shift; { printf -- '---\n'; printf '%s\n' "$@"; printf -- '---\n# Note\n'; } > "$R/$path"; }
note docs/features/x/plan/tasks/TASK-0001-Shipped.md 'type: "[[task]]"' 'id: TASK-0001' 'status: done' 'parent: ""' 'tests: ["[[TST-0002]]"]'
note docs/features/x/plan/tasks/TASK-0002-Open.md 'type: "[[task]]"' 'id: TASK-0002' 'status: doing' 'parent: ""' 'related: ["[[TASK-0001]]"]'
note docs/features/x/plan/tasks/TASK-0003-Done-Later.md 'type: "[[task]]"' 'id: TASK-0003' 'status: doing' 'parent: ""'
note docs/issues/ISS-0001-Fixed.md 'type: "[[issue]]"' 'id: ISS-0001' 'status: fixed'
note docs/changes/CHG-20260901-A-Change.md 'type: "[[change]]"' 'id: CHG-20260901-A-Change' 'status: merged'
note docs/tests/acceptance/TST-0001-Retired.md 'type: "[[test]]"' 'id: TST-0001' 'status: retired' 'level: acceptance'
note docs/tests/TST-0002-Unit.md 'type: "[[test]]"' 'id: TST-0002' 'status: active' 'level: unit' 'command: "true"'
python3 - "$R/SNAPSHOT.yaml" <<'PY'
import sys
p = sys.argv[1]; t = open(p).read()
t = t.replace("items:\n", "items:\n  tasks:\n    TASK-0001:\n      file: docs/features/x/plan/tasks/TASK-0001-Shipped.md\n      status: done\n    TASK-0002:\n      file: docs/features/x/plan/tasks/TASK-0002-Open.md\n      status: doing\n", 1)
open(p, "w").write(t)
PY
g() { (cd "$R" && git -c user.email=t@t -c user.name=t "$@"); }
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
g init -q; g add -A; g commit -q -m base --no-verify; g tag v1.0
note docs/releases/REL-0001-v1.0.md 'type: "[[release]]"' 'id: REL-0001' 'status: released' 'tag: "v1.0"' 'date: 2026-09-10'
sed -i.bak 's/^status: doing$/status: done/' "$R/docs/features/x/plan/tasks/TASK-0003-Done-Later.md"; rm -f "$R/docs/features/x/plan/tasks/TASK-0003-Done-Later.md.bak"
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
g add -A; g commit -q -m release --no-verify
count() { find "$R/docs" -name '*.md' | wc -l | tr -d ' '; }
n_before="$(count)"

dry="$(cd "$R" && python3 tools/scripts/archive-notes.py 2>&1)"
check "the dry run names one task, one issue and one check, and moves nothing" \
  "$( { printf '%s' "$dry" | grep -qE '^archive-notes: would move [0-9]+ note\(s\) finished at v1.0 to docs/archive/ \(change [0-9]+, issue 1, task 1, test 1\)$' && [[ ! -d "$R/docs/archive" ]]; }; echo $?)" "$dry"

out="$(cd "$R" && python3 tools/scripts/archive-notes.py --apply 2>&1)"
A="$R/docs/archive"
check "a task, an issue, a change note and a retired check move, under the same sub-path" \
  "$( { [[ -f "$A/features/x/plan/tasks/TASK-0001-Shipped.md" && -f "$A/issues/ISS-0001-Fixed.md" && -f "$A/changes/CHG-20260901-A-Change.md" && -f "$A/tests/acceptance/TST-0001-Retired.md" ]]; }; echo $?)" "$out"
check "a task finished after the release stays" "$([[ -f "$R/docs/features/x/plan/tasks/TASK-0003-Done-Later.md" ]]; echo $?)"
check "an open task and a live test stay" "$([[ -f "$R/docs/features/x/plan/tasks/TASK-0002-Open.md" && -f "$R/docs/tests/TST-0002-Unit.md" ]]; echo $?)"
check "nothing is deleted" "$([[ "$(count)" == "$n_before" ]]; echo $?)" "$n_before -> $(count)"
check "git records the moves as renames" "$(g status --short | grep -q '^R  docs/features/x/plan/tasks/TASK-0001-Shipped.md -> docs/archive/'; echo $?)" "$(g status --short)"
check "the archived task leaves the snapshot; the open one stays" \
  "$( { ! grep -q '^    TASK-0001:' "$R/SNAPSHOT.yaml" && grep -q '^    TASK-0002:' "$R/SNAPSHOT.yaml"; }; echo $?)"

(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
v="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"; code=$?
check "the repo validates after the move, and the open task's link to the archived one resolves" "$code" "$v"

# A content finding about an archived note is not shown; a structural one is.
sed -i.bak 's/^command: "true"$/command: "true"\nstatus_note: x/' "$R/docs/tests/TST-0002-Unit.md"; rm -f "$R/docs/tests/TST-0002-Unit.md.bak"
sed -i.bak 's/^status: active$/status: failing/' "$R/docs/tests/TST-0002-Unit.md"; rm -f "$R/docs/tests/TST-0002-Unit.md.bak"
v="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "a content finding about an archived note is hidden and counted" \
  "$( { ! printf '%s' "$v" | grep -E '^(ERROR|WARN)' | grep -q 'TASK-0001' && printf '%s' "$v" | grep -q 'finding(s) about archived notes not shown'; }; echo $?)" "$v"
printf -- '---\ntype: "[[task]]"\nid: TASK-0001\ntitle: "a "broken" title"\nstatus: done\n---\n# Note\n' > "$A/features/x/plan/tasks/TASK-0001-Shipped.md"
v="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "a structural finding about an archived note still shows" "$(printf '%s' "$v" | grep -q 'NOTE-FRONTMATTER.*docs/archive/features/x/plan/tasks/TASK-0001'; echo $?)" "$v"

check "the template's .ignore keeps search out of the archive" "$(grep -qx 'docs/archive/' "$ROOT/.ignore"; echo $?)"

echo "test-archive-notes: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

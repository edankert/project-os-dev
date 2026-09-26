#!/usr/bin/env bash
# Reverse lists follow the child (project-os-dev ISS-0095, TASK-0172, ADR-0048).
# A task is written once, with its `parent:` and `phase:`; the feature's
# `tasks:`, the phase note's `tasks:`, the snapshot's two lists and the
# snapshot entry all follow from it. Fixture repo under a tempdir.
# Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1 PROJECT_OS_NO_CACHE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"
mkdir -p "$R/docs/features/a/plan/tasks" "$R/docs/features/b/plan/tasks" "$R/docs/issues" "$R/docs/phases" "$R/tools/scripts/hooks"
cp "$HERE/validate-docs.py" "$HERE/sync-snapshot.py" "$HERE/derive-lists.py" "$R/tools/scripts/"
cp "$HERE/hooks/pre-commit" "$R/tools/scripts/hooks/"
printf '#!/usr/bin/env bash\nexit 0\n' > "$R/tools/scripts/validate-docs.sh"; chmod +x "$R/tools/scripts/validate-docs.sh"

cat > "$R/SNAPSHOT.yaml" <<'YAML'
version: 1
updated: "2026-09-26T00:00Z"
template:
  replace_me: false
retention:
  derive_lists: true
counters:
  FEAT: 2
  ISS: 1
  PHASE: 1
  TASK: 6
focus:
  task: ""
  feature: ""
  phase: ""
  issue: ""
items:
  phases:
    PHASE-0001: { file: "docs/phases/PHASE-0001-One.md", status: active, tasks: [], features: [FEAT-0001] }
  features:
    FEAT-0001:
      file: docs/features/a/FEAT-0001-A.md
      status: doing
      tasks:
        - TASK-0001
        - TASK-0005
  issues:
    ISS-0001:
      file: docs/issues/ISS-0001-One.md
      status: open
  tasks:
    TASK-0001:
      file: docs/features/a/plan/tasks/TASK-0001-First.md
      status: done
      parent: FEAT-0001
YAML
note() { local path="$1"; shift; { printf -- '---\n'; printf '%s\n' "$@"; printf -- '---\n# Note\n'; } > "$R/$path"; }
note docs/phases/PHASE-0001-One.md 'type: "[[phase]]"' 'id: PHASE-0001' 'status: active' 'tasks: []' 'features: [FEAT-0001]'
note docs/features/a/FEAT-0001-A.md 'type: "[[feature]]"' 'id: FEAT-0001' 'status: doing' 'phase: "[[PHASE-0001]]"' 'tasks:' '  - "[[TASK-0001-First]]"' '  - "[[TASK-0004-Listed-Only]]"' '  - "[[TASK-0005-Moved-Away]]"' 'owner: user:x'
note docs/features/b/FEAT-0002-B.md 'type: "[[feature]]"' 'id: FEAT-0002' 'status: doing' 'tasks: []'
note docs/issues/ISS-0001-One.md 'type: "[[issue]]"' 'id: ISS-0001' 'status: open' 'parent: ""' 'related: []'
note docs/features/a/plan/tasks/TASK-0001-First.md 'type: "[[task]]"' 'id: TASK-0001' 'status: done' 'parent: "[[FEAT-0001]]"' 'phase: "[[PHASE-0001]]"'
note docs/features/a/plan/tasks/TASK-0004-Listed-Only.md 'type: "[[task]]"' 'id: TASK-0004' 'status: done' 'parent: ""'
note docs/features/b/plan/tasks/TASK-0005-Moved-Away.md 'type: "[[task]]"' 'id: TASK-0005' 'status: done' 'parent: "[[FEAT-0002]]"'
note docs/features/a/plan/tasks/TASK-0006-Fixes-The-Issue.md 'type: "[[task]]"' 'id: TASK-0006' 'status: done' 'parent: "[[FEAT-0001]]"'
sed -i.bak 's/^related: \[\]$/related: []\ntasks: ["[[TASK-0006]]"]/' "$R/docs/issues/ISS-0001-One.md"; rm -f "$R/docs/issues/ISS-0001-One.md.bak"
(cd "$R" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -q -m base)

# The new work is written in ONE place each: two task notes.
note docs/features/a/plan/tasks/TASK-0002-Second.md 'type: "[[task]]"' 'id: TASK-0002' 'status: backlog' 'parent: "[[FEAT-0001]]"' 'phase: "[[PHASE-0001]]"'
note docs/issues/TASK-0003-For-The-Issue.md 'type: "[[task]]"' 'id: TASK-0003' 'status: doing' 'parent: "[[ISS-0001]]"'
sed -i.bak 's/^  TASK: 6$/  TASK: 6/' "$R/SNAPSHOT.yaml"; rm -f "$R/SNAPSHOT.yaml.bak"
(cd "$R" && git add docs/features/a/plan/tasks/TASK-0002-Second.md docs/issues/TASK-0003-For-The-Issue.md)

dry="$(cd "$R" && python3 tools/scripts/derive-lists.py 2>&1)"
check "the dry run reports the conflict, naming both sides, and writes nothing" \
  "$( { printf '%s' "$dry" | grep -q 'CONFLICT TASK-0005 parent names FEAT-0002, but FEAT-0001 lists it' && [[ -z "$(cd "$R" && git status --porcelain --untracked-files=no | grep -v '^A ')" ]]; }; echo $?)" "$dry"

# Commit through the pre-commit hook: the sync writes, the hook stages.
hook="$(cd "$R" && bash tools/scripts/hooks/pre-commit 2>&1)"; code=$?
check "the pre-commit hook passes" "$code" "$hook"
fm() { sed -n '/^---$/,/^---$/p' "$R/$1"; }
snap() { cat "$R/SNAPSHOT.yaml"; }

f="$(fm docs/features/a/FEAT-0001-A.md)"
check "the feature's block list gains TASK-0002, in the list's slug form" "$(printf '%s' "$f" | grep -qx '  - "\[\[TASK-0002-Second\]\]"'; echo $?)" "$f"
check "a task written only in the feature's list is kept there" "$(printf '%s' "$f" | grep -q 'TASK-0004-Listed-Only'; echo $?)" "$f"
check "a task whose parent is another feature leaves this feature's list" "$(! printf '%s' "$f" | grep -q 'TASK-0005'; echo $?)" "$f"
check "the block list stays a block list, and the next field survives" "$(printf '%s' "$f" | grep -qx 'tasks:' && printf '%s' "$f" | grep -qx 'owner: user:x'; echo $?)" "$f"
t4="$(fm docs/features/a/plan/tasks/TASK-0004-Listed-Only.md)"
check "the listed-only fact moves onto the child: TASK-0004's parent is FEAT-0001" "$(printf '%s' "$t4" | grep -qx 'parent: "\[\[FEAT-0001\]\]"'; echo $?)" "$t4"
i="$(fm docs/issues/ISS-0001-One.md)"
check "the issue lists its own task and keeps the task that fixes it" "$(printf '%s' "$i" | grep -qx 'tasks: \["\[\[TASK-0006\]\]", "\[\[TASK-0003\]\]"\]'; echo $?)" "$i"
ph="$(fm docs/phases/PHASE-0001-One.md)"
check "the phase note's empty list gains its tasks" "$(printf '%s' "$ph" | grep -qx 'tasks: \["\[\[TASK-0001\]\]", "\[\[TASK-0002\]\]"\]'; echo $?)" "$ph"
check "the phase note's bare-id list keeps its form" "$(printf '%s' "$ph" | grep -qx 'features: \[FEAT-0001\]'; echo $?)" "$ph"
s="$(snap)"
check "the snapshot's feature list follows: TASK-0002 and TASK-0006 in, TASK-0005 out" "$(python3 -c 'import sys,yaml; d=yaml.safe_load(open(sys.argv[1])); sys.exit(0 if d["items"]["features"]["FEAT-0001"]["tasks"]==["TASK-0001","TASK-0002","TASK-0004","TASK-0006"] else 1)' "$R/SNAPSHOT.yaml" 2>/dev/null || python3 - "$R/SNAPSHOT.yaml" <<'PY'
import re, sys
t = open(sys.argv[1]).read()
block = t.split("    FEAT-0001:")[1].split("  issues:")[0]
sys.exit(0 if re.findall(r"- (TASK-\d+)", block) == ["TASK-0001", "TASK-0002", "TASK-0004", "TASK-0006"] else 1)
PY
echo $?)" "$s"
check "the snapshot's inline phase list follows, as bare ids" "$(printf '%s' "$s" | grep -q 'tasks: \[TASK-0001, TASK-0002\], features: \[FEAT-0001\]'; echo $?)" "$s"
check "a live task under a live entry gets a snapshot entry" "$(printf '%s' "$s" | grep -q '^    TASK-0002:$' && printf '%s' "$s" | grep -q '^    TASK-0003:$'; echo $?)" "$s"
staged="$(cd "$R" && git diff --cached --name-only)"
check "the hook staged every note the sync wrote" "$(for p in docs/features/a/FEAT-0001-A.md docs/issues/ISS-0001-One.md docs/phases/PHASE-0001-One.md docs/features/a/plan/tasks/TASK-0004-Listed-Only.md SNAPSHOT.yaml; do printf '%s\n' "$staged" | grep -qx "$p" || { echo 1; exit; }; done; echo 0)" "$staged"

o="$(cd "$R" && python3 tools/scripts/sync-snapshot.py --check 2>&1)"; code=$?
check "a second run finds nothing to change" "$code" "$o"

# Opted in, the validator leaves the lists to the sync: a new task its feature
# does not list yet is not a PARENT-BACKLINK finding.
note docs/features/a/plan/tasks/TASK-0008-Not-Yet-Listed.md 'type: "[[task]]"' 'id: TASK-0008' 'status: done' 'parent: "[[FEAT-0001]]"'
v="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "opted in: no PARENT-BACKLINK for a task the sync has not listed yet" "$(! printf '%s' "$v" | grep -q 'PARENT-BACKLINK'; echo $?)" "$v"
rm "$R/docs/features/a/plan/tasks/TASK-0008-Not-Yet-Listed.md"

# A repo that has not opted in: nothing is written, and the would-be changes are counted.
cd "$R" && git -c user.email=t@t -c user.name=t commit -q -m derived --no-verify; cd - >/dev/null
sed -i.bak '/^retention:$/,/^  derive_lists: true$/d' "$R/SNAPSHOT.yaml"; rm -f "$R/SNAPSHOT.yaml.bak"
note docs/features/a/plan/tasks/TASK-0007-Unlisted.md 'type: "[[task]]"' 'id: TASK-0007' 'status: done' 'parent: "[[FEAT-0001]]"'
sed -i.bak 's/^  TASK: 6$/  TASK: 7/' "$R/SNAPSHOT.yaml"; rm -f "$R/SNAPSHOT.yaml.bak"
before="$(cat "$R/docs/features/a/FEAT-0001-A.md")"
o="$(cd "$R" && python3 tools/scripts/sync-snapshot.py 2>&1)"
check "not opted in: the feature note is not written" "$([[ "$(cat "$R/docs/features/a/FEAT-0001-A.md")" == "$before" ]]; echo $?)"
v="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "not opted in: PARENT-BACKLINK still reports the unlisted task" "$(printf '%s' "$v" | grep -q 'PARENT-BACKLINK.*TASK-0007'; echo $?)" "$v"
check "not opted in: the run says how many lists would follow" "$(printf '%s' "$o" | grep -q 'reverse list(s) would follow their children; set retention.derive_lists'; echo $?)" "$o"

echo "test-derive-lists: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

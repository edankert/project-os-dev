#!/usr/bin/env bash
# FROZEN-EDIT (project-os-dev ISS-0097, TASK-0178, ADR-0048): a ticket that was
# finished when its release went out is a record, and an edit to it warns.
# A warning, never an error. Fixture git repo with a released tag.
# Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1 PROJECT_OS_NO_CACHE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"; rsync -a --exclude .git "$ROOT/" "$R/"
sed -i.bak 's/^  replace_me: true$/  replace_me: false/' "$R/SNAPSHOT.yaml"; rm -f "$R/SNAPSHOT.yaml.bak"
mkdir -p "$R/docs/features/x/plan/tasks" "$R/docs/issues" "$R/docs/changes" "$R/docs/releases"
note() { local path="$1"; shift; { printf -- '---\n'; printf '%s\n' "$@"; printf -- '---\n# Note\n\nBody.\n'; } > "$R/$path"; }
note docs/features/x/plan/tasks/TASK-0001-Shipped.md 'type: "[[task]]"' 'id: TASK-0001' 'status: done' 'parent: ""' 'review_verdict: changes-requested'
note docs/features/x/plan/tasks/TASK-0002-Still-Open.md 'type: "[[task]]"' 'id: TASK-0002' 'status: doing' 'parent: ""'
note docs/features/x/plan/tasks/TASK-0003-To-Be-Moved.md 'type: "[[task]]"' 'id: TASK-0003' 'status: done' 'parent: ""'
note docs/features/x/plan/tasks/TASK-0004-Replaced-Later.md 'type: "[[task]]"' 'id: TASK-0004' 'status: done' 'parent: ""'
note docs/issues/ISS-0001-Fixed.md 'type: "[[issue]]"' 'id: ISS-0001' 'status: fixed' 'tasks: []'
note docs/changes/CHG-20260901-A-Change.md 'type: "[[change]]"' 'id: CHG-20260901-A-Change' 'status: merged'
g() { (cd "$R" && git -c user.email=t@t -c user.name=t "$@"); }
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
g init -q; g add -A; g commit -q -m base --no-verify; g tag v1.0
note docs/releases/REL-0001-v1.0.md 'type: "[[release]]"' 'id: REL-0001' 'status: released' 'tag: "v1.0"' 'date: 2026-09-10'
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
g add -A; g commit -q -m release --no-verify

v() { (cd "$R" && python3 tools/scripts/validate-docs.py 2>&1); }
out="$(v)"
check "nothing edited: no FROZEN-EDIT" "$(! printf '%s' "$out" | grep -q FROZEN-EDIT; echo $?)" "$out"

printf '\nA later thought.\n' >> "$R/docs/features/x/plan/tasks/TASK-0001-Shipped.md"
printf '\nMore work.\n' >> "$R/docs/features/x/plan/tasks/TASK-0002-Still-Open.md"
printf '\nA correction.\n' >> "$R/docs/changes/CHG-20260901-A-Change.md"
sed -i.bak 's/^tasks: \[\]$/tasks: ["[[TASK-0001]]"]/' "$R/docs/issues/ISS-0001-Fixed.md"; rm -f "$R/docs/issues/ISS-0001-Fixed.md.bak"
# A new task supersedes a released one: the sync stamps the old note's
# pointer and status, and that is the tooling, not an edit.
note docs/features/x/plan/tasks/TASK-0005-Replacement.md 'type: "[[task]]"' 'id: TASK-0005' 'status: backlog' 'parent: ""' 'supersedes: "[[TASK-0004]]"'
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
g mv docs/features/x/plan/tasks/TASK-0003-To-Be-Moved.md docs/features/x/plan/tasks/TASK-0003-Moved.md
out="$(v)"; code=$?
check "an edit to a task that was done at the release warns, naming the release" \
  "$(printf '%s' "$out" | grep -q '^WARN  \[FROZEN-EDIT\] TASK-0001 was done when v1.0 was released'; echo $?)" "$out"
check "a change note is a record too" "$(printf '%s' "$out" | grep -q 'FROZEN-EDIT\] CHG-20260901-A-Change was merged'; echo $?)" "$out"
check "a task still open at the release is not frozen" "$(! printf '%s' "$out" | grep -q 'FROZEN-EDIT\] TASK-0002'; echo $?)" "$out"
check "a list the tools write is not an edit" "$(! printf '%s' "$out" | grep -q 'FROZEN-EDIT\] ISS-0001'; echo $?)" "$out"
check "the sync's supersession stamp on a released task is not an edit" \
  "$( { grep -q '^superseded_by: "\[\[TASK-0005\]\]"$' "$R/docs/features/x/plan/tasks/TASK-0004-Replaced-Later.md" && ! printf '%s' "$out" | grep -q 'FROZEN-EDIT\] TASK-0004'; }; echo $?)" "$out"
check "a rename (how the archive moves a note) is not an edit" "$(! printf '%s' "$out" | grep -q 'FROZEN-EDIT\] TASK-0003'; echo $?)" "$out"
check "it is a warning: the validator still passes" "$code" "$out"

# Staged and committed edits: the index is compared too, a commit clears it.
g add -A
out="$(v)"
check "a staged edit still warns (the pre-commit case)" "$(printf '%s' "$out" | grep -q 'FROZEN-EDIT\] TASK-0001'; echo $?)" "$out"
g commit -q -m edits --no-verify
out="$(v)"
check "once committed, the working tree has nothing to report" "$(! printf '%s' "$out" | grep -q FROZEN-EDIT; echo $?)" "$out"

# No release note: the newest git tag is the boundary.
rm "$R/docs/releases/REL-0001-v1.0.md"; (cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1); g add -A; g commit -q -m norel --no-verify
printf '\nAnother thought.\n' >> "$R/docs/features/x/plan/tasks/TASK-0001-Shipped.md"
out="$(v)"
check "with no release note, the newest tag is the boundary" "$(printf '%s' "$out" | grep -q 'FROZEN-EDIT\] TASK-0001 was done when v1.0'; echo $?)" "$out"

# TASK-0184: a note finished when the release went out draws no content
# finding; the same finding on work finished since is shown.
out="$(v)"
check "a released task's content finding (REVIEW-STALE) is hidden and counted" \
  "$( { ! printf '%s' "$out" | grep -E '^(ERROR|WARN)' | grep -v FROZEN-EDIT | grep -q 'TASK-0001' && printf '%s' "$out" | grep -q 'finding(s) about notes finished when v1.0 was released not shown'; }; echo $?)" "$out"
check "while FROZEN-EDIT on it still shows" "$(printf '%s' "$out" | grep -q 'FROZEN-EDIT\] TASK-0001'; echo $?)" "$out"
note docs/features/x/plan/tasks/TASK-0006-Done-Since.md 'type: "[[task]]"' 'id: TASK-0006' 'status: done' 'parent: ""' 'review_verdict: changes-requested'
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
out="$(v)"
check "the same finding on a task finished since the release is shown" "$(printf '%s' "$out" | grep -E '^(ERROR|WARN)' | grep -q 'REVIEW-STALE.*TASK-0006'; echo $?)" "$out"

echo "test-frozen-edit: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

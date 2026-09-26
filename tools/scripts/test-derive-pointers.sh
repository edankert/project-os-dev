#!/usr/bin/env bash
# Supersession is written once, on the new note (project-os-dev ISS-0096,
# TASK-0173, ADR-0048). The sync stamps the old note's back-pointer and status;
# the validator warns when work in flight links the old note; snapshot-query
# shows the pointer. Fixture repo under a tempdir. Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1 PROJECT_OS_NO_CACHE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"; mkdir -p "$R/docs/decisions" "$R/docs/designs" "$R/docs/features/x/plan/tasks" "$R/tools/scripts"
cp "$HERE/validate-docs.py" "$HERE/sync-snapshot.py" "$HERE/derive-pointers.py" "$HERE/snapshot-query.py" "$HERE/snapshot-slice.py" "$R/tools/scripts/"
cat > "$R/SNAPSHOT.yaml" <<'YAML'
version: 1
updated: "2026-09-26T00:00Z"
template:
  replace_me: false
counters:
  ADR: 7
  DES: 2
  TASK: 2
focus:
  task: ""
  feature: ""
  phase: ""
  issue: ""
items:
  decisions:
    ADR-0001:
      file: docs/decisions/ADR-0001-Old.md
      status: accepted
YAML
note() { local path="$1"; shift; { printf -- '---\n'; printf '%s\n' "$@"; printf -- '---\n# Note\n'; } > "$R/$path"; }
adr() { note "docs/decisions/$1.md" 'type: "[[adr]]"' "id: ${1%%-[A-Z]*}" "status: $2" "${@:3}"; }
adr ADR-0001-Old accepted 'supersedes: ""' 'superseded: ""'
adr ADR-0002-New accepted 'supersedes: "[[ADR-0001-Old]]"'
adr ADR-0003-Undecided proposed 'supersedes: "[[ADR-0004]]"'
adr ADR-0004-Still-Standing accepted
adr ADR-0005-Amends accepted 'amends: "[[ADR-0006]]"'
adr ADR-0006-Amended accepted
adr ADR-0007-Also-Amends accepted 'amends: ["[[ADR-0006]]"]'
note docs/designs/DES-0001-Old-Design.md 'type: "[[design]]"' 'id: DES-0001' 'status: accepted'
note docs/designs/DES-0002-New-Design.md 'type: "[[design]]"' 'id: DES-0002' 'status: accepted' 'supersedes: "[[DES-0001]]"'
note docs/features/x/plan/tasks/TASK-0001-Live.md 'type: "[[task]]"' 'id: TASK-0001' 'status: doing' 'related: ["[[ADR-0001]]", "[[ADR-0004]]"]'
note docs/features/x/plan/tasks/TASK-0002-Finished.md 'type: "[[task]]"' 'id: TASK-0002' 'status: done' 'related: ["[[ADR-0001]]"]'

out="$(cd "$R" && python3 tools/scripts/sync-snapshot.py --quiet 2>&1)"
fm() { sed -n '/^---$/,/^---$/p' "$R/$1"; }
a1="$(fm docs/decisions/ADR-0001-Old.md)"
check "the old ADR gets its pointer, written by the sync" "$(printf '%s' "$a1" | grep -qx 'superseded: "\[\[ADR-0002\]\]"'; echo $?)" "$a1"
check "and its status becomes superseded" "$(printf '%s' "$a1" | grep -qx 'status: superseded'; echo $?)" "$a1"
check "the snapshot entry follows the new status" "$(grep -A2 '^    ADR-0001:' "$R/SNAPSHOT.yaml" | grep -q 'status: superseded'; echo $?)" "$(cat "$R/SNAPSHOT.yaml")"
check "the sync names each note it wrote" "$(printf '%s' "$out" | grep -q '^sync-snapshot: wrote docs/decisions/ADR-0001-Old.md$'; echo $?)" "$out"
a4="$(fm docs/decisions/ADR-0004-Still-Standing.md)"
check "a proposed successor replaces nothing yet" "$( { printf '%s' "$a4" | grep -qx 'status: accepted' && ! printf '%s' "$a4" | grep -q 'superseded'; }; echo $?)" "$a4"
a6="$(fm docs/decisions/ADR-0006-Amended.md)"
check "an amended ADR lists both amenders and keeps its status" "$( { printf '%s' "$a6" | grep -qx 'amended_by: \["\[\[ADR-0005\]\]", "\[\[ADR-0007\]\]"\]' && printf '%s' "$a6" | grep -qx 'status: accepted'; }; echo $?)" "$a6"
d1="$(fm docs/designs/DES-0001-Old-Design.md)"
check "a design gets the field its type spells superseded_by" "$( { printf '%s' "$d1" | grep -qx 'superseded_by: "\[\[DES-0002\]\]"' && printf '%s' "$d1" | grep -qx 'status: superseded'; }; echo $?)" "$d1"

o="$(cd "$R" && python3 tools/scripts/sync-snapshot.py --check 2>&1)"; code=$?
check "a second run finds nothing to stamp" "$code" "$o"

v="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "work in flight that links the old ADR is warned" "$(printf '%s' "$v" | grep -q '^WARN  \[CITES-SUPERSEDED\] TASK-0001 links to ADR-0001 in `related:`, and ADR-0001 is superseded by ADR-0002'; echo $?)" "$v"
check "a finished task linking it is history, not warned; nor is a standing ADR" "$( { [[ $(printf '%s\n' "$v" | grep -c 'CITES-SUPERSEDED') -eq 1 ]]; }; echo $?)" "$v"

q="$(cd "$R" && python3 tools/scripts/snapshot-query.py ADR-0001 ADR-0006 2>&1)"
check "snapshot-query shows who replaced it and who amended it" "$( { printf '%s' "$q" | grep -q '^ADR-0001 superseded .* superseded-by=ADR-0002' && printf '%s' "$q" | grep -q '^ADR-0006 accepted .* amended-by=ADR-0005,ADR-0007'; }; echo $?)" "$q"

echo "test-derive-pointers: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

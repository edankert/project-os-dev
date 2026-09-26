#!/usr/bin/env bash
# migrate-ledger-fields.py (project-os-dev ISS-0099, TASK-0183): drop a field
# ADR-0037 moved into the ledger only where the ledger holds the same fact, and
# say why every other one stays. Fixture repo under a tempdir.
# Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1 PROJECT_OS_NO_CACHE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"; A="$R/docs/tests/acceptance"; mkdir -p "$A" "$R/docs/releases/ledgers"
cat > "$R/docs/releases/ledgers/WORKING-android.json" <<'JSON'
{"platform": "android", "entries": [
  {"check": "TST-0001", "mark": "pass", "date": "2026-08-30", "by": "migration", "method": "migration", "reason": "Backfilled from `mark: done`."},
  {"check": "TST-0002", "invalidated_by": "CHG-20260922-A-Change", "date": "2026-09-22", "reason": "The screen moved."}
], "evidence": []}
JSON
check_note() { local f="$A/$1-Fixture.md"; shift; { printf -- '---\ntype: "[[test]]"\nid: %s\ntitle: "A check"\nstatus: active\nlevel: acceptance\n' "$(basename "$f" -Fixture.md)"; printf '%s\n' "$@"; printf -- 'owner: user:x\n---\n\n# A check\n\n## Expect\n- It works.\n'; } > "$f"; }
check_note TST-0001 'mark: done' 'verdict_date: ""' 'verdict_reason: ""' 'invalidated_by: {}' 'automation: manual' 'covered_by: []' 'evidence: []'
check_note TST-0002 'mark: done' 'invalidated_by:' '  change: CHG-20260922-A-Change' 'automation: partial'
check_note TST-0003 'mark: todo' 'section: 3' '# A comment the author wrote.' 'covered_by:' '  - "[[FooTest]]"'
fm() { sed -n '/^---$/,/^---$/p' "$A/$1-Fixture.md"; }
before="$(cat "$A"/*.md)"

dry="$(python3 "$HERE/migrate-ledger-fields.py" --repo-root "$R" 2>&1)"
check "the dry run counts one note cleared and two partly, and writes nothing" \
  "$( { printf '%s' "$dry" | grep -q '^migrate-ledger-fields: would clear 1 of 3 notes' && printf '%s' "$dry" | grep -q '2 more lose some fields' && [[ "$(cat "$A"/*.md)" == "$before" ]]; }; echo $?)" "$dry"
check "the report says why a field stays" \
  "$( { printf '%s' "$dry" | grep -q 'the ledger has no `pass` for it' && printf '%s' "$dry" | grep -q 'automation `partial` and no automated verdict' && printf '%s' "$dry" | grep -q 'covered_by names'; }; echo $?)" "$dry"

python3 "$HERE/migrate-ledger-fields.py" --repo-root "$R" --apply >/dev/null
f1="$(fm TST-0001)"; f2="$(fm TST-0002)"; f3="$(fm TST-0003)"
check "a note whose ledger holds everything loses every moved field" \
  "$(! printf '%s' "$f1" | grep -qE '^(mark|verdict_date|verdict_reason|invalidated_by|automation|covered_by|evidence):'; echo $?)" "$f1"
check "and keeps the rest of its frontmatter and its body" \
  "$( { printf '%s' "$f1" | grep -qx 'owner: user:x' && printf '%s' "$f1" | grep -qx 'level: acceptance' && grep -q '^- It works\.$' "$A/TST-0001-Fixture.md"; }; echo $?)" "$f1"
check "an invalidation the ledger records is dropped, with its nested lines" \
  "$(! printf '%s' "$f2" | grep -qE '^(invalidated_by:|  change:)'; echo $?)" "$f2"
check "a verdict the ledger lacks, and a partial automation, stay" \
  "$( { printf '%s' "$f2" | grep -qx 'mark: done' && printf '%s' "$f2" | grep -qx 'automation: partial'; }; echo $?)" "$f2"
check "a todo mark and dead provenance go; a comment and a covered_by stay" \
  "$( { ! printf '%s' "$f3" | grep -qE '^(mark|section):' && printf '%s' "$f3" | grep -qx '# A comment the author wrote.' && printf '%s' "$f3" | grep -qx 'covered_by:' && printf '%s' "$f3" | grep -qx '  - "\[\[FooTest\]\]"'; }; echo $?)" "$f3"
again="$(python3 "$HERE/migrate-ledger-fields.py" --repo-root "$R" 2>&1)"
check "a second run clears nothing more" "$(printf '%s' "$again" | grep -q '^migrate-ledger-fields: would clear 0 of 2 notes'; echo $?)" "$again"

echo "test-migrate-ledger-fields: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

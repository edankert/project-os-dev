#!/usr/bin/env bash
# migrate-release-test-names.py (project-os-dev ADR-0050, TASK-0187): a
# consumer's own files move from the walk's names to the release test's, once.
# A fixture repo under a tempdir, committed in git so the moves can be seen as
# renames. Before the migration the validator names each old name's new one;
# after it, the validator reports none, and a second run changes nothing.
# Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1 PROJECT_OS_NO_CACHE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
MIGRATE="$HERE/migrate-release-test-names.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }
git_do() { git -C "$R" -c user.email=f@f -c user.name=fixture "$@" >/dev/null 2>&1; }

# A copy of the template's notes and scripts, so the validator runs as it does
# in a consumer, plus the files a consumer wrote under the old names.
R="$TMP/repo"; mkdir -p "$R/tools"
cp -R "$ROOT/SNAPSHOT.yaml" "$ROOT/docs" "$R/"
cp -R "$ROOT/tools/scripts" "$ROOT/tools/instructions" "$R/tools/"
A="$R/docs/tests/acceptance"; L="$R/docs/releases/ledgers"
mkdir -p "$A/walk" "$L"
cat > "$A/WALK.md" <<'MD'
---
type: "[[reference]]"
title: "Walk order"
status: active
---

# Walk order

### The bench

```yaml
surfaces: ["Bench"]
```
MD
cat > "$A/walk/the-bench.md" <<'MD'
---
type: "[[reference]]"
title: "The bench"
sitting: "The bench"
status: active
---

# The bench

## Steps

1. Open the bench. The prose may say sitting: and stays as written.
MD
cat > "$A/TST-0001-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0001
title: "A check"
status: active
level: acceptance
area: "Bench"
walk_readiness_for:
  app: {kind: decision, reason: "Waits for a product call."}
---

# A check

Its body mentions walk_readiness_for: and keeps it.
MD
# A key name at the start of a body line is prose, not frontmatter.
cat > "$A/TST-0002-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0002
title: "Another check"
status: active
level: acceptance
area: "Bench"
---

# Another check

walk_readiness_for: is how this note's author once wrote it, and it stays.
MD
printf -- '- Walk procedure: tools/skills/walk-procedure/SKILL.md\n- Other skill: tools/skills/close-out/SKILL.md\nSee tools/skills/walk-procedure/SKILL.md for procedures.\n' > "$R/CLAUDE.md"
cat > "$L/WORKING-app.json" <<'JSON'
{
  "platform": "app",
  "entries": [
    {"check": "TST-0001", "mark": "pass", "date": "2026-09-01", "by": "user:x", "method": "manual"},
    {"check": "TST-0001", "mark": "fail", "date": "2026-09-02", "by": "user:x", "method": "manual", "reason": "The note said \"mark\": fail."}
  ],
  "evidence": []
}
JSON
cat > "$L/REL-0001-app.json" <<'JSON'
{"platform": "app", "sealed": "2026-08-01", "release": "REL-0001", "entries": [
  {"check": "TST-0001", "mark": "pass", "date": "2026-08-01", "by": "user:x", "method": "manual"}
]}
JSON
sealed_before="$(shasum "$L/REL-0001-app.json")"
git -C "$R" init -q; git_do add -A; git_do commit -qm fixture

old_names() { python3 "$R/tools/scripts/validate-docs.py" --repo-root "$R" 2>&1 | grep '\[OLD-NAME\]'; }

# --- before: every old name is an error that names the new one
out="$(old_names)"
for want in 'WALK.md is the old name; it is now docs/tests/acceptance/RELEASE-TEST.md' \
            'acceptance/walk is the old name; it is now docs/tests/acceptance/release-test' \
            'TST-0001: `walk_readiness_for:` is the old name; it is now `readiness_for:`' \
            'CLAUDE.md lists tools/skills/walk-procedure/, the old name of tools/skills/release-test-procedure/'; do
  check "before migrating, the validator reports: $want" "$(printf '%s' "$out" | grep -qF "$want"; echo $?)" "$out"
done
check "each old-name error gives the migration command" \
  "$( [[ "$(printf '%s\n' "$out" | grep -c 'migrate-release-test-names.py --apply')" -eq 4 ]]; echo $?)" "$out"

# --- a dry run and --check change nothing
python3 "$MIGRATE" --repo-root "$R" >/dev/null
check "a dry run changes nothing" "$( [[ -z "$(git -C "$R" status --porcelain)" ]]; echo $?)" "$(git -C "$R" status --porcelain)"
python3 "$MIGRATE" --repo-root "$R" --check >/dev/null; code=$?
check "--check exits 1 while there is work" "$( [[ $code -eq 1 ]]; echo $?)" "exit $code"

# --- apply. The moves are read before anything is staged: `git mv` stages a
# rename itself, while a plain rename would show a deletion and a new file.
out="$(python3 "$MIGRATE" --repo-root "$R" --apply 2>&1)"; code=$?
check "--apply exits 0" "$code" "$out"
status="$(git -C "$R" status --porcelain)"
check "WALK.md moves to RELEASE-TEST.md as a git rename" \
  "$(printf '%s' "$status" | grep -qE '^R  docs/tests/acceptance/WALK\.md -> docs/tests/acceptance/RELEASE-TEST\.md'; echo $?)" "$status"
check "walk/ moves to release-test/ as a git rename" \
  "$(printf '%s' "$status" | grep -qE '^R. docs/tests/acceptance/walk/the-bench\.md -> docs/tests/acceptance/release-test/the-bench\.md'; echo $?)" "$status"
check "the old folder is gone" "$( [[ ! -e "$A/walk" ]]; echo $?)"
P="$A/release-test/the-bench.md"
check "the procedure's sitting: becomes section:" \
  "$( { grep -qx 'section: "The bench"' "$P" && ! grep -q '^sitting:' "$P"; }; echo $?)" "$(cat "$P")"
check "the procedure's prose is left as written" "$(grep -qF 'The prose may say sitting: and stays' "$P"; echo $?)"
C="$A/TST-0001-Fixture.md"
check "the check's walk_readiness_for: becomes readiness_for:" \
  "$( { grep -qx 'readiness_for:' "$C" && ! grep -q '^walk_readiness_for:' "$C"; }; echo $?)" "$(cat "$C")"
check "the check's body is left as written" "$(grep -qF 'Its body mentions walk_readiness_for: and keeps it.' "$C"; echo $?)"
check "a body line that starts with the old key is left as written" \
  "$(grep -qx 'walk_readiness_for: is how this note.s author once wrote it, and it stays.' "$A/TST-0002-Fixture.md"; echo $?)"
check "CLAUDE.md's skill line names the new skill" \
  "$( { grep -qx -- '- Release test procedure: tools/skills/release-test-procedure/SKILL.md' "$R/CLAUDE.md" && grep -qx -- '- Other skill: tools/skills/close-out/SKILL.md' "$R/CLAUDE.md"; }; echo $?)" "$(cat "$R/CLAUDE.md")"
check "and any other mention of the old skill path names the new one" \
  "$(grep -qx 'See tools/skills/release-test-procedure/SKILL.md for procedures.' "$R/CLAUDE.md"; echo $?)" "$(cat "$R/CLAUDE.md")"
ledger="$(python3 - "$L/WORKING-app.json" <<'PY'
import json, sys
text = open(sys.argv[1]).read()
d = json.loads(text)
ok = (all("result" in e and "mark" not in e for e in d["entries"])
      and [e["result"] for e in d["entries"]] == ["pass", "fail"]
      and d["entries"][1]["reason"] == 'The note said "mark": fail.'
      and len(text.splitlines()) == 8)
print("ok" if ok else text)
PY
)"
check "the open ledger's entries say result, one entry per line as before, reasons untouched" "$( [[ "$ledger" == ok ]]; echo $?)" "$ledger"
check "the sealed ledger is not rewritten" "$( [[ "$(shasum "$L/REL-0001-app.json")" == "$sealed_before" ]]; echo $?)"

# --- after: no old name is left, and the generator reads the moved files
out="$(old_names)"
check "after migrating, the validator reports no old name" "$( [[ -z "$out" ]]; echo $?)" "$out"
out="$(python3 "$R/tools/scripts/release-test.py" --check --platform app --repo-root "$R" 2>&1)"
check "the generator finds the section by its new key" "$(! printf '%s' "$out" | grep -qE 'no .section:|old name'; echo $?)" "$out"

# --- a second run changes nothing
git_do add -A; git_do commit -qm migrated
out="$(python3 "$MIGRATE" --repo-root "$R" --apply 2>&1)"; code=$?
check "a second run says there is nothing to do" "$( { [[ $code -eq 0 ]] && printf '%s' "$out" | grep -q 'nothing to do'; }; echo $?)" "$out"
check "and changes nothing" "$( [[ -z "$(git -C "$R" status --porcelain)" ]]; echo $?)" "$(git -C "$R" status --porcelain)"
python3 "$MIGRATE" --repo-root "$R" --check >/dev/null; code=$?
check "--check exits 0 once migrated" "$code"

# --- nothing is overwritten: both names present is a conflict
cp "$A/RELEASE-TEST.md" "$A/WALK.md"
printf 'local edit\n' >> "$A/WALK.md"
out="$(python3 "$MIGRATE" --repo-root "$R" --apply 2>&1)"; code=$?
check "WALK.md beside RELEASE-TEST.md is a conflict, exit 2" \
  "$( { [[ $code -eq 2 ]] && printf '%s' "$out" | grep -q 'CONFLICT  docs/tests/acceptance/WALK.md and docs/tests/acceptance/RELEASE-TEST.md both exist'; }; echo $?)" "exit $code: $out"
check "and neither file is touched" \
  "$( { [[ -f "$A/WALK.md" ]] && ! grep -q 'local edit' "$A/RELEASE-TEST.md"; }; echo $?)"

echo "test-migrate-release-test-names: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

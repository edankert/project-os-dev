#!/usr/bin/env bash
# The drift checks that replace sweep findings (project-os-dev ISS-0052,
# ISS-0053): FRONTMATTER-TYPO, INDEX-COVERAGE, FIELD-UNDOCUMENTED, CITATION.
# Each runs on a fresh copy of this template, which must be clean, with one
# defect put in. Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }
fresh() { rm -rf "$TMP/r"; mkdir -p "$TMP/r"; (cd "$ROOT" && tar cf - --exclude .git .) | (cd "$TMP/r" && tar xf -); }
run() { python3 "$TMP/r/tools/scripts/validate-docs.py" --repo-root "$TMP/r" 2>&1; }
edit() { python3 - "$@" <<'PY'
import sys; p, a, b = sys.argv[1:]; s = open(p).read(); assert s.count(a) == 1, ("not found", a); open(p, "w").write(s.replace(a, b, 1))
PY
}

fresh
out="$(run)"
check "a clean template trips none of the four checks" \
  "$(! printf '%s' "$out" | grep -qE 'FRONTMATTER-TYPO|INDEX-COVERAGE|FIELD-UNDOCUMENTED|\[CITATION\]'; echo $?)" "$(printf '%s' "$out" | grep -E 'TYPO|COVERAGE|UNDOC|CITATION')"

# FRONTMATTER-TYPO (ISS-0053): `elated:` silently drops a note's links.
mkdir -p "$TMP/r/docs/issues"
printf -- '---\ntype: "[[issue]]"\nid: ISS-0901\nstatus: open\nelated: ["[[ISS-0902]]"]\nfeature: "x"\nreview_note: "y"\n---\n# X\n' > "$TMP/r/docs/issues/ISS-0901-X.md"
out="$(run)"
check "a misspelt link field is an error naming the field it resembles" \
  "$(printf '%s' "$out" | grep -q 'ERROR \[FRONTMATTER-TYPO\] docs/issues/ISS-0901-X.md: frontmatter key `elated:` is defined nowhere and looks like `related:`'; echo $?)" "$out"
check "a singular field and a project field are not typos" \
  "$([[ $(printf '%s' "$out" | grep -c 'FRONTMATTER-TYPO') -eq 1 ]]; echo $?)" "$(printf '%s' "$out" | grep TYPO)"

# INDEX-COVERAGE: an index missing an entry of its directory.
fresh
edit "$TMP/r/docs/INDEX.md" '- Obsidian conventions: `../tools/instructions/OBSIDIAN.md`
' ''
mkdir -p "$TMP/r/tools/skills/zz-new-skill"
out="$(run)"
check "docs/INDEX.md without OBSIDIAN.md is reported" \
  "$(printf '%s' "$out" | grep -q 'INDEX-COVERAGE\] docs/INDEX.md lists 15 of the 16 entries in tools/instructions/; missing: OBSIDIAN.md'; echo $?)" "$out"
check "a skill no README lists is reported" \
  "$(printf '%s' "$out" | grep -q 'INDEX-COVERAGE\] tools/skills/README.md .*missing: zz-new-skill'; echo $?)" "$out"
check "INDEX-COVERAGE warns until its promotion date" \
  "$(printf '%s' "$out" | grep -q '^WARN  \[INDEX-COVERAGE\]'; echo $?)"

# FIELD-UNDOCUMENTED: a field the validator reads that SCHEMAS.md does not define.
fresh
edit "$TMP/r/docs/__templates__/SCHEMAS.md" '- (optional) `fixes` (list of links)' '- (optional) `repairs` (list of links)'
out="$(run)"
check "a field the validator reads and SCHEMAS.md drops is reported" \
  "$(printf '%s' "$out" | grep -q 'FIELD-UNDOCUMENTED\] the validator reads frontmatter field `fixes:`'; echo $?)" "$out"

# CITATION: a path or a section that resolves nowhere.
fresh
cat >> "$TMP/r/tools/skills/close-out/SKILL.md" <<'MD'

Test citations: see `tools/scripts/no-such-script.py`, and `../../instructions/QUALITY.md`, "A heading nobody wrote".
Not citations: `docs/changes/CHG-YYYYMMDD-Example.md`, `tools/scripts/report-YYYY.py`, `plan/PLAN.md`, and `../../instructions/QUALITY.md`, "Independent review (clean-context)".
MD
out="$(run)"
check "a cited path that resolves nowhere is reported" \
  "$(printf '%s' "$out" | grep -q 'CITATION\] tools/skills/close-out/SKILL.md:[0-9]* cites `tools/scripts/no-such-script.py`'; echo $?)" "$out"
check "a cited section the file lacks is reported" \
  "$(printf '%s' "$out" | grep -q 'A heading nobody wrote", and that file has no such heading'; echo $?)" "$out"
check "placeholders, context-relative paths and real sections are not reported" \
  "$([[ $(printf '%s' "$out" | grep -c '\[CITATION\]') -eq 2 ]]; echo $?)" "$(printf '%s' "$out" | grep CITATION)"

echo "test-drift-checks: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

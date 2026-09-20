#!/usr/bin/env bash
# The scaffolds under docs/__templates__ against the validator that reads them
# (project-os-dev ISS-0074).
#
# A scaffold is where a field is discovered. The validator gated on a feature's
# `acceptance:` and `design:` for months while `feature.md` offered neither, so
# the only repo whose features could use those gates was the one that had edited
# its own copy -- and it carried that edit as a sync exception, invisibly, with
# the four review fields accidentally duplicated inside it (2026-09-20).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
T="$ROOT/docs/__templates__"
failures=0
n=0
check() { # check <description> <command...>
  n=$((n + 1))
  if "${@:2}" >/dev/null 2>&1; then echo "  ok   $1"; else echo "  FAIL $1"; failures=$((failures + 1)); fi
}

# Every field the validator's feature gates read must exist in the scaffold,
# or an author never learns the gate is there.
check "feature.md offers the acceptance gate the validator reads" grep -q '^acceptance: ""' "$T/feature.md"
check "feature.md offers the design gate the validator reads" grep -q '^design: ""' "$T/feature.md"
check "feature.md offers the four review fields QUALITY.md asks for" bash -c '
  for f in reviewed_by review_date review_verdict review_round; do
    grep -q "^$f: \"\"" "'"$T"'/feature.md" || exit 1
  done'
check "the acceptance gate says what writes it" grep -q "never answers" "$T/feature.md"
check "the design gate says it warns rather than blocks" grep -q "never blocks" "$T/feature.md"

# The gates the scaffold advertises must be gates the validator actually runs.
V="$ROOT/tools/scripts/validate-docs.py"
check "the validator reads a feature's acceptance field" grep -q 'get("acceptance")' "$V"
check "the validator reads a feature's design field" grep -q "DESIGN-GATE" "$V"

# A duplicated key is a silent defect: YAML keeps one value and the other edit
# is lost. The cockpit's copy carried reviewed_by twice and nothing said so.
check "no scaffold declares the same frontmatter key twice" python3 - "$T" <<'PY'
import re, sys
from pathlib import Path
bad = []
for path in sorted(Path(sys.argv[1]).glob("*.md")):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        continue
    seen, dupes = set(), set()
    for line in m.group(1).splitlines():
        key = re.match(r"^([A-Za-z_][\w-]*):", line)
        if not key:
            continue
        if key.group(1) in seen:
            dupes.add(key.group(1))
        seen.add(key.group(1))
    if dupes:
        bad.append("%s: %s" % (path.name, ", ".join(sorted(dupes))))
if bad:
    print("duplicate frontmatter keys:\n  " + "\n  ".join(bad), file=sys.stderr)
    sys.exit(1)
PY

# Every scaffold must parse as frontmatter at all; the validator indexes them.
check "every scaffold has parseable frontmatter" python3 - "$T" <<'PY'
import re, sys
from pathlib import Path
bad = [p.name for p in sorted(Path(sys.argv[1]).glob("*.md"))
       if p.name != "README.md" and not re.match(r"^---\n.*?\n---", p.read_text(encoding="utf-8"), re.S)]
if bad:
    print("no frontmatter: %s" % ", ".join(bad), file=sys.stderr)
    sys.exit(1)
PY

echo "test-note-templates: $n assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

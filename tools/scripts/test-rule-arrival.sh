#!/usr/bin/env bash
# A content rule judges only notes still open when it arrived, and --changed
# shows only what the current change is about (project-os-dev ISS-0094,
# TASK-0179, ADR-0048). Fixture: a copy of the template in its own git repo,
# so REQ-BOXES "arrives" on the fixture's first commit, today.
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
mkdir -p "$R/docs/requirements"
req() { # req <id> <updated>: implemented, with one criterion never ticked
  cat > "$R/docs/requirements/$1-Fixture.md" <<MD
---
type: "[[requirement]]"
id: $1
title: "A requirement"
status: implemented
owner: unassigned
created: 2026-01-01
updated: $2
---

# A requirement

## Statement
The app does the thing.

## Acceptance Criteria

- [ ] The thing happens — evidence: none yet
MD
}
req REQ-0001 2026-01-01      # finished long before the rule arrived
req REQ-0002 2099-01-01      # touched after it arrived
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
(cd "$R" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -q -m base --no-verify)

out="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "a note finished before its rule arrived is not judged by it" "$(! printf '%s' "$out" | grep -q 'REQ-BOXES.*REQ-0001'; echo $?)" "$out"
check "a note touched after the rule arrived still is" "$(printf '%s' "$out" | grep -q 'REQ-BOXES.*REQ-0002'; echo $?)" "$out"
check "the hidden findings are counted, by rule" "$(printf '%s' "$out" | grep -q '^validate-docs: 1 finding(s) not shown, about notes finished before their rule arrived (REQ-BOXES 1)'; echo $?)" "$out"

# A structural check still covers the old note: frontmatter that is not YAML.
sed -i.bak 's/^title: "A requirement"$/title: "A "broken" requirement"/' "$R/docs/requirements/REQ-0001-Fixture.md"; rm -f "$R/docs/requirements/REQ-0001-Fixture.md.bak"
out="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "structural checks still judge the old note" "$(printf '%s' "$out" | grep -E '^(ERROR|WARN)' | grep -q 'NOTE-FRONTMATTER.*REQ-0001'; echo $?)" "$out"
(cd "$R" && git checkout -q -- docs/requirements/REQ-0001-Fixture.md)

# --changed: only the findings about files changed since HEAD, a count of the
# rest, and the exit status still counts every error.
mkdir -p "$R/docs/features/x/plan/tasks"
printf -- '---\ntype: "[[task]]"\nid: TASK-0001\nstatus: banana\nparent: ""\n---\n# Committed error\n' > "$R/docs/features/x/plan/tasks/TASK-0001-Old-Error.md"
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1; git add -A && git -c user.email=t@t -c user.name=t commit -q -m error --no-verify)
printf '\nEdited.\n' >> "$R/docs/requirements/REQ-0002-Fixture.md"
out="$(cd "$R" && python3 tools/scripts/validate-docs.py --changed 2>&1)"; code=$?
check "--changed shows the finding about the edited note" "$(printf '%s' "$out" | grep -q 'REQ-BOXES.*REQ-0002'; echo $?)" "$out"
check "--changed hides the finding about the unchanged note, and counts it" \
  "$( { ! printf '%s' "$out" | grep -q 'TASK-0001.*banana' && printf '%s' "$out" | grep -q 'error(s) and .* warning(s) about files not changed since HEAD are not shown'; }; echo $?)" "$out"
check "--changed still fails on the hidden error" "$([[ $code -eq 1 ]]; echo $?)" "exit $code: $out"

# The only error hidden: the exit status must still say FAIL.
(cd "$R" && git checkout -q -- docs/requirements/REQ-0002-Fixture.md)
printf '\nA note with nothing wrong.\n' >> "$R/README.md"
out="$(cd "$R" && python3 tools/scripts/validate-docs.py --changed 2>&1)"; code=$?
check "--changed with only a hidden error still exits 1 and prints no ERROR line" \
  "$( { [[ $code -eq 1 ]] && ! printf '%s' "$out" | grep -q '^ERROR'; }; echo $?)" "exit $code: $out"

# The judge itself: an open note is judged whatever its date, and a rule with
# no arrival date is never filtered.
j="$(python3 - "$HERE/validate-docs.py" <<'PY2'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("vd", sys.argv[1]); vd = importlib.util.module_from_spec(spec); spec.loader.exec_module(vd)
idx = {"REQ-0001": (Path("x"), {"type": "[[requirement]]", "status": "approved", "updated": "2026-01-01"}),
       "REQ-0002": (Path("y"), {"type": "[[requirement]]", "status": "implemented", "updated": "2026-01-01"})}
judge = vd.predates_rule(idx)
print(judge("REVIEW-STALE", "REQ-0001 is 'approved'"), judge("REVIEW-STALE", "REQ-0002 is x"), judge("LINK", "REQ-0002 x"))
PY2
)"
check "the judge keeps an open note and a rule with no arrival date" "$([[ "$j" == "False True False" ]]; echo $?)" "$j"

echo "test-rule-arrival: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

#!/usr/bin/env bash
# A feature filed for later needs its feature note only (project-os-dev
# ISS-0087, TASK-0174). The validator must accept a backlog feature in a
# planned phase with no plan, tasks, requirements or acceptance check, and must
# still ask for the check once the feature is done. Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1 PROJECT_OS_NO_CACHE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"; rsync -a --exclude .git "$ROOT/" "$R/"
sed -i.bak 's/^  replace_me: true$/  replace_me: false/' "$R/SNAPSHOT.yaml"; rm -f "$R/SNAPSHOT.yaml.bak"
mkdir -p "$R/docs/features/later" "$R/docs/phases"
python3 - "$R" <<'PY'
import sys
from pathlib import Path
r = Path(sys.argv[1])
t = (r / "docs/__templates__/feature.md").read_text()
t = t.replace("id: FEAT-0000", "id: FEAT-0001").replace('title: ""', 'title: "Later"', 1)
t = t.replace("phase:\n", 'phase: "[[PHASE-0001]]"\n', 1).replace('goal: ""', 'goal: "Build it when its phase starts"', 1)
t += "\n## Findings\n\nWhat is known.\n\n## Open questions\n\nWhat must be decided first.\n"
(r / "docs/features/later/FEAT-0001-Later.md").write_text(t)
p = (r / "docs/__templates__/phase.md").read_text().replace("id: PHASE-0000", "id: PHASE-0001")
(r / "docs/phases/PHASE-0001-Future.md").write_text(p)
# The repo holds an acceptance suite, so FEATURE-UNCOVERED is live here.
(r / "docs/tests/acceptance").mkdir(parents=True, exist_ok=True)
(r / "docs/tests/acceptance/TST-0001-Another-Check.md").write_text(
    '---\ntype: "[[test]]"\nid: TST-0001\ntitle: "Another check"\nstatus: active\nlevel: acceptance\n'
    'covers: ["[[FEAT-0002]]"]\n---\n# Another check\n')
PY
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
out="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"; code=$?
check "a parked feature with its note only validates" "$code" "$out"
check "nothing is asked of it: no finding names FEAT-0001" "$(! printf '%s' "$out" | grep -q 'FEAT-0001'; echo $?)" "$out"

sed -i.bak 's/^status: backlog$/status: done/; s/^updated: .*$/updated: 2099-01-01/' "$R/docs/features/later/FEAT-0001-Later.md"; rm -f "$R/docs/features/later/FEAT-0001-Later.md.bak"
(cd "$R" && python3 tools/scripts/sync-snapshot.py >/dev/null 2>&1)
out="$(cd "$R" && python3 tools/scripts/validate-docs.py 2>&1)"
check "the same feature, done, is asked for its acceptance check" "$(printf '%s' "$out" | grep -q 'FEATURE-UNCOVERED.*FEAT-0001'; echo $?)" "$out"

skill="$ROOT/tools/skills/feature-scaffold/SKILL.md"
check "the scaffold skill gives a feature filed for later its note only" \
  "$(grep -q '^## A feature filed for later gets its feature note only$' "$skill" && grep -q 'Write no requirements, plan, tasks, risk notes or acceptance check yet' "$skill"; echo $?)"

echo "test-parked-feature: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

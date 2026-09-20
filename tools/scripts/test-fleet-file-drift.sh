#!/usr/bin/env bash
# fleet-file-drift.py against built fixtures (project-os-dev TASK-0146).
# It must catch a template-owned file that differs, catch one that is missing,
# stay quiet about `merge` and `seed` paths, and say nothing about a repo that
# matches. The case that matters is the one that got through on 2026-09-20: a
# stale adapter hook while every other synced file was identical.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$(cd "$HERE/../.." && pwd)"
DRIFT="$HERE/fleet-file-drift.py"
failures=0
n=0
check() { # check <description> <command...>
  n=$((n + 1))
  if "${@:2}" >/dev/null 2>&1; then echo "  ok   $1"; else echo "  FAIL $1"; failures=$((failures + 1)); fi
}
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# A repo that matches the template on every template-owned path.
make_repo() { # make_repo <name>
  local repo="$TMP/$1"
  mkdir -p "$repo"
  printf 'version: 1\n' > "$repo/SNAPSHOT.yaml"
  python3 - "$TEMPLATE" "$repo" <<'PY'
import importlib.util, sys, shutil
from pathlib import Path
template, repo = Path(sys.argv[1]), Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("_s", template / "tools/scripts/sync-project-os.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
owners, excludes = m.parse_manifest(template / "tools/sync/MANIFEST.yaml")
for p in template.rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(template).as_posix()
    if rel.startswith(".git/") or m.excluded(rel, template, excludes):
        continue
    if m.ownership_for(rel, owners) == "template":
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, repo / rel)
PY
}

make_repo clean
out="$(python3 "$DRIFT" --repo "$TMP/clean" 2>&1)"; rc=$?
check "a repo that matches the template is clean" test "$rc" -eq 0
check "and it says so" grep -q "^ok " <<<"$out"

# The 2026-09-20 case: one adapter hook stale, everything else identical.
make_repo stalehook
printf '\n# a local edit nobody synced\n' >> "$TMP/stalehook/tools/adapters/claude-code/hooks/review-budget.py"
out="$(python3 "$DRIFT" --repo "$TMP/stalehook" 2>&1)"; rc=$?
check "a stale adapter hook is drift" test "$rc" -eq 1
check "and the hook is named" grep -q "stale   tools/adapters/claude-code/hooks/review-budget.py" <<<"$out"

# A template-owned file the repo never received.
make_repo missingfile
rm -f "$TMP/missingfile/tools/skills/independent-review/SKILL.md"
out="$(python3 "$DRIFT" --repo "$TMP/missingfile" 2>&1)"; rc=$?
check "a missing template-owned file is drift" test "$rc" -eq 1
check "and it is reported as missing, not stale" grep -q "missing tools/skills/independent-review/SKILL.md" <<<"$out"

# Paths the manifest does not call `template` are expected to differ.
make_repo projectpaths
mkdir -p "$TMP/projectpaths/docs/phases"
printf 'a phase this project owns\n' > "$TMP/projectpaths/docs/phases/PHASE-0001-Local.md"
printf 'a local brief\n' > "$TMP/projectpaths/LLM_BRIEF.md"
printf 'local schema notes\n' > "$TMP/projectpaths/docs/__templates__/SCHEMAS.md"
out="$(python3 "$DRIFT" --repo "$TMP/projectpaths" 2>&1)"; rc=$?
check "merge, seed and project paths are not drift" test "$rc" -eq 0
check "SCHEMAS.md (merge) is not reported" bash -c '! grep -q "SCHEMAS.md" <<<"$0"' "$out"

# Two drifted repos are both reported, and the summary counts them.
out="$(python3 "$DRIFT" --repo "$TMP/stalehook" --repo "$TMP/missingfile" 2>&1)"
check "every drifted repo is listed" test "$(grep -c '^DRIFT' <<<"$out")" -eq 2
check "the summary counts the drifted repos" grep -q "2 repo(s) checked, 2 drifted" <<<"$out"

out="$(python3 "$DRIFT" --repo "$TMP/clean" --quiet 2>&1)"
check "--quiet prints no line for a clean repo" bash -c '! grep -q "^ok " <<<"$0"' "$out"

echo "test-fleet-file-drift: $n assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

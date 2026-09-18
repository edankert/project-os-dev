#!/usr/bin/env bash
# sync-project-os.py against a throwaway template with history (project-os-dev
# TASK-0134): a stale copy is fast-forwarded, a real local edit is still
# reported, a merge-owned stale file is left alone, and keep_local survives.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC="$HERE/sync-project-os.py"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
failures=0; n=0
check() { n=$((n + 1)); if "${@:2}" >/dev/null 2>&1; then echo "  ok   $1"; else echo "  FAIL $1"; failures=$((failures + 1)); fi; }
U="$T/up"; D="$T/down"; mkdir -p "$U/tools/sync" "$U/tools/instructions" "$U/docs" "$D"
cd "$U" && git init -q && git config user.email t@t && git config user.name t
cat > tools/sync/MANIFEST.yaml <<'EOF'
version: 1
paths:
  "tools/": template
  "docs/PHASES.md": merge
  "LLM_BRIEF.md": seed
  ".github/workflows/": project
  ".github/workflows/validate-docs.yml": template
EOF
w() { mkdir -p "$(dirname "$1")"; printf '%s\n' "$2" > "$1"; }
w tools/instructions/A.md "A v1"; w tools/instructions/B.md "B v1"; w tools/instructions/C.md "C v1"; w docs/PHASES.md "P v1"; w .github/workflows/validate-docs.yml "W v1"; w LLM_BRIEF.md "REPLACE ME"
git add -A && git commit -qm v1
w tools/instructions/A.md "A v2"; w tools/instructions/B.md "B v2"; w docs/PHASES.md "P v2"; w .github/workflows/validate-docs.yml "W v2"
git add -A && git commit -qm v2; V2="$(git rev-parse HEAD)"
w tools/instructions/A.md "A v3"; w tools/instructions/B.md "B v3"; w tools/instructions/C.md "C v3"; w docs/PHASES.md "P v3"; w .github/workflows/validate-docs.yml "W v3"
git add -A && git commit -qm v3
# downstream: A stale at v1, B locally edited, C at the v2 baseline (v1 content, unchanged in v2),
# PHASES stale at v1 (merge-owned), a kept workflow that is an older template version
# (so without keep_local it would be fast-forwarded), a brief filled with project facts
mkdir -p "$D/tools/instructions" "$D/docs" "$D/.github/workflows"
w "$D/tools/instructions/A.md" "A v1"; w "$D/tools/instructions/B.md" "B local edit"; w "$D/tools/instructions/C.md" "C v1"
w "$D/docs/PHASES.md" "P v1"; w "$D/.github/workflows/validate-docs.yml" "W v1"; w "$D/.github/workflows/own-ci.yml" "our CI"; w "$D/LLM_BRIEF.md" "Name: down"
printf 'baseline_sha: "%s"\nkeep_local:\n  - ".github/workflows/validate-docs.yml"   # runs its own suite\n' "$V2" > "$D/.project-os-sync"
out="$(python3 "$SYNC" "$U" --repo-root "$D" 2>&1 || (cd "$D" && python3 "$SYNC" "$U" 2>&1))"
check "a stale copy (an older template version) is fast-forwarded" grep -qx "A v3" "$D/tools/instructions/A.md"
check "and reported as updated from an older version" grep -q "A.md (was an older template version)" <<<"$out"
check "a file at the baseline is fast-forwarded as before" grep -qx "C v3" "$D/tools/instructions/C.md"
check "a real local edit is left alone" grep -qx "B local edit" "$D/tools/instructions/B.md"
check "and still reported for a hand-merge" grep -q "B.md" <<<"$(grep -A20 'ACTION REQUIRED' <<<"$out")"
check "a merge-owned stale file is not overwritten" grep -qx "P v1" "$D/docs/PHASES.md"
check "a keep_local file is not touched, even when it is stale" grep -qx "W v1" "$D/.github/workflows/validate-docs.yml"
check "and is reported as kept" grep -q "KEPT  .github/workflows/validate-docs.yml" <<<"$out"
check "keep_local survives the state rewrite, comment included" grep -q 'runs its own suite' "$D/.project-os-sync"
check "the baseline moved to the template head" grep -q "$(git -C "$U" rev-parse HEAD)" "$D/.project-os-sync"
check "a project's own workflow is left alone" grep -qx "our CI" "$D/.github/workflows/own-ci.yml"
check "a seed file with project facts is left alone" grep -qx "Name: down" "$D/LLM_BRIEF.md"
echo "test-sync-stale: $n assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

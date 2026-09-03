#!/usr/bin/env bash
# TST-0006 (project-os-dev): the always-loaded instruction file is under its word budget,
# and the generated Cursor copy was regenerated to match.
#
# Budgets are project-os-dev REQ-0026's, amended 2026-09-03: LIFECYCLE.md under
# 1,000 words, .cursor/rules/lifecycle.mdc under 1,040 (the source budget plus its
# 40-word generated header). A short but stale copy would pass the size check, so
# the third assertion is generate-adapters --check. Paths resolve from this
# script's location, so the note's cross-repo command works from any repo root.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
failures=0
budget() { # budget <file> <max>
  local n
  n=$(wc -w < "$ROOT/$1" | tr -d ' ')
  if [[ "$n" -lt "$2" ]]; then
    echo "  ok   $1: $n words (< $2)"
  else
    echo "  FAIL $1: $n words, budget $2"
    failures=$((failures + 1))
  fi
}
budget tools/instructions/LIFECYCLE.md 1000
budget .cursor/rules/lifecycle.mdc 1040
if python3 "$ROOT/tools/scripts/generate-adapters.py" --repo-root "$ROOT" --check >/dev/null 2>&1; then
  echo "  ok   generated adapters are current"
else
  echo "  FAIL generated adapters are stale; the Cursor copy does not track its source"
  failures=$((failures + 1))
fi
echo "test-word-budgets: 3 assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

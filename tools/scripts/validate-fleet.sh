#!/usr/bin/env bash
set -uo pipefail

# Fleet-wide docs validation: run the project-os validator across every
# SNAPSHOT-bearing repo under a root directory and print an aggregate summary.
#
# Usage: validate-fleet.sh [fleet-root] [--verbose]
#   fleet-root defaults to the parent directory of this repo (e.g. ~/Dev/repos).
#   --verbose prints each repo's full error/warning lines, not just counts.
#
# Uses THIS repo's validate-docs.py for uniform semantics; per-repo STATUSES.md
# taxonomy overrides still apply (the validator loads them from each target repo).
# Exit 1 if any repo fails validation.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FLEET_ROOT="$DEFAULT_ROOT"
VERBOSE=0

for arg in "$@"; do
  case "$arg" in
    --verbose) VERBOSE=1 ;;
    -h|--help) sed -n '3,12p' "$0"; exit 0 ;;
    *) FLEET_ROOT="$arg" ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "validate-fleet: python3 is required; treat this as a setup error." >&2
  exit 2
fi

fail=0
total=0
printf "%-30s %-6s %7s %7s %8s\n" "repo" "result" "errors" "warns" "waivers"

for snap in "$FLEET_ROOT"/*/SNAPSHOT.yaml; do
  [[ -f "$snap" ]] || continue
  repo="$(dirname "$snap")"
  name="$(basename "$repo")"
  total=$((total + 1))
  out="$(python3 "$SCRIPT_DIR/validate-docs.py" --repo-root "$repo" 2>&1)"
  rc=$?
  errs="$(printf '%s\n' "$out" | grep -c '^ERROR' || true)"
  warns="$(printf '%s\n' "$out" | grep -c '^WARN' || true)"
  waivers="$(printf '%s\n' "$out" | grep -c 'VERIFY-WAIVED' || true)"
  if [[ $rc -eq 0 ]]; then
    result="OK"
  elif [[ $rc -eq 1 ]]; then
    result="FAIL"
    fail=1
  else
    result="ERROR"
    fail=1
  fi
  printf "%-30s %-6s %7s %7s %8s\n" "$name" "$result" "$errs" "$warns" "$waivers"
  if [[ $VERBOSE -eq 1 && ( $rc -ne 0 || $warns -gt 0 ) ]]; then
    printf '%s\n' "$out" | grep -E '^(ERROR|WARN)' | sed 's/^/    /'
  fi
done

if [[ $total -eq 0 ]]; then
  echo "validate-fleet: no SNAPSHOT.yaml found under $FLEET_ROOT/*/" >&2
  exit 2
fi

if [[ $fail -eq 0 ]]; then
  echo "validate-fleet: all $total repos OK"
else
  echo "validate-fleet: FAILURES present (see above)"
fi
exit $fail

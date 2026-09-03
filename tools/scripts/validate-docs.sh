#!/usr/bin/env bash
# Thin wrapper so hooks, pre-commit, and CI all call the validator the same way.
#
# With --as-committed it instead materialises HEAD into a temporary tree and runs
# the FULL CI step set there. See the comment on run_as_committed below for why
# that is a different question from "does the validator pass".
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "validate-docs: python3 is required but not found; skipping validation (treat as a setup error, not a pass)." >&2
  exit 2
fi

# Every check below reads the WORKING TREE. That is a different thing from what
# CI reads, which is the commit — and the gap is where a whole class of failure
# lives: a file that is present on disk but ignored, untracked, or simply not
# staged is invisible to every local check and absent in CI.
#
# Two instances of exactly that, both of which validated clean on the authoring
# machine and failed on a fresh clone:
#
#   - an unanchored `inbox/` in .gitignore swallowed docs/features/inbox/, so a
#     feature note, its plan and three tasks were missing from main for weeks;
#   - a stock `.claude/` ignore swallowed the generated adapters, so
#     `generate-adapters --check` could never pass in CI while passing locally
#     against the very files git was ignoring.
#
# `--as-committed` closes that gap by checking what a fresh clone would contain.
run_as_committed() {
  if ! command -v git >/dev/null 2>&1; then
    echo "validate-docs: --as-committed needs git" >&2
    exit 2
  fi
  # Not `local`: the EXIT trap fires after this function has returned, and a
  # local would be unbound by then (fatal under `set -u`).
  AS_COMMITTED_TMP="$(mktemp -d)"
  trap 'rm -rf "${AS_COMMITTED_TMP:-}"' EXIT
  local tmp="$AS_COMMITTED_TMP"
  git -C "$ROOT" archive HEAD | tar -x -C "$tmp"

  echo "validate-docs: checking HEAD as a fresh clone would see it ($tmp)"
  local status=0
  bash "$tmp/tools/scripts/validate-docs.sh" --repo-root "$tmp" || status=$?
  if [[ -f "$tmp/tools/scripts/sync-snapshot.py" ]]; then
    python3 "$tmp/tools/scripts/sync-snapshot.py" --repo-root "$tmp" --check || status=$?
  fi
  if [[ -f "$tmp/tools/scripts/generate-adapters.py" ]]; then
    python3 "$tmp/tools/scripts/generate-adapters.py" --repo-root "$tmp" --check || status=$?
  fi

  if [[ $status -ne 0 ]]; then
    echo "" >&2
    echo "validate-docs: HEAD fails checks that pass in your working tree." >&2
    echo "Something you can see is not in the commit — check .gitignore and 'git status --ignored'." >&2
  else
    echo "validate-docs: HEAD passes the full CI step set"
  fi
  return $status
}

for arg in "$@"; do
  if [[ "$arg" == "--as-committed" ]]; then
    run_as_committed
    exit $?
  fi
done

exec python3 "$SCRIPT_DIR/validate-docs.py" "$@"

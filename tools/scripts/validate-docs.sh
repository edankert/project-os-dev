#!/usr/bin/env bash
# Thin wrapper so hooks, pre-commit, and CI all call the validator the same way.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "validate-docs: python3 is required but not found; skipping validation (treat as a setup error, not a pass)." >&2
  exit 2
fi
exec python3 "$SCRIPT_DIR/validate-docs.py" "$@"

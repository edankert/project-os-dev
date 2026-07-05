#!/bin/bash
# HC-003: Verification Gate (blocking)
# Claude Code PreToolUse hook for Write/Edit tools.
#
# Denies status transitions to done/closed/verified while linked TST-* notes
# are not `status: passing`; asks when no test is linked at all. Logic lives in
# verification-gate.py (JSON/YAML resolution outgrew grep). Requires python3;
# fails open with a note if unavailable so a missing runtime never bricks edits.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "NOTE: verification gate skipped (python3 not found). Ensure linked TST-* notes are passing before terminal status transitions (HC-003)."
  exit 0
fi
exec python3 "$SCRIPT_DIR/verification-gate.py"

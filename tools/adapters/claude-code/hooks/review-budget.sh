#!/bin/bash
# Review budget (project-os-dev FEAT-0034, TASK-0128).
# Claude Code PreToolUse and PostToolUse hook, every tool.
#
# Stops the independent-reviewer subagent at its tool-call budget, so a review
# ends with a report instead of running on. Registered for every tool call of
# every session, so this wrapper exits at once unless the input comes from the
# reviewer: the Python half runs only for the reviewer's own calls.
# Fails open: a missing runtime must never block anyone's work.

INPUT="$(cat)"
case "$INPUT" in
  *'"independent-reviewer"'*) ;;
  *) exit 0 ;;
esac
command -v python3 >/dev/null 2>&1 || exit 0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
printf '%s' "$INPUT" | exec python3 "$SCRIPT_DIR/review-budget.py"

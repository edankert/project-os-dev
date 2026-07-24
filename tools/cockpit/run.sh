#!/usr/bin/env bash
# Bootstrap and run the synced project-os-cockpit against a docs path.
#
# Usage: tools/cockpit/run.sh <docs-path> [--bind 0.0.0.0] [--port 8765]
#
# This wrapper is project-os-owned (NOT synced from the canonical
# project-os-cockpit repo). It exists so downstream consumers have a
# stable entry point; the cockpit source itself lives alongside this
# file under tools/cockpit/{src,pyproject.toml,...} and is refreshed
# by the canonical repo's release-to-project-os.sh script.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/.venv"

# -------- bootstrap a project-local venv on first run -------------------

if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet -e "$HERE"
fi

# Re-install if pyproject changed since last install (cheap heuristic:
# pyproject.toml newer than the venv-stamp file).
STAMP="$VENV/.cockpit-stamp"
if [[ ! -f "$STAMP" || "$HERE/pyproject.toml" -nt "$STAMP" ]]; then
  "$VENV/bin/pip" install --quiet -e "$HERE"
  touch "$STAMP"
fi

# -------- run -----------------------------------------------------------

exec "$VENV/bin/python" -m project_os_cockpit "$@"

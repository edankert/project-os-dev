#!/usr/bin/env bash
set -euo pipefail

# Thin wrapper around the manifest-driven sync (tools/scripts/sync-project-os.py).
# Ownership rules live in tools/sync/MANIFEST.yaml (upstream copy is authoritative);
# divergence detection compares downstream files against the baseline template
# commit recorded in .project-os-sync. See tools/instructions/SYNCING.md.
#
# Usage: sync-project-os.sh <path-to-upstream-project-os> [--dry-run] [--force] [--baseline SHA]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: sync-project-os.sh <path-to-upstream-project-os> [--dry-run] [--force] [--baseline SHA]" >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "sync-project-os: python3 is required for the manifest-driven sync; treat this as a setup error." >&2
  exit 2
fi

SRC="$1"
shift
exec python3 "$SCRIPT_DIR/sync-project-os.py" "$SRC" --repo-root "$ROOT_DIR" "$@"

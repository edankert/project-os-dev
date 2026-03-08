#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: sync-project-os.sh <path-to-upstream-project-os> [--dry-run]

Sync template-owned project-os files from an upstream clone into this repo.
This does NOT touch SNAPSHOT.yaml or project-owned docs (features/issues/etc).

Examples:
  tools/scripts/sync-project-os.sh ../project-os
  tools/scripts/sync-project-os.sh /path/to/project-os --dry-run
USAGE
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 2
fi

SRC="$1"
DRY_RUN=""
if [[ $# -eq 2 ]]; then
  if [[ "$2" == "--dry-run" ]]; then
    DRY_RUN="--dry-run"
  else
    usage
    exit 2
  fi
fi

if [[ ! -d "$SRC" ]]; then
  echo "Source path not found: $SRC" >&2
  exit 1
fi

if [[ ! -f "$SRC/SNAPSHOT.yaml" ]]; then
  echo "Source does not look like project-os (missing SNAPSHOT.yaml): $SRC" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required but not found." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

copy_dir() {
  local rel="$1"
  rsync -a $DRY_RUN --exclude '.git' "$SRC/$rel/" "$ROOT_DIR/$rel/"
}

copy_file() {
  local rel="$1"
  rsync -a $DRY_RUN "$SRC/$rel" "$ROOT_DIR/$rel"
}

# Template-owned directories
copy_dir "tools/instructions"
copy_dir "tools/skills"
copy_dir "docs/__templates__"
copy_dir "docs/__bases__"

# Template-owned files
copy_file "docs/README.md"
copy_file "docs/INDEX.md"
copy_file "CONTEXT.md"

# Optional: only copy if present upstream
if [[ -f "$SRC/SECURITY.md" ]]; then
  copy_file "SECURITY.md"
fi
if [[ -f "$SRC/ROADMAP.md" ]]; then
  copy_file "ROADMAP.md"
fi

echo "Sync complete. Review changes and run tools/skills/snapshot-sync/SKILL.md."

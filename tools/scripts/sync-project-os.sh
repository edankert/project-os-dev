#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: sync-project-os.sh <path-to-upstream-project-os> [--dry-run]

Sync template-owned project-os files from an upstream clone into this repo.
This does NOT touch SNAPSHOT.yaml or project-owned docs under docs/features, docs/issues, docs/requirements, docs/tests, docs/changes, docs/decisions, docs/workflows, docs/reference, docs/research, or other project-specific docs subdirectories.

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

copy_file_if_missing() {
  local rel="$1"
  if [[ ! -f "$SRC/$rel" ]]; then
    return 0
  fi
  if [[ -e "$ROOT_DIR/$rel" ]]; then
    echo "Skipping existing project-owned file: $rel"
    return 0
  fi
  if [[ -n "$DRY_RUN" ]]; then
    echo "Would create parent directory and copy missing file: $rel"
    return 0
  fi
  mkdir -p "$(dirname "$ROOT_DIR/$rel")"
  rsync -a $DRY_RUN "$SRC/$rel" "$ROOT_DIR/$rel"
}

# Template-owned directories
copy_dir "tools/instructions"
copy_dir "tools/skills"
copy_dir "tools/agents"
copy_dir "tools/adapters"
if [[ -d "$SRC/tools/cockpit" ]]; then
  rsync -a $DRY_RUN --exclude '.venv' --exclude '*.egg-info' --exclude '__pycache__' "$SRC/tools/cockpit/" "$ROOT_DIR/tools/cockpit/"
fi
copy_dir "tools/scripts"
copy_dir "tools/cockpit"
copy_dir "docs/__templates__"
copy_dir "docs/__bases__"
if [[ -d "$SRC/docs/phases" ]]; then
  copy_dir "docs/phases"
fi

# Template-owned files
copy_file "docs/README.md"
copy_file "docs/INDEX.md"
if [[ -f "$SRC/docs/PHASES.md" ]]; then
  copy_file "docs/PHASES.md"
fi
copy_file "CONTEXT.md"
if [[ -f "$SRC/AGENTS.md" ]]; then
  copy_file "AGENTS.md"
fi
if [[ -f "$SRC/LLM_BRIEF.md" ]]; then
  copy_file "LLM_BRIEF.md"
fi

# Optional: only copy if present upstream
if [[ -f "$SRC/SECURITY.md" ]]; then
  copy_file "SECURITY.md"
fi
if [[ -f "$SRC/ROADMAP.md" ]]; then
  copy_file "ROADMAP.md"
fi

# Optional project-owned reference documentation area. Seed the README once,
# but never overwrite downstream reference/source packages.
copy_file_if_missing "docs/reference/README.md"

# Optional CI seed: wire the docs validator into CI once, but never overwrite
# downstream CI config.
copy_file_if_missing ".github/workflows/validate-docs.yml"

echo "Sync complete. Review changes and run tools/skills/snapshot-sync/SKILL.md."

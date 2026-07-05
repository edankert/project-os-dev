#!/usr/bin/env bash
# Install project-os git hooks into .git/hooks for this repo.
# Idempotent; preserves any existing non-project-os pre-commit hook by chaining it.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$ROOT/tools/scripts/hooks"
HOOKS_DST="$(git -C "$ROOT" rev-parse --git-path hooks)"

mkdir -p "$HOOKS_DST"
SRC="$HOOKS_SRC/pre-commit"
DST="$HOOKS_DST/pre-commit"

if [[ -f "$DST" ]] && ! grep -q "project-os pre-commit hook" "$DST"; then
  echo "Existing non-project-os pre-commit hook found; preserving it as pre-commit.local (it will be chained)."
  mv "$DST" "$HOOKS_DST/pre-commit.local"
fi

cp "$SRC" "$DST"
if [[ -f "$HOOKS_DST/pre-commit.local" ]] && ! grep -q "pre-commit.local" "$DST"; then
  cat >>"$DST" <<'CHAIN'

# Chain to the pre-existing local hook preserved by install-git-hooks.sh.
LOCAL_HOOK="$(git rev-parse --git-path hooks)/pre-commit.local"
if [[ -x "$LOCAL_HOOK" ]]; then
  "$LOCAL_HOOK" "$@" || exit 1
fi
CHAIN
fi
chmod +x "$DST"
echo "Installed pre-commit hook -> $DST"

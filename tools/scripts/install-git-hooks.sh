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

# pre-push: the filtered test commands run here, where the toolchain is warm.
# CI runs the declared ci.suite_command once instead of running them one by one.
PUSH_SRC="$HOOKS_SRC/pre-push"
PUSH_DST="$HOOKS_DST/pre-push"
if [[ -f "$PUSH_SRC" ]]; then
  if [[ -f "$PUSH_DST" ]] && ! grep -q "project-os pre-push hook" "$PUSH_DST"; then
    echo "Existing non-project-os pre-push hook found; preserving it as pre-push.local (it will be chained)."
    mv "$PUSH_DST" "$HOOKS_DST/pre-push.local"
  fi
  cp "$PUSH_SRC" "$PUSH_DST"
  if [[ -f "$HOOKS_DST/pre-push.local" ]] && ! grep -q "pre-push.local" "$PUSH_DST"; then
    cat >>"$PUSH_DST" <<'CHAIN'

# Chain to the pre-existing local hook preserved by install-git-hooks.sh.
LOCAL_HOOK="$(git rev-parse --git-path hooks)/pre-push.local"
if [[ -x "$LOCAL_HOOK" ]]; then
  "$LOCAL_HOOK" "$@" || exit 1
fi
CHAIN
  fi
  chmod +x "$PUSH_DST"
  echo "Installed pre-push hook -> $PUSH_DST"
fi


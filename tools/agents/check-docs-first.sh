#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [[ $# -gt 0 ]]; then
  BASE_REF="$1"
  CHANGED="$(git diff --name-only "${BASE_REF}"..HEAD)"
else
  TRACKED="$(git diff --name-only HEAD)"
  UNTRACKED="$(git ls-files --others --exclude-standard)"
  CHANGED="$(printf '%s\n%s\n' "$TRACKED" "$UNTRACKED" | sed '/^$/d' | sort -u)"
fi

if [[ -z "${CHANGED}" ]]; then
  echo "[OK] No changed files detected."
  exit 0
fi

is_doc_only_path() {
  local path="$1"
  case "$path" in
    docs/*|SNAPSHOT.yaml|AGENTS.md|LLM_BRIEF.md|tools/agents/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

CODE_CHANGED=0
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  if ! is_doc_only_path "$f"; then
    CODE_CHANGED=1
    break
  fi
done <<< "$CHANGED"

if [[ "$CODE_CHANGED" -eq 0 ]]; then
  echo "[OK] Docs-only change set."
  exit 0
fi

CHG_FILES="$(printf '%s\n' "$CHANGED" | grep '^docs/changes/CHG-.*\.md$' || true)"
if [[ -z "$CHG_FILES" ]]; then
  echo "[FAIL] Code changes detected but no docs/changes/CHG-*.md update found."
  exit 1
fi

if ! printf '%s\n' "$CHANGED" | grep -qx 'SNAPSHOT.yaml'; then
  echo "[FAIL] Code changes detected but SNAPSHOT.yaml was not updated."
  exit 1
fi

required_keys=(
  "features"
  "requirements"
  "tasks"
  "issues"
  "tests"
  "workflows"
  "decisions"
  "risks"
  "changes"
  "snapshot"
)

check_key_value() {
  local file="$1"
  local key="$2"
  local line
  line="$(grep -E "^- ${key}: " "$file" | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    echo "[FAIL] ${file}: missing checklist entry '- ${key}: ...'"
    return 1
  fi
  case "$line" in
    *": pending")
      echo "[FAIL] ${file}: '${key}' is still pending."
      return 1
      ;;
  esac
  return 0
}

FAILED=0
while IFS= read -r chg_file; do
  [[ -z "$chg_file" ]] && continue
  if [[ ! -f "$chg_file" ]]; then
    echo "[FAIL] Changed change-note file missing on disk: ${chg_file}"
    FAILED=1
    continue
  fi
  for key in "${required_keys[@]}"; do
    if ! check_key_value "$chg_file" "$key"; then
      FAILED=1
    fi
  done
done <<< "$CHG_FILES"

if [[ "$FAILED" -ne 0 ]]; then
  exit 1
fi

echo "[OK] Docs-first checks passed for code changes."

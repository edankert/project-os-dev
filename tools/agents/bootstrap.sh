#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SNAPSHOT="$REPO_ROOT/SNAPSHOT.yaml"

print_header() {
  printf '\n== %s ==\n' "$1"
}

kv_from_snapshot() {
  local key="$1"
  awk -F': ' -v k="$key" '$1 == k {print $2; exit}' "$SNAPSHOT" 2>/dev/null || true
}

print_header "Repository"
printf 'root: %s\n' "$REPO_ROOT"
printf 'branch: %s\n' "$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
printf 'head: %s\n' "$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"

print_header "Contract Files"
for f in CONTEXT.md docs/INDEX.md SNAPSHOT.yaml AGENTS.md LLM_BRIEF.md; do
  if [[ -f "$REPO_ROOT/$f" ]]; then
    printf '[OK] %s\n' "$f"
  else
    printf '[MISSING] %s\n' "$f"
  fi
done

print_header "Snapshot"
if [[ -f "$SNAPSHOT" ]]; then
  printf 'updated: %s\n' "$(kv_from_snapshot updated)"
  printf 'project: %s\n' "$(kv_from_snapshot '  name')"

  phase_focus="$(awk -F': ' '$1 == "  phase" {print $2; exit}' "$SNAPSHOT" | sed 's/#.*//' | tr -d "'\"" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  feature_focus="$(awk -F': ' '$1 == "  feature" {print $2; exit}' "$SNAPSHOT" | tr -d "'\"")"
  task_focus="$(awk -F': ' '$1 == "  task" {print $2; exit}' "$SNAPSHOT" | tr -d "'\"")"
  issue_focus="$(awk -F': ' '$1 == "  issue" {print $2; exit}' "$SNAPSHOT" | tr -d "'\"")"

  printf 'focus.phase: %s\n' "${phase_focus:-<none>}"
  printf 'focus.feature: %s\n' "${feature_focus:-<none>}"
  printf 'focus.task: %s\n' "${task_focus:-<none>}"
  printf 'focus.issue: %s\n' "${issue_focus:-<none>}"
else
  printf '[ERROR] SNAPSHOT.yaml not found\n'
fi

print_header "Working Tree"
git -C "$REPO_ROOT" status --short

print_header "Tooling"
if command -v python3.11 >/dev/null 2>&1; then
  printf '[OK] python3.11: %s\n' "$(python3.11 --version 2>/dev/null)"
else
  printf '[WARN] python3.11 not found\n'
fi

if command -v node >/dev/null 2>&1; then
  printf '[OK] node: %s\n' "$(node --version 2>/dev/null)"
else
  printf '[INFO] node not found\n'
fi

print_header "Recommended Next Step"
printf '1) Read AGENTS.md if not already done.\n'
printf '2) Use focus + status output to choose the first task.\n'

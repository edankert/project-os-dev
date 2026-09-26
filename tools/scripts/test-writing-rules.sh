#!/usr/bin/env bash
# WRITING.md rules 11 and 12 and the templates that point at them
# (project-os-dev ISS-0098 and ISS-0092, TASK-0176 and TASK-0177). A rule an
# agent never reads is not a rule, so the note templates an agent copies say
# where history goes. Exit 0 = every assertion holds.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }
W="$ROOT/tools/instructions/WRITING.md"

check "rule 11: a note says what is true now, and history goes to the change note" \
  "$(grep -q '^11\. \*\*A note says what is true now\.\*\*.*change note and the commit message' "$W"; echo $?)"
check "rule 12: link a rule by name instead of restating it" \
  "$(grep -q '^12\. \*\*Link a rule by name; do not restate it\.\*\*' "$W"; echo $?)"
check "the task template's Notes point at rule 11" \
  "$(grep -q 'WRITING.md, rule 11' "$ROOT/docs/__templates__/task.md"; echo $?)"
check "the feature template points at rule 11" \
  "$(grep -q 'WRITING.md, rule 11' "$ROOT/docs/__templates__/feature.md"; echo $?)"
check "the rules are numbered 1 to 12 with no gap" \
  "$([[ "$(grep -oE '^[0-9]+\. \*\*' "$W" | cut -d. -f1 | tr '\n' ' ')" == "1 2 3 4 5 6 7 8 9 10 11 12 " ]]; echo $?)"

# project-os-dev ISS-0102 (TASK-0182): search with the Grep tool or rg, which
# honour .gitignore and .ignore, and no instruction teaches `grep -r`.
check "LIFECYCLE says to search with the Grep tool or rg, not grep -r" \
  "$(grep -q '^- Search with the Grep tool or `rg`, not `grep -r`' "$ROOT/tools/instructions/LIFECYCLE.md"; echo $?)"
taught="$(cd "$ROOT" && grep -rnE 'grep -[a-zA-Z]*[rR]' tools/instructions tools/skills 2>/dev/null | grep -v 'not `grep -r`' || true)"
check "no instruction or skill tells an agent to run grep -r" "$([[ -z "$taught" ]]; echo $?)" "$taught"

echo "test-writing-rules: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

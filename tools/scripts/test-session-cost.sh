#!/usr/bin/env bash
# session-cost.py (project-os-dev ISS-0100, TASK-0168): opened, edited and
# surfaced notes, each classified by status at the commit the session started
# from. A fixture repo and a hand-written transcript; exit 0 = all hold.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

R="$TMP/repo"; mkdir -p "$R/docs/issues" "$R/docs/tasks"
note() { printf -- '---\nid: %s\nstatus: %s\n---\n# %s\n' "$2" "$3" "$2" > "$R/$1"; }
note docs/issues/ISS-0001-Old.md ISS-0001 fixed
note docs/issues/ISS-0002-Live.md ISS-0002 open
note docs/tasks/TASK-0001-Done.md TASK-0001 done
note docs/tasks/TASK-0002-Doing.md TASK-0002 doing
(cd "$R" && git init -q && git add . && GIT_COMMITTER_DATE="2026-09-01T10:00:00Z" git -c user.email=t@t -c user.name=t commit -q --date "2026-09-01T10:00:00Z" -m one)
# After the session starts, TASK-0002 is closed: it still counts as live, because
# the session saw it open.
note docs/tasks/TASK-0002-Doing.md TASK-0002 done
(cd "$R" && git add . && GIT_COMMITTER_DATE="2026-09-03T10:00:00Z" git -c user.email=t@t -c user.name=t commit -q --date "2026-09-03T10:00:00Z" -m two)

R="$(cd "$R" && pwd -P)"   # the script slugs the resolved path (/var is /private/var on macOS)
P="$TMP/projects/$(printf '%s' "$R" | tr '/' '-')"; mkdir -p "$P"
python3 - "$P/s1.jsonl" <<'PY'
import json, sys
recs = [
 {"timestamp": "2026-09-02T09:00:00Z", "message": {"content": [
   {"type": "tool_use", "id": "a", "name": "Read", "input": {"file_path": "/x/docs/issues/ISS-0001-Old.md"}},
   {"type": "tool_use", "id": "b", "name": "Bash", "input": {"command": "cat docs/tasks/TASK-0002-Doing.md"}},
   {"type": "tool_use", "id": "c", "name": "Edit", "input": {"file_path": "/x/docs/issues/ISS-0002-Live.md"}},
   {"type": "tool_use", "id": "d", "name": "Bash", "input": {"command": "sed -i '' 's/a/b/' docs/tasks/TASK-0001-Done.md"}},
   {"type": "tool_use", "id": "e", "name": "Grep", "input": {"pattern": "x"}},
   {"type": "tool_use", "id": "f", "name": "Bash", "input": {"command": "ls"}}]}},
 {"timestamp": "2026-09-02T09:01:00Z", "message": {"content": [
   {"type": "tool_result", "tool_use_id": "e", "content": "docs/issues/ISS-0001-Old.md\ndocs/tasks/TASK-0001-Done.md\ndocs/issues/ISS-0002-Live.md"},
   {"type": "tool_result", "tool_use_id": "f", "content": "docs/tasks/TASK-0002-Doing.md"}]}},
]
open(sys.argv[1], "w").write("\n".join(json.dumps(r) for r in recs) + "\n")
PY
out="$(python3 "$HERE/session-cost.py" --repo-root "$R" --projects-dir "$TMP/projects" --json)"
get() { python3 -c 'import json,sys; print(json.loads(sys.argv[1])["total"][sys.argv[2]])' "$out" "$1"; }
check "opened: Read and cat, 2 notes" "$([[ $(get opened) -eq 2 ]]; echo $?)" "$out"
check "opened finished: ISS-0001 only (TASK-0002 was open when the session began)" "$([[ $(get opened_finished) -eq 1 ]]; echo $?)" "$out"
check "edited: Edit and sed -i, 2 notes" "$([[ $(get edited) -eq 2 ]]; echo $?)" "$out"
check "edited finished: TASK-0001" "$([[ $(get edited_finished) -eq 1 ]]; echo $?)" "$out"
check "surfaced: only a search's result counts, not ls" "$([[ $(get surfaced) -eq 3 ]]; echo $?)" "$out"
check "surfaced finished: ISS-0001 and TASK-0001" "$([[ $(get surfaced_finished) -eq 2 ]]; echo $?)" "$out"
check "no transcript text in the output" "$(! printf '%s' "$out" | grep -q "sed -i"; echo $?)"

echo "test-session-cost: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

#!/usr/bin/env bash
# The Stop hooks sync the snapshot before they validate (project-os-dev
# ISS-0090, TASK-0171). In your-trainer a background planner created REQ-0221
# while counters.REQ was 220, and the main session's stop was blocked on
# COUNTER, an error the next commit's sync would have fixed by itself. Both the
# Claude Code hook and the Codex dispatch are run on a copy of this template.
# Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ -z "$2" || "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }

# setup <dir>: a copy of the template, adopted, with one issue note the snapshot
# counter does not yet cover.
setup() {
  rsync -a --exclude .git "$ROOT/" "$1/"
  # As a fresh clone of a repo with core.fileMode off has it (ISS-0103).
  chmod -x "$1/tools/scripts/validate-docs.sh"
  sed -i.bak 's/^  replace_me: true$/  replace_me: false/' "$1/SNAPSHOT.yaml"; rm -f "$1/SNAPSHOT.yaml.bak"
  printf -- '---\ntype: "[[issue]]"\nid: ISS-0001\naliases: ["ISS-0001"]\ntitle: "A new issue"\nstatus: triage\nowner: unassigned\ncreated: 2026-09-26\nupdated: 2026-09-26\n---\n# A new issue\n' > "$1/docs/issues/ISS-0001-A-New-Issue.md"
}
claude_stop() { printf '{"stop_hook_active": false}' | CLAUDE_PROJECT_DIR="$1" bash "$1/tools/adapters/claude-code/hooks/close-out-check.sh" 2>/dev/null; }
codex_stop() { printf '{"cwd": "%s", "hook_event_name": "Stop"}' "$1" | python3 "$1/tools/adapters/codex/hooks/dispatch.py" 2>/dev/null; }

A="$TMP/claude"; setup "$A"
before="$(bash "$A/tools/scripts/validate-docs.sh" --repo-root "$A" --quiet 2>&1)"; code=$?
check "the fixture reproduces the case: unsynced, the validator fails on COUNTER" \
  "$( { [[ $code -eq 1 ]] && printf '%s' "$before" | grep -q 'ERROR \[COUNTER\] ISS-0001'; }; echo $?)" "exit $code: $before"
out="$(claude_stop "$A")"
check "Claude Code: the stop goes through" "$([[ -z "$out" ]]; echo $?)" "$out"
check "Claude Code: the hook raised counters.ISS to 1" "$(grep -qE '^  ISS: 1$' "$A/SNAPSHOT.yaml"; echo $?)"

B="$TMP/codex"; setup "$B"
out="$(codex_stop "$B")"
check "Codex: the stop goes through" "$([[ -z "$out" || "$out" == "{}" ]]; echo $?)" "$out"
check "Codex: the hook raised counters.ISS to 1" "$(grep -qE '^  ISS: 1$' "$B/SNAPSHOT.yaml"; echo $?)"

# A real error still blocks: syncing fixes derived fields, not the notes.
C="$TMP/broken"; setup "$C"
sed -i.bak 's/^status: triage$/status: banana/' "$C/docs/issues/ISS-0001-A-New-Issue.md"; rm -f "$C/docs/issues/ISS-0001-A-New-Issue.md.bak"
out="$(claude_stop "$C")"
check "a note error the sync cannot fix still blocks the stop" "$(printf '%s' "$out" | grep -q '"decision": "block"'; echo $?)" "$out"

# The sync never writes over an edit made while it ran.
cat > "$TMP/race.py" <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("s", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
p = Path(sys.argv[2]); p.write_text("theirs\n")
ok = m.write_if_unchanged(p, "what the sync read\n", "the sync's result\n")
ok2 = m.write_if_unchanged(p, "theirs\n", "the sync's result\n")
print(ok, p.read_text().strip() if not ok2 else "", ok2, p.read_text().strip(), sorted(x.name for x in p.parent.iterdir()))
PY
mkdir -p "$TMP/race"
o="$(python3 "$TMP/race.py" "$HERE/sync-snapshot.py" "$TMP/race/SNAPSHOT.yaml")"
check "a snapshot changed since the sync read it is left alone; an unchanged one is replaced, with no temp file left" \
  "$([[ "$o" == "False  True the sync's result ['SNAPSHOT.yaml']" ]]; echo $?)" "$o"

echo "test-stop-sync: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

#!/usr/bin/env bash
# snapshot-query.py (project-os-dev TASK-0081): one lookup that answers the same
# way whatever the snapshot's YAML style, falls back to the note, and keeps a
# stable JSON shape. Fixtures under a tempdir. Exit 0 = every assertion holds.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
Q="$HERE/snapshot-query.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }
q() { python3 "$Q" --repo-root "$@"; }

head='version: 1
updated: "2026-09-25T00:00Z"
template:
  replace_me: false
focus:
  task: "TASK-0002"
  feature: "FEAT-0001"
  phase: ""
  issue: ""
items:'
mkdir -p "$TMP/block" "$TMP/inline"
cat > "$TMP/block/SNAPSHOT.yaml" <<YAML
$head
  features:
    FEAT-0001:
      file: docs/features/x/FEAT-0001-X.md
      status: doing
      phase: "[[PHASE-0001]]"
      tasks:
        - TASK-0002
        - TASK-0003
  tasks:
    TASK-0002:
      file: docs/features/x/plan/tasks/TASK-0002-X.md
      parent: FEAT-0001
      status: doing
      phase: "[[PHASE-0001]]"
    TASK-0003:
      file: docs/features/x/plan/tasks/TASK-0003-X.md
      parent: FEAT-0001
      status: backlog
YAML
cat > "$TMP/inline/SNAPSHOT.yaml" <<YAML
$head
  features:
    FEAT-0001: { file: "docs/features/x/FEAT-0001-X.md", status: doing, phase: "[[PHASE-0001]]", tasks: [TASK-0002, TASK-0003] }
  tasks:
    TASK-0002: { file: "docs/features/x/plan/tasks/TASK-0002-X.md", title: "Parse, then: check", parent: FEAT-0001, status: doing, phase: "[[PHASE-0001]]" }
    TASK-0003: { file: "docs/features/x/plan/tasks/TASK-0003-X.md", parent: FEAT-0001, status: backlog }
YAML

# The defect: grep answers differently by style. The query must not.
b="$(q "$TMP/block" TASK-0002)"; i="$(q "$TMP/inline" TASK-0002)"
check "block style: status, file, parent and phase" "$([[ "$b" == "TASK-0002 doing docs/features/x/plan/tasks/TASK-0002-X.md parent=FEAT-0001 phase=PHASE-0001" ]]; echo $?)" "$b"
check "inline style gives the identical line" "$([[ "$b" == "$i" ]]; echo $?)" "block: $b | inline: $i"
bj="$(q "$TMP/block" --json FEAT-0001)"; ij="$(q "$TMP/inline" --json FEAT-0001)"
check "--json is identical across styles, block lists included" "$([[ "$bj" == "$ij" ]]; echo $?)" "$bj // $ij"
check "--json carries version 1 and the task links" "$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if d["version"]==1 and d["items"][0]["links"]["tasks"]==["TASK-0002","TASK-0003"] else 1)' "$bj"; echo $?)" "$bj"

# Filters and the in-flight list.
check "--status filters" "$([[ "$(q "$TMP/block" --status backlog | cut -d' ' -f1)" == "TASK-0003" ]]; echo $?)"
check "--collection with --status combine" "$([[ "$(q "$TMP/inline" --collection features --status doing | cut -d' ' -f1)" == "FEAT-0001" ]]; echo $?)"
check "--in-flight lists doing items, not backlog" "$(o="$(q "$TMP/block" --in-flight)"; printf '%s' "$o" | grep -q '^TASK-0002 ' && ! printf '%s' "$o" | grep -q '^TASK-0003 '; echo $?)"

# A pruned item is still real: the note answers.
mkdir -p "$TMP/block/docs/issues"
printf -- '---\ntype: "[[issue]]"\nid: ISS-0009\nstatus: fixed\nphase: "[[PHASE-0001]]"\n---\n# Old\n' > "$TMP/block/docs/issues/ISS-0009-Old.md"
o="$(q "$TMP/block" ISS-0009)"; code=$?
check "an id not in the snapshot falls back to its note" "$( { [[ $code -eq 0 ]] && printf '%s' "$o" | grep -q '^ISS-0009 fixed docs/issues/ISS-0009-Old.md phase=PHASE-0001 (from the note'; }; echo $?)" "$o"
check "--json marks a note answer as source note" "$(q "$TMP/block" --json ISS-0009 | grep -q '"source": "note"'; echo $?)"

# Unknown id and usage.
o="$(q "$TMP/block" TASK-0999 2>&1)"; code=$?
check "an unknown id exits 1 and says where it looked" "$( { [[ $code -eq 1 ]] && printf '%s' "$o" | grep -q 'not in SNAPSHOT.yaml and no note named TASK-0999'; }; echo $?)" "exit $code: $o"
python3 "$Q" --repo-root "$TMP/block" >/dev/null 2>&1; code=$?
check "no id and no filter is a usage error" "$([[ $code -eq 2 ]]; echo $?)" "exit $code"

# The session-start orientation advertises it, and only where it exists.
check "without the script, the orientation does not name it" "$(! python3 "$HERE/snapshot-slice.py" "$TMP/block" | grep -q 'snapshot-query.py'; echo $?)"
mkdir -p "$TMP/block/tools/scripts"; cp "$Q" "$TMP/block/tools/scripts/"
check "with the script, the orientation names it" "$(python3 "$HERE/snapshot-slice.py" "$TMP/block" | grep -q 'snapshot-query.py <ID>'; echo $?)"

# FEAT-0021 review, 2026-09-25: a change note's id carries its slug.
for style in block inline; do
  f="$TMP/$style/SNAPSHOT.yaml"
  if [[ $style == block ]]; then
    printf '  changes:\n    CHG-20260925-First-Change:\n      file: docs/changes/CHG-20260925-First-Change.md\n      status: merged\n    CHG-20260925-Second-Change:\n      file: docs/changes/CHG-20260925-Second-Change.md\n      status: merged\n    CHG-20260924-Only-One:\n      file: docs/changes/CHG-20260924-Only-One.md\n      status: merged\n    CHG-20260531e-Lettered:\n      file: docs/changes/CHG-20260531e-Lettered.md\n      status: merged\n' >> "$f"
  else
    printf '  changes:\n    CHG-20260925-First-Change: { file: "docs/changes/CHG-20260925-First-Change.md", status: merged }\n    CHG-20260925-Second-Change: { file: "docs/changes/CHG-20260925-Second-Change.md", status: merged }\n    CHG-20260924-Only-One: { file: "docs/changes/CHG-20260924-Only-One.md", status: merged }\n    CHG-20260531e-Lettered: { file: "docs/changes/CHG-20260531e-Lettered.md", status: merged }\n' >> "$f"
  fi
done
b="$(q "$TMP/block" CHG-20260925-Second-Change)"; i="$(q "$TMP/inline" CHG-20260925-Second-Change)"
check "a change is found by its full id, from the snapshot" "$([[ "$b" == "CHG-20260925-Second-Change merged docs/changes/CHG-20260925-Second-Change.md" ]]; echo $?)" "$b"
check "and the same in inline style" "$([[ "$b" == "$i" ]]; echo $?)" "$i"
o="$(q "$TMP/block" CHG-20260925 2>&1)"; code=$?
check "a date two changes share is ambiguous, not a guess" "$( { [[ $code -eq 1 ]] && printf '%s' "$o" | grep -q 'ambiguous, 2 items match: CHG-20260925-First-Change, CHG-20260925-Second-Change'; }; echo $?)" "exit $code: $o"
check "a date one change has is answered" "$(q "$TMP/block" CHG-20260924 | grep -q '^CHG-20260924-Only-One merged'; echo $?)"
check "--collection changes lists them" "$([[ $(q "$TMP/inline" --collection changes | wc -l | tr -d ' ') -eq 4 ]]; echo $?)"
check "a change whose date carries a letter is found" "$(q "$TMP/block" CHG-20260531e-Lettered | grep -q '^CHG-20260531e-Lettered merged'; echo $?)"

# Lists: at the key's own indent, and with a quoted comma.
mkdir -p "$TMP/lists"
cat > "$TMP/lists/SNAPSHOT.yaml" <<'YAML'
version: 1
items:
  tasks:
    TASK-0005:
      status: doing
      depends:
      - TASK-0006
      - TASK-0007
      related: ["TASK-0008", "a note, with a comma"]
      phase:
      note: "a \"quoted\" word, the block\u2019s own, and it''s"
      title: 'it''s single'
YAML
o="$(q "$TMP/lists" --json TASK-0005)"
check "a block list at the key's own indent is read" "$(python3 -c 'import json,sys; d=json.loads(sys.argv[1])["items"][0]; sys.exit(0 if d["links"]["depends"]==["TASK-0006","TASK-0007"] else 1)' "$o"; echo $?)" "$o"
check "a quoted comma does not split an inline list" "$(python3 - "$TMP/lists/SNAPSHOT.yaml" "$HERE/snapshot-slice.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("s", sys.argv[2]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
fields = m.parse(open(sys.argv[1]).read())[3]["tasks"]["TASK-0005"]
sys.exit(0 if fields["related"] == ["TASK-0008", "a note, with a comma"] and fields["phase"] == "" else 1)
PY
echo $?)"
cat > "$TMP/esc.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("s", sys.argv[2]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
fields = m.parse(open(sys.argv[1]).read())[3]["tasks"]["TASK-0005"]
want_note = 'a "quoted" word, the block’s own, and it' + "''" + 's'
sys.exit(0 if fields["note"] == want_note and fields["title"] == "it's single" else 1)
PY
check "quoted values have their escapes read, as YAML does" "$(python3 "$TMP/esc.py" "$TMP/lists/SNAPSHOT.yaml" "$HERE/snapshot-slice.py"; echo $?)"

o="$(python3 "$Q" --repo-root "$TMP/block" TASK-0002 --status doing 2>&1)"; code=$?
check "ids and a filter together are a usage error, not a silent drop" "$( { [[ $code -eq 2 ]] && printf '%s' "$o" | grep -q 'not both'; }; echo $?)" "exit $code: $o"

echo "test-snapshot-query: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

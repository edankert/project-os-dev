#!/usr/bin/env bash
# TST-0007 (project-os-dev): the hooks emit what their contracts say they emit.
#
# Three Claude Code hooks read a snapshot and print a message, so they are
# tested directly against fixture repos under a tempdir, never this repo:
#   HC-006 close-out-check.sh   (Stop)             names two actions, not "acknowledge",
#                                                    and quotes the task's open boxes
#   HC-002 snapshot-freshness.sh (SessionStart)     serves the orientation slice
#   HC-008 model-routing-hint.sh (UserPromptSubmit) serves focus state; recommends the
#                                                    planner and the reviewer selectively;
#                                                    stays within a size bound
#   HC-001 document-first-gate.sh (PreToolUse)      allows paths outside every project-os
#                                                    repo (project-os-dev ISS-0003)
# Every hook file is also checked for the executable bit, which the assertions
# below cannot detect on their own (project-os-dev ISS-0055), and the Stop
# hook's write test is exercised against a session marker (ISS-0056).
# Paths resolve from this script's location. Exit 0 = every assertion holds.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
HOOKS="$ROOT/tools/adapters/claude-code/hooks"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

assertions=0; failures=0
check() { # check <name> <ok:0|1> [detail]
  assertions=$((assertions + 1))
  if [[ "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi
}
has()    { printf '%s' "$1" | grep -qF -- "$2"; }
hasnot() { ! printf '%s' "$1" | grep -qF -- "$2"; }

# fixture <dir> <task-id> <task-status> <feature-id> <feature-status> <issue-id>
fixture() {
  mkdir -p "$1"
  cat > "$1/SNAPSHOT.yaml" <<YAML
version: 1
updated: "2026-09-03T00:00Z"
template:
  replace_me: false
counters:
  TASK: 1
focus:
  task: "$2"
  feature: "$4"
  phase: "PHASE-0001"
  issue: "$6"
items:
  features:
    FEAT-0001:
      file: docs/features/x/FEAT-0001.md
      status: $5
  tasks:
    TASK-0001:
      file: docs/features/x/plan/tasks/TASK-0001.md
      status: $3
  issues:
    ISS-0001:
      file: docs/issues/ISS-0001.md
      status: open
YAML
}
stop_hook() { printf '{"stop_hook_active": %s}' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/close-out-check.sh" 2>/dev/null; }
hint()      { printf '{"prompt":"x"}' | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/model-routing-hint.sh" 2>/dev/null; }
gate()      { printf '{"tool_input":{"file_path":"%s"}}' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/document-first-gate.sh" 2>/dev/null; }
# vgate <project-dir> <file-path> <new-content>
vgate()     { python3 -c 'import json,sys; print(json.dumps({"tool_input":{"file_path":sys.argv[1],"new_string":sys.argv[2]},"cwd":sys.argv[3]}))' "$2" "$3" "$1" | python3 "$HOOKS/verification-gate.py" 2>/dev/null; }
# tstnote <project-dir> <id> <status> [extra frontmatter line]
tstnote()   { mkdir -p "$1/docs/tests"; { printf -- '---\nid: %s\nstatus: %s\n' "$2" "$3"; [ -n "$4" ] && printf '%s\n' "$4"; printf -- '---\n'; } > "$1/docs/tests/$2-x.md"; }

# -- HC-006: the Stop hook names two actions ---------------------------------
fixture "$TMP/doing" TASK-0001 doing FEAT-0001 doing ""
out="$(stop_hook "$TMP/doing" false)"
check "stop hook blocks while focus.task is set" "$(has "$out" '"decision": "block"'; echo $?)"
check "stop hook, work complete: set the status and clear focus" "$(has "$out" 'set the task status to done and clear focus now'; echo $?)"
check "stop hook, mid-flight: write the handoff, then stop" "$( { has "$out" 'write the handoff' && has "$out" 'then stop'; }; echo $?)"
check "stop hook no longer says acknowledge to continue" "$(hasnot "$out" 'acknowledge'; echo $?)"
out2="$(stop_hook "$TMP/doing" true)"
check "the loop guard lets the second stop through" "$([[ -z "$out2" ]]; echo $?)" "got: $out2"
fixture "$TMP/issue" "" doing FEAT-0001 doing ISS-0001
out="$(stop_hook "$TMP/issue" false)"
check "stop hook, issue in focus: names the two actions" "$( { has "$out" 'set its status to fixed and clear focus now' && has "$out" 'write the handoff'; }; echo $?)"

# -- HC-008: the hint serves state ------------------------------------------
fixture "$TMP/empty" "" done FEAT-0001 done ""
sed -i.bak 's/^  feature: "FEAT-0001"/  feature: ""/' "$TMP/empty/SNAPSHOT.yaml"; rm -f "$TMP/empty/SNAPSHOT.yaml.bak"
h_empty="$(hint "$TMP/empty")"
check "hint, empty focus: states that nothing is in flight" "$(has "$h_empty" 'nothing in flight'; echo $?)" "$h_empty"
check "hint, empty focus: does not instruct delegation" "$( { hasnot "$h_empty" 'delegate preflight' && hasnot "$h_empty" 'before coding'; }; echo $?)" "$h_empty"
check "hint, empty focus: still says every change gets its note first" "$(has "$h_empty" 'note written here before the code'; echo $?)" "$h_empty"

fixture "$TMP/planning" TASK-0001 backlog FEAT-0001 doing ""
h_plan="$(hint "$TMP/planning")"
check "hint, planning state: names the item, its status and its phase" "$( { has "$h_plan" "TASK-0001 is 'backlog'" && has "$h_plan" 'PHASE-0001'; }; echo $?)" "$h_plan"
check "hint, planning state: recommends the planner for a multi-item scaffold or an ambiguous ask" "$( { has "$h_plan" "'planner'" && has "$h_plan" 'multi-item scaffold or an ambiguous ask'; }; echo $?)" "$h_plan"
check "hint: the delegation carries the prompt verbatim and the reason" "$( { has "$h_plan" 'prompt verbatim' && has "$h_plan" 'what the result enables'; }; echo $?)" "$h_plan"
check "hint: the lead keeps reading while the planner runs" "$(has "$h_plan" 'keep reading the code'; echo $?)" "$h_plan"

fixture "$TMP/review" "" done FEAT-0001 review ""
h_rev="$(hint "$TMP/review")"
check "hint, review state: sends verification to the reviewer" "$(has "$h_rev" "'independent-reviewer'"; echo $?)" "$h_rev"
h_doing="$(hint "$TMP/doing")"
# The two remaining arms of the case statement: deferred and the terminal list
# (a focused task at `done`). Review found them unguarded: a review sentence
# inserted into the terminal arm passed every assertion (TST-0007 round 1,
# finding 9). There is no `blocked` arm to cover -- `blocked` is not a status
# in STATUSES.md, and blocked-ness is `depends:`.
fixture "$TMP/deferred" TASK-0001 deferred FEAT-0001 doing ""; h_deferred="$(hint "$TMP/deferred")"
fixture "$TMP/terminal" TASK-0001 done FEAT-0001 doing "";     h_terminal="$(hint "$TMP/terminal")"
check "hint, terminal state: says nothing is in flight and who writes the next note" "$( { has "$h_terminal" 'nothing in flight' && has "$h_terminal" "'planner'"; }; echo $?)" "$h_terminal"
check "hint, deferred state: says to re-adopt first" "$(has "$h_deferred" 're-adopt'; echo $?)" "$h_deferred"
for pair in "empty:$h_empty" "planning:$h_plan" "doing:$h_doing" "deferred:$h_deferred" "terminal:$h_terminal"; do
  name="${pair%%:*}"; text="${pair#*:}"
  check "hint, $name state: no review sentence" "$(hasnot "$text" 'independent-reviewer'; echo $?)" "$text"
done

# Size bound (TASK-0103): at most 3 lines and 600 characters in every one of
# the six states, so the hint never grows into the SessionStart slice
# FEAT-0021 serves.
for pair in "empty:$h_empty" "planning:$h_plan" "doing:$h_doing" "review:$h_rev" "deferred:$h_deferred" "terminal:$h_terminal"; do
  name="${pair%%:*}"; text="${pair#*:}"
  lines=$(printf '%s\n' "$text" | wc -l | tr -d ' '); chars=${#text}
  check "hint, $name state: within 3 lines and 600 characters" "$([[ "$lines" -le 3 && "$chars" -le 600 ]]; echo $?)" "$lines lines, $chars chars"
done

# -- HC-003: the two exemptions and the waiver expiry (ISS-0051) --------------
# The hook and validate-docs.py both enforce this gate, and until ISS-0051 only
# the validator carried the exemptions -- so the hook denied `done` to any
# feature holding the acceptance check feature-scaffold requires.
fixture "$TMP/vg" "" doing FEAT-0001 doing ""
mkdir -p "$TMP/vg/docs/features/x"
FEATNOTE="$TMP/vg/docs/features/x/FEAT-0001-X.md"

tstnote "$TMP/vg" TST-0001 active "level: acceptance"
out="$(vgate "$TMP/vg" "$FEATNOTE" 'status: done
tests: ["TST-0001"]')"
check "HC-003: an acceptance test at active does not block done" "$(hasnot "$out" '"deny"'; echo $?)" "$out"

tstnote "$TMP/vg" TST-0002 ready "command: pytest -q"
out="$(vgate "$TMP/vg" "$FEATNOTE" 'status: done
tests: ["TST-0002"]')"
check "HC-003: a test with command: does not block done" "$(hasnot "$out" '"deny"'; echo $?)" "$out"

tstnote "$TMP/vg" TST-0003 failing ""
out="$(vgate "$TMP/vg" "$FEATNOTE" 'status: done
tests: ["TST-0003"]')"
check "HC-003: a failing manual test still blocks done" "$(has "$out" '"deny"'; echo $?)" "$out"

out="$(vgate "$TMP/vg" "$FEATNOTE" 'status: done
verification_waiver: docs-only')"
check "HC-003: a waiver with no expiry is denied" "$(has "$out" '"deny"'; echo $?)" "$out"
check "HC-003: the denial names waiver_expires" "$(has "$out" 'waiver_expires'; echo $?)" "$out"

out="$(vgate "$TMP/vg" "$FEATNOTE" 'status: done
verification_waiver: docs-only
waiver_expires: 2026-12-01')"
check "HC-003: a waiver with an expiry is allowed" "$(hasnot "$out" '"deny"'; echo $?)" "$out"

# -- HC-001: the four paths of ISS-0003 ---------------------------------------
fixture "$TMP/proj" "" backlog FEAT-0001 backlog ""
mkdir -p "$TMP/scratch/scratchpad" "$TMP/other/src"
check "gate: a scratch path with no repo above it is allowed" "$([[ -z "$(gate "$TMP/proj" "$TMP/scratch/scratchpad/report.html")" ]]; echo $?)"
check "gate: a path in a repo with no SNAPSHOT.yaml is allowed" "$([[ -z "$(gate "$TMP/proj" "$TMP/other/src/main.py")" ]]; echo $?)"
check "gate: a relative path inside the project is denied" "$(has "$(cd "$TMP/proj" && gate "$TMP/proj" "src/main.py")" '"deny"'; echo $?)"
check "gate: an absolute path inside the project is denied" "$(has "$(gate "$TMP/proj" "$TMP/proj/src/main.py")" '"deny"'; echo $?)"

# -- Every hook file is executable -------------------------------------------
# Last, so the assertion ordinals TST-0007 documents do not shift.
# Every assertion above invokes its hook as `bash "$HOOKS/<name>"`, which runs a
# file whatever its mode. Claude Code does not: .claude/settings.json registers
# every hook by bare path with no interpreter, so a hook missing the executable
# bit fails with "Permission denied" on each event it is registered for. That is
# how the delegation hint reached twelve repos unrunnable while this harness was
# green (project-os-dev ISS-0055). A failure here is fixed by re-running
# `python3 tools/scripts/generate-adapters.py --install-hooks`, and, in a repo
# with core.fileMode=false, by recording the mode with
# `git update-index --chmod=+x <path>` so it survives the next clone.
for hook in "$HOOKS"/*; do
  [ -f "$hook" ] || continue
  check "$(basename "$hook") is executable" "$([ -x "$hook" ]; echo $?)" "mode is $(stat -f '%Sp' "$hook" 2>/dev/null || stat -c '%A' "$hook")"
done

# On disk is not enough. A repo with core.fileMode=false records a new hook as
# 100644 whatever its mode here, so the checks above pass while a fresh clone
# still gets "Permission denied" -- which is how ISS-0055 shipped, and how
# session-touch.sh was added an hour after fixing it. Skipped outside a
# repository, and outside one that tracks these files.
# A hook file a downstream .gitignore swallows is invisible to every check
# above: git ls-files never lists it, so its mode is never wrong, and a clone
# simply does not have it. One repo ignored `lib/` and would have dropped the
# marker helper (project-os-dev ISS-0056), which is why the directory is called
# `shared`.
if git -C "$HOOKS" rev-parse --show-toplevel >/dev/null 2>&1; then
  for hook in "$HOOKS"/* "$HOOKS"/shared/*; do
    [ -f "$hook" ] || continue
    # --no-index, because check-ignore reports nothing for an already-tracked
    # file: without it this passes here and only fails in the repo that has not
    # committed the file yet, which is the one place nobody is looking.
    check "$(basename "$hook") is not gitignored" "$(! git -C "$HOOKS" check-ignore -q --no-index "$hook"; echo $?)" "a .gitignore pattern hides it from the commit"
  done
fi

if git -C "$HOOKS" rev-parse --show-toplevel >/dev/null 2>&1; then
  while read -r mode _ _ path; do
    [ -n "$path" ] || continue
    case "$path" in *shared/*) continue ;; esac # sourced, never executed
    check "$(basename "$path") is executable in git" "$([ "$mode" = "100755" ]; echo $?)" "index mode is $mode; record it with git update-index --chmod=+x"
  done <<GITMODES
$(git -C "$HOOKS" ls-files -s . 2>/dev/null)
GITMODES
fi

# -- HC-006: the focus half blocks only a stop that follows a write -----------
# Appended last, like the block above, so the ordinals TST-0007 documents by
# number do not shift. A set focus is durable project state: before ISS-0056 the
# hook read it as if it described the turn, and cost a forced continuation on
# every stop -- questions included -- in any repo whose focus was parked.
SESSION="test-hooks-$$-aaaa"
. "$HOOKS/shared/session-marker.sh"
MARKER=$(session_marker "$SESSION" "$TMP/doing")
rm -f "$MARKER"
# stop_with_session <project-dir> <session-id>
stop_with_session() { printf '{"stop_hook_active": false, "session_id": "%s"}' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/close-out-check.sh" 2>/dev/null; }
touch_hook()        { printf '{"session_id": "%s", "tool_name": "Write"}' "$2" | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/session-touch.sh" 2>/dev/null; }

out="$(stop_with_session "$TMP/doing" "$SESSION")"
check "stop hook, nothing written this session: the stop goes through" "$([[ -z "$out" ]]; echo $?)" "got: $out"

touch_hook "$TMP/doing" "$SESSION"
check "the touch hook records the write" "$([ -e "$MARKER" ]; echo $?)" "expected $MARKER"

out="$(stop_with_session "$TMP/doing" "$SESSION")"
check "stop hook, a write happened: it still blocks on focus" "$(has "$out" '"decision": "block"'; echo $?)"
check "the block spends the marker" "$([ ! -e "$MARKER" ]; echo $?)" "marker survived the block"

out="$(stop_with_session "$TMP/doing" "$SESSION")"
check "stop hook, quiet turn after a block: the stop goes through" "$([[ -z "$out" ]]; echo $?)" "got: $out"

# A payload without session_id cannot answer the question, so it blocks: the
# behaviour before ISS-0056. A check that disables itself when its input is
# missing is worse than one that nags.
out="$(stop_hook "$TMP/doing" false)"
check "stop hook, no session_id: falls back to blocking" "$(has "$out" '"decision": "block"'; echo $?)"

touch_hook "$TMP/doing" ""
check "the touch hook records nothing without a session_id" "$([ ! -e "$MARKER" ]; echo $?)"

# Two repos in one session must not share a marker, or work in one silences the
# reminder in the other.
fixture "$TMP/other" TASK-0001 doing FEAT-0001 doing ""
OTHER=$(session_marker "$SESSION" "$TMP/other")
check "the marker is per project, not per session" "$([ "$MARKER" != "$OTHER" ]; echo $?)" "both resolved to $MARKER"
touch_hook "$TMP/other" "$SESSION"
out="$(stop_with_session "$TMP/doing" "$SESSION")"
check "a write in one repo does not arm the other repo's check" "$([[ -z "$out" ]]; echo $?)" "got: $out"
rm -f "$MARKER" "$OTHER"

# -- HC-006: the block quotes the focus task's open boxes (project-os-dev TASK-0157)
# The fixture above has no task note, so every assertion before this point sees
# the plain reason; these give the task a note.
fixture "$TMP/boxes" TASK-0001 doing FEAT-0001 doing ""
BOXNOTE="$TMP/boxes/docs/features/x/plan/tasks/TASK-0001.md"
mkdir -p "$(dirname "$BOXNOTE")"
cat > "$BOXNOTE" <<'MD'
---
id: TASK-0001
---
# A task
## Definition of Done
- [x] Already done
- [ ] Write the "parser"; test it
## Steps
- [ ] Run the suite
## Notes
- [ ] Not a work box
MD
out="$(stop_hook "$TMP/boxes" false)"
check "stop hook, open boxes: the block is valid JSON" "$(printf '%s' "$out" | python3 -c 'import json,sys; json.load(sys.stdin)' >/dev/null 2>&1; echo $?)" "$out"
check "stop hook, open boxes: counts and quotes both open boxes" "$( { has "$out" '2 unticked box(es)' && has "$out" 'Write the \"parser\"; test it' && has "$out" 'Run the suite'; }; echo $?)" "$out"
check "stop hook, open boxes: leaves out ticked boxes and other sections" "$( { hasnot "$out" 'Already done' && hasnot "$out" 'Not a work box'; }; echo $?)" "$out"
check "stop hook, open boxes: still names both actions" "$( { has "$out" 'set the task status to done and clear focus now' && has "$out" 'write the handoff'; }; echo $?)" "$out"
sed -i.bak 's/^- \[ \]/- [x]/' "$BOXNOTE"; rm -f "$BOXNOTE.bak"
out="$(stop_hook "$TMP/boxes" false)"
check "stop hook, every box ticked: says so" "$(has "$out" 'every box in its note is ticked'; echo $?)" "$out"
{ echo '## Steps'; for i in 1 2 3 4 5 6 7; do echo "- [ ] step $i"; done; } >> "$BOXNOTE"
out="$(stop_hook "$TMP/boxes" false)"
check "stop hook, more than five open: quotes five and counts the rest" "$( { has "$out" 'step 5' && hasnot "$out" 'step 6' && has "$out" 'and 2 more'; }; echo $?)" "$out"
# An inline flow-map snapshot (your-trainer's style) resolves the note too.
sed -i.bak '/^    TASK-0001:$/{N;N;s/.*/    TASK-0001: { file: "docs\/features\/x\/plan\/tasks\/TASK-0001.md", status: doing }/;}' "$TMP/boxes/SNAPSHOT.yaml"; rm -f "$TMP/boxes/SNAPSHOT.yaml.bak"
out="$(stop_hook "$TMP/boxes" false)"
check "stop hook, inline snapshot style: still finds the note" "$(has "$out" '7 unticked box(es)'; echo $?)" "$out"

# Review round 1 of FEAT-0039: the cases the first version got wrong.
cat > "$BOXNOTE" <<'MD'
# A task
## Definition of Done
- [ ]
```
- [ ] inside a fence
```
MD
out="$(stop_hook "$TMP/boxes" false)"
check "stop hook: an empty box is counted and named, fenced lines are not boxes" "$( { has "$out" '1 unticked box(es): \"(a box with no text)\"' && hasnot "$out" 'inside a fence'; }; echo $?)" "$out"
printf '# A task\n## Notes\nNothing here.\n' > "$BOXNOTE"
out="$(stop_hook "$TMP/boxes" false)"
check "stop hook: a note with no box sections gets the plain reason, not 'every box is ticked'" "$( { hasnot "$out" 'every box' && has "$out" 'set the task status to done and clear focus now'; }; echo $?)" "$out"
printf '# A task\n## Steps\n- [ ] Found by name\n' > "$BOXNOTE"
sed -i.bak '/TASK-0001: {/d' "$TMP/boxes/SNAPSHOT.yaml"; rm -f "$TMP/boxes/SNAPSHOT.yaml.bak"
mv "$BOXNOTE" "$(dirname "$BOXNOTE")/TASK-0001-Named.md"
out2="$(stop_hook "$TMP/boxes" false)"
check "stop hook: a focus task missing from the snapshot is found by its note's filename" "$(has "$out2" '\"Found by name\"'; echo $?)" "$out2"

# -- HC-002: SessionStart serves the orientation slice (project-os-dev TASK-0080)
start_hook() { printf '{}' | CLAUDE_PROJECT_DIR="$1" bash "$HOOKS/snapshot-freshness.sh" 2>/dev/null; }
fixture "$TMP/start" TASK-0001 doing FEAT-0001 doing ""
mkdir -p "$TMP/start/tools/scripts" "$TMP/start/docs"
cp "$ROOT/tools/scripts/snapshot-slice.py" "$TMP/start/tools/scripts/"
touch "$TMP/start/AGENTS.md" "$TMP/start/CONTEXT.md" "$TMP/start/docs/INDEX.md"
out="$(start_hook "$TMP/start")"
check "session start: names the focus task, its status and note" "$(has "$out" 'focus.task: TASK-0001 (doing) docs/features/x/plan/tasks/TASK-0001.md'; echo $?)" "$out"
check "session start: lists in-flight items outside focus" "$(has "$out" 'ISS-0001 (open) docs/issues/ISS-0001.md'; echo $?)" "$out"
check "session start: no reminder to read the whole file" "$(hasnot "$out" 'REMINDER'; echo $?)" "$out"
check "session start: says to open the linked notes before changing anything" "$(has "$out" 'the notes it links'; echo $?)" "$out"
check "session start: no missing-files line when the contract files exist" "$(hasnot "$out" 'MISSING'; echo $?)" "$out"
rm "$TMP/start/AGENTS.md"
out="$(start_hook "$TMP/start")"
check "session start: a missing contract file is named (HC-002 guard)" "$(has "$out" 'MISSING contract files: AGENTS.md'; echo $?)" "$out"
touch "$TMP/start/AGENTS.md"
# Budget: 400 in-flight tasks with long paths stay under 6,000 characters.
python3 - "$TMP/start/SNAPSHOT.yaml" <<'PY'
import sys
path = sys.argv[1]
extra = "".join("    TASK-%04d:\n      file: docs/features/a-rather-long-feature-slug/plan/tasks/TASK-%04d-A-Long-Descriptive-Task-Title-Slug.md\n      status: doing\n" % (i, i) for i in range(2, 402))
text = open(path).read().replace("  tasks:\n", "  tasks:\n" + extra, 1)
open(path, "w").write(text)
PY
out="$(start_hook "$TMP/start")"
check "session start: 400 in-flight items stay within 6,000 characters" "$([[ ${#out} -le 6000 ]]; echo $?)" "${#out} chars"
check "session start: items past the budget are counted, not listed" "$(has "$out" 'more, not listed'; echo $?)" "$out"
# Inline flow maps, and the fallback when the slice script is absent.
fixture "$TMP/inline" "" doing FEAT-0001 doing ""
sed -i.bak '/^    TASK-0001:$/{N;N;s/.*/    TASK-0001: { file: "docs\/t.md", title: "a, b: c", status: doing }/;}' "$TMP/inline/SNAPSHOT.yaml"; rm -f "$TMP/inline/SNAPSHOT.yaml.bak"
mkdir -p "$TMP/inline/tools/scripts"; cp "$ROOT/tools/scripts/snapshot-slice.py" "$TMP/inline/tools/scripts/"
out="$(start_hook "$TMP/inline")"
check "session start: reads inline flow-map items" "$(has "$out" 'TASK-0001 (doing) docs/t.md'; echo $?)" "$out"
rm "$TMP/inline/tools/scripts/snapshot-slice.py"
out="$(start_hook "$TMP/inline")"
check "session start: without the slice script, falls back to the reminder" "$(has "$out" 'REMINDER'; echo $?)" "$out"

# bootstrap.sh prints the same orientation, and its focus lines when the slice prints nothing
mkdir -p "$TMP/start/tools/agents"; cp "$ROOT/tools/agents/bootstrap.sh" "$TMP/start/tools/agents/"
out="$(bash "$TMP/start/tools/agents/bootstrap.sh" 2>/dev/null)"
check "bootstrap: prints the orientation slice" "$(has "$out" 'focus.task: TASK-0001 (doing)'; echo $?)" "$out"
rm "$TMP/start/tools/scripts/snapshot-slice.py"
out="$(bash "$TMP/start/tools/agents/bootstrap.sh" 2>/dev/null)"
check "bootstrap: without the slice, prints project and focus lines" "$( { has "$out" 'focus.task: TASK-0001' && has "$out" 'project:'; }; echo $?)" "$out"

echo "test-hooks: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

#!/usr/bin/env bash
# TST-0009 (project-os-dev): the walk sheet is the ledger's owed set, in the
# order WALK.md authored, with each check walkable on the page (ADR-0029).
#
# One fixture repo under a tempdir, eight acceptance checks across three areas,
# one working ledger and one WALK.md. It asserts what a walker would notice:
#
#   rows      the automated, passed and excused checks are absent; the
#             invalidated and never-walked ones are present
#   survey    names the invalidated check's surface, the task that reopened it
#             with that task's title, and quotes its reopened section
#   order     sittings in file order (NOT alphabetical -- the fixture's first
#             sitting sorts last on purpose), `after:` before id inside one,
#             the first sitting to claim a check keeps it
#   labels    a check with no Setup heading prints "Setup: not stated", and a
#             check no sitting claims lands under "Unplaced"
#   silence   no duration anywhere on the sheet, which is the guard rail the
#             cancelled ordering attempt left behind
#
# Eight checks rather than the six the task sketched: six cannot carry a
# passed, an excused, an automated, an invalidated, an ordered pair AND an
# unplaced row at the same time.
# Paths resolve from this script's location. Exit 0 = every assertion holds.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SHEET="$ROOT/tools/scripts/walk-sheet.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
assertions=0; failures=0
check() { assertions=$((assertions + 1)); if [[ "$2" -ne 0 ]]; then failures=$((failures + 1)); echo "  FAIL $1${3:+: $3}"; fi; }
# has <label> <pattern>   -- the sheet contains a line matching pattern
has() { check "$1" "$(printf '%s' "$OUT" | grep -Eq "$2" && echo 0 || echo 1)"; }
hasnt() { check "$1" "$(printf '%s' "$OUT" | grep -Eq "$2" && echo 1 || echo 0)"; }
# line_of <pattern> -- 1-based line number of the first match, 0 when absent
line_of() { printf '%s' "$OUT" | grep -nE "$1" | head -1 | cut -d: -f1; }

REPO="$TMP/fixture"
mkdir -p "$REPO/docs/tests/acceptance" "$REPO/docs/releases/ledgers" "$REPO/docs/features/x/plan/tasks"
cat > "$REPO/SNAPSHOT.yaml" <<'YAML'
version: 1
updated: "2026-09-13T00:00Z"
template:
  replace_me: false
counters:
  TST: 8
focus:
  task: ""
  feature: ""
  phase: ""
  issue: ""
items: {}
YAML

# check <id> <area> <extra frontmatter> <setup section or -> <after list or ->
fixture_check() {
  local id="$1" area="$2" extra="$3" setup="$4" after="$5"
  {
    printf -- '---\ntype: "[[test]]"\nid: %s\ntitle: "The %s check"\nstatus: active\nowner: user:fixture\nscope: system\nlevel: acceptance\narea: "%s"\n' "$id" "$id" "$area"
    [[ "$after" != "-" ]] && printf 'after: %s\n' "$after"
    [[ -n "$extra" ]] && printf '%s\n' "$extra"
    printf -- '---\n\n# The %s check\n\n' "$id"
    [[ "$setup" != "-" ]] && printf '## Setup\n%s\n\n' "$setup"
    printf '## Steps\n1. Open the screen.\n2. Press the button.\n\n## Expect\n- The banner reads DONE.\n\n## Not this check\n- The banner colour, which is %s next door.\n' "$id"
  } > "$REPO/docs/tests/acceptance/$id-Fixture.md"
}
fixture_check TST-0001 Alpha 'command: "true"' 'Any device.' -
fixture_check TST-0002 Alpha '' 'A signed-in account.' -
fixture_check TST-0003 Alpha '' 'A signed-in account.' -
fixture_check TST-0004 Alpha '' 'A signed-in account with one session.' '["TST-0005"]'
fixture_check TST-0005 Alpha '' 'A fresh install.' -
fixture_check TST-0006 Beta  '' 'The trainer awake and paired.' -
fixture_check TST-0007 Beta  '' 'The trainer awake and paired.' -
fixture_check TST-0008 Gamma '' '-' -
# TST-0008 is the worst-shaped check the real corpora actually hold: no Setup,
# no Steps, no Expect, its whole procedure an unheaded paragraph under the
# title. 53 of your-trainer's 61 owed rows looked like this on 2026-09-13.
cat > "$REPO/docs/tests/acceptance/TST-0008-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0008
title: "The TST-0008 check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Gamma"
---

# The TST-0008 check

Open the panel and confirm the reading arrives. Nothing here is under a heading, which is the shape the sheet has to stay useful on.

## Provenance

Migrated from the old document in 2026-08.
MD
# A check with nothing at all under its title: the branch that has no prose to
# fall back to either.
cat > "$REPO/docs/tests/acceptance/TST-0009-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0009
title: "The TST-0009 check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Gamma"
---

# The TST-0009 check
MD

# The note the invalidation names: its title and its reopened section are what
# the survey is asserted to carry.
cat > "$REPO/docs/features/x/plan/tasks/TASK-0001-The-Banner-Moves.md" <<'MD'
---
type: "[[task]]"
id: TASK-0001
title: "The banner moves to the second row"
status: done
owner: user:fixture
parent: "[[FEAT-0001]]"
---

# The banner moves to the second row

## Acceptance checks reopened

- TST-0006 — the banner it asserts against is on a different row now.
MD

cat > "$REPO/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{
  "platform": "testbed",
  "entries": [
    {"check": "TST-0002", "mark": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0003", "mark": "excused", "date": "2026-09-01", "by": "user:fixture", "method": "manual", "reason": "not walked this cycle, by decision"},
    {"check": "TST-0006", "mark": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0006", "invalidated_by": "TASK-0001", "date": "2026-09-05", "reason": "the banner moved"}
  ],
  "evidence": []
}
JSON

# Sitting order is FILE order: "The trainer on the bench" sorts after "A fresh
# install" alphabetically, and must still render first.
cat > "$REPO/docs/tests/acceptance/WALK.md" <<'MD'
---
type: "[[reference]]"
title: "Walk order"
status: active
owner: user:fixture
created: 2026-09-13
updated: 2026-09-13
gallery: "make screens"
---

# Walk order

### The trainer on the bench

```yaml
surfaces: ["Alpha"]
checks: ["TST-0007"]
state: "A signed-in account with one session."
bench: ["The trainer, powered"]
```

### A fresh install

```yaml
surfaces: ["Beta"]
state: "A fresh install, no account yet."
bench: ["The tablet with the candidate build"]
```
MD

OUT="$(python3 "$SHEET" --release REL-0042 --platform testbed --repo-root "$REPO" 2>&1)"; code=$?
check "the generator exits 0 on a repo with a ledger" "$code" "$OUT"

# --- rows are exactly the ledger's owed manual checks
hasnt "the automated check (command:) never reaches the sheet" '^### \[TST-0001\]'
hasnt "a passed check is absent"                               '^### \[TST-0002\]'
hasnt "an excused check is absent while its ledger is open"    '^### \[TST-0003\]'
has   "a check invalidated after its pass is owed again"       '^### \[TST-0006\]'
has   "a never-walked check is owed"                           '^### \[TST-0004\]'
has   "the header counts rows and sittings"                    '\*\*6 owed rows in 3 sittings\.\*\*'
has   "the header says which count the validator reports"      'ISS-0060'

# --- the survey
has "the survey names the invalidated check's surface"     '^### Beta — 1 owed'
has "the survey names the task that reopened it"           '^- \*\*TASK-0001\*\* — The banner moves to the second row'
has "the survey quotes the reopened section"               '^> - TST-0006 — the banner it asserts against'
has "the survey prints WALK.md's gallery command"          'Regenerate and compare before walking anything: `make screens`'
hasnt "an owed check nobody invalidated is not in the survey" '^### Alpha — '

# --- order
first=$(line_of '^## Sitting 1 — The trainer on the bench')
second=$(line_of '^## Sitting 2 — A fresh install')
check "sittings render in WALK.md file order, not alphabetically" \
  "$( { [[ -n "$first" && -n "$second" && "$first" -lt "$second" ]]; }; echo $?)" "1=$first 2=$second"
a=$(line_of '^### \[TST-0005\]'); b=$(line_of '^### \[TST-0004\]')
check "a check with after: renders after its prerequisite, against id order" \
  "$( { [[ -n "$a" && -n "$b" && "$a" -lt "$b" ]]; }; echo $?)" "TST-0005=$a TST-0004=$b"
pulled=$(line_of '^### \[TST-0007\]')
check "a check named by id joins that sitting, not its own area's later one" \
  "$( { [[ -n "$pulled" && "$pulled" -lt "$second" ]]; }; echo $?)" "TST-0007=$pulled sitting2=$second"

# --- labels
has "a check no sitting claims lands under Unplaced" '^## Unplaced'
unplaced=$(line_of '^## Unplaced'); gamma=$(line_of '^### \[TST-0008\]')
check "the unclaimed area's check is the row under Unplaced" \
  "$( { [[ -n "$gamma" && "$gamma" -gt "$unplaced" ]]; }; echo $?)" "Unplaced=$unplaced TST-0008=$gamma"
has "a check with no Setup heading says so"   '\*\*Setup: not stated\.\*\*'
# A corpus written before the four headings existed keeps its procedure in an
# unheaded paragraph. Printing nothing for those rows would make the sheet
# useless on the only corpus big enough to need it.
has "a check with no Steps heading prints its own description"   '\*\*Steps: no heading\.\*\*'
has "that description is the note's prose, verbatim"             '^Open the panel and confirm the reading arrives\.'
hasnt "the fallback stops at the next heading"                   '^Migrated from the old document'
has "a check with no prose at all says the note states no steps" '_The note states no steps\._'
# A row's link has to work in a checkout, not only on the machine that
# generated the sheet.
has   "a row links its note by a repo-relative path" '^### \[TST-0004\]\(docs/tests/acceptance/'
hasnt "no row link is an absolute filesystem path"   '\]\(/'
has "a check with a Setup heading prints it"  '\*\*Setup:\*\* A fresh install\.'
has "each row prints the note's steps verbatim"    '^1\. Open the screen\.'
has "each row prints the note's expected result"   '^- The banner reads DONE\.'
has "each row carries an empty tick box"           '^- \[ \] walked, and the verdict recorded in the ledger'
has "a sitting prints the state it needs"          '\*\*State this sitting needs:\*\* A fresh install, no account yet\.'
has "a sitting prints what must be on the bench"   '^- The tablet with the candidate build'

# --- no schedule, anywhere (TASK-0449's guard rail)
check "the generator writes no duration of its own" \
  "$(printf '%s' "$OUT" | grep -Eiq '[0-9]+ *(min|minutes?|hours?|hrs?)\b|~ *[0-9]|\bminutes?\b|\bhours?\b|\bestimate' && echo 1 || echo 0)" \
  "$(printf '%s' "$OUT" | grep -Eino '[0-9]+ *(min|minutes?|hours?)|~ *[0-9]|\bminutes?\b|\bhours?\b' | head -3 | tr '\n' ' ')"

# --- a repo with no ledger is refused, and says where that is written down
NOLEDGER="$TMP/no-ledger"
mkdir -p "$NOLEDGER/docs/tests/acceptance"
cp "$REPO/SNAPSHOT.yaml" "$NOLEDGER/SNAPSHOT.yaml"
cp "$REPO/docs/tests/acceptance/TST-0004-Fixture.md" "$NOLEDGER/docs/tests/acceptance/"
err="$(python3 "$SHEET" --release REL-0042 --platform testbed --repo-root "$NOLEDGER" 2>&1)"; code=$?
check "a repo with no ledger exits 2" "$([[ $code -eq 2 ]]; echo $?)" "exit $code"
check "the refusal names ISS-0059" "$(printf '%s' "$err" | grep -q 'ISS-0059' && echo 0 || echo 1)" "$err"

# --- a repo with no WALK.md still gets a sheet, and is told its order is nobody's
rm "$REPO/docs/tests/acceptance/WALK.md"
OUT="$(python3 "$SHEET" --release REL-0042 --platform testbed --repo-root "$REPO" 2>&1)"
has "without WALK.md the sheet says the order is unauthored" 'authored no walk order'
has "without WALK.md the rows are still grouped by area"     '^## Sitting [0-9]+ — Alpha'
has "without WALK.md every owed row is still on the sheet"   '\*\*6 owed rows in'

# --- --out writes the sheet and reports the count
python3 "$SHEET" --release REL-0042 --platform testbed --repo-root "$REPO" --out "$TMP/sheet.md" >/dev/null 2>&1
check "--out writes the sheet to the named path" "$([[ -s "$TMP/sheet.md" ]]; echo $?)"

# ---------------------------------------------------------------------------
# The ledger's resolution layer. The first fixture has one OPEN ledger and no
# sealed one, so nothing above exercises what sealing does -- and that is where
# the sharpest rules live: an excuse expires with its release, everything else
# that clears persists until an invalidation, and a non-persisting mark in a
# sealed ledger takes nothing with it when it goes. An independent review on
# 2026-09-13 mutated all three and the 38-assertion suite noticed none of them.
# ---------------------------------------------------------------------------
LAYERS="$TMP/layers"
mkdir -p "$LAYERS/docs/tests/acceptance" "$LAYERS/docs/releases/ledgers"
cp "$REPO/SNAPSHOT.yaml" "$LAYERS/SNAPSHOT.yaml"
for id in TST-0101 TST-0102 TST-0103 TST-0104 TST-0105 TST-0106 TST-0107 TST-0108; do
  cat > "$LAYERS/docs/tests/acceptance/$id-Fixture.md" <<MD
---
type: "[[test]]"
id: $id
title: "The $id check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Alpha"
---

# The $id check

## Setup
A signed-in account.

## Steps
1. Open the screen.

## Expect
- The banner reads DONE.
MD
done
# Sealed first (2026-08-01): an invalidation for TST-0104 that a later ledger's
# pass must overtake, and the verdicts the layers are built on.
cat > "$LAYERS/docs/releases/ledgers/REL-0040-testbed.json" <<'JSON'
{
  "platform": "testbed", "release": "REL-0040", "version": "1.0", "sealed": "2026-08-01",
  "entries": [
    {"check": "TST-0101", "mark": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0102", "mark": "excused", "date": "2026-07-01", "by": "user:fixture", "method": "manual", "reason": "not this cycle"},
    {"check": "TST-0103", "mark": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0103", "mark": "blocked", "date": "2026-07-02", "by": "user:fixture", "method": "manual", "reason": "the rig was down"},
    {"check": "TST-0104", "invalidated_by": "TASK-0001", "date": "2026-07-03", "reason": "the banner moved"},
    {"check": "TST-0105", "mark": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0108", "mark": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"}
  ],
  "evidence": []
}
JSON
# Sealed LATER (2026-09-01) and named EARLIER (REL-0039): the pass that must
# overtake the invalidation above. The two orderings disagree on purpose --
# resolution order is the seal date, and a sort that fell back to filename
# order would reverse these two and lose the pass.
cat > "$LAYERS/docs/releases/ledgers/REL-0039-testbed.json" <<'JSON'
{
  "platform": "testbed", "release": "REL-0039", "version": "1.1", "sealed": "2026-09-01",
  "entries": [
    {"check": "TST-0104", "mark": "pass", "date": "2026-08-15", "by": "user:fixture", "method": "manual"}
  ],
  "evidence": []
}
JSON
# Sealed, and carrying NO release: the file that told the two implementations
# apart. Sorting on `sealed` and expiring on `release` disagree exactly here.
cat > "$LAYERS/docs/releases/ledgers/REL-0042-testbed.json" <<'JSON'
{
  "platform": "testbed", "sealed": "2026-09-02",
  "entries": [
    {"check": "TST-0105", "mark": "blocked", "date": "2026-09-02", "by": "user:fixture", "method": "manual", "reason": "the rig was down"}
  ],
  "evidence": []
}
JSON
cat > "$LAYERS/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{
  "platform": "testbed",
  "entries": [
    {"check": "TST-0101", "mark": "excused", "date": "2026-09-10", "by": "user:fixture", "method": "manual", "reason": "not this cycle"},
    {"check": "TST-0106", "mark": "pass", "date": "2026-09-10", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0108", "invalidated_by": "TASK-0001", "date": "2026-09-10", "reason": "the screen changed after the seal"}
  ],
  "evidence": []
}
JSON
OUT="$(python3 "$SHEET" --release REL-0043 --platform testbed --repo-root "$LAYERS" 2>&1)"
hasnt "an excuse in the OPEN ledger does not destroy the pass beneath it" '^### \[TST-0101\]'
has   "an excuse expires when its ledger seals, and the check is owed again"  '^### \[TST-0102\]'
hasnt "a blocked in a SEALED ledger expires and leaves the pass under it"     '^### \[TST-0103\]'
hasnt "a pass in a later ledger overtakes an invalidation in an earlier one"  '^### \[TST-0104\]'
hasnt "sealing is read from the sealed field, not from the release field"     '^### \[TST-0105\]'
hasnt "a pass in the open ledger clears"                                      '^### \[TST-0106\]'
has   "a check nobody ever walked is owed"                                    '^### \[TST-0107\]'
# The sealed ledgers resolve BEFORE the open one. Nothing pinned that boundary
# until this row: every other invalidation in the fixture sits in the earliest
# sealed ledger, so resolving the open ledger first changed nothing here while
# dropping 35 of your-trainer's 61 owed rows. Found by independent review,
# round two, 2026-09-13.
has   "an invalidation in the OPEN ledger reopens a pass from a sealed one"   '^### \[TST-0108\]'
has   "only the three genuinely owed rows are on the sheet"                   '\*\*3 owed rows in'

# ---------------------------------------------------------------------------
# Note shapes and WALK.md shapes a real corpus turns out to have.
# ---------------------------------------------------------------------------
SHAPES="$TMP/shapes"
mkdir -p "$SHAPES/docs/tests/acceptance" "$SHAPES/docs/releases/ledgers" "$SHAPES/docs/surfaces" "$SHAPES/docs/changes"
cp "$REPO/SNAPSHOT.yaml" "$SHAPES/SNAPSHOT.yaml"
cat > "$SHAPES/docs/tests/acceptance/TST-0201-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0201
title: "The old-headings check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Navigator"
---

# The old-headings check

## Procedure
1. Press the old button.

## Expected results
- The old banner appears.
MD
cat > "$SHAPES/docs/tests/acceptance/TST-0202-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0202
title: "The commented check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Navigator"
---

<!-- imported from the v2.1.1 plan, row 214 -->

# The commented check

Press the button and watch the row settle.
MD
cat > "$SHAPES/docs/tests/acceptance/TST-0203-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0203
title: "The regression check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Navigator"
covers: ["[[ISS-0001-The-Banner-Vanished]]"]
---

# The regression check

## Setup
A signed-in account.

## Steps
1. Do the thing that used to break.

## Expect
- It does not break.
MD
for id in TST-0204 TST-0205; do
  other=TST-0205; [[ "$id" == "TST-0205" ]] && other=TST-0204
  cat > "$SHAPES/docs/tests/acceptance/$id-Fixture.md" <<MD
---
type: "[[test]]"
id: $id
title: "The $id check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Navigator"
after: ["$other"]
---

# The $id check

## Setup
A signed-in account.

## Steps
1. Open it.

## Expect
- It opens.
MD
done
cat > "$SHAPES/docs/surfaces/SUR-0001-The-Navigator.md" <<'MD'
---
type: "[[surface]]"
id: SUR-0001
title: "Navigator"
status: active
owner: user:fixture
---

# Navigator
MD
cat > "$SHAPES/docs/changes/CHG-20260913-The-Banner-Moves.md" <<'MD'
---
type: "[[change]]"
id: CHG-20260913-The-Banner-Moves
title: "The banner moves to the second row"
status: merged
owner: user:fixture
---

# The banner moves to the second row

## Acceptance checks reopened

- TST-0201 the banner it asserts against is on a different row now.
MD
cat > "$SHAPES/docs/tests/acceptance/TST-0207-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0207
title: "The fenced check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Navigator"
---

# The fenced check

## Steps
1. Run it:

```bash
# this comment is a heading shape and must not end the section
./run --once
```

2. Watch the row settle.

## Expect
- The row settles.
MD
cat > "$SHAPES/docs/tests/acceptance/TST-0206-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0206
title: "The canonical-id check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Ledger"
---

# The canonical-id check

## Setup
A signed-in account.

## Steps
1. Open it.

## Expect
- It opens.
MD
cat > "$SHAPES/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{
  "platform": "testbed",
  "entries": [
    {"check": "TST-0201", "mark": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0201", "invalidated_by": "CHG-20260913-The-Banner-Moves", "date": "2026-09-05", "reason": "the banner moved"},
    {"check": "TST-0206", "mark": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0206", "invalidated_by": "CHG-20260913", "date": "2026-09-05", "reason": "the banner moved"}
  ],
  "evidence": []
}
JSON
# A sitting claiming its checks by SUR-* id rather than by the area string, a
# `state:` carrying a trailing comment, a bench entry whose sentence holds a
# comma, a block-style list, and a sitting that
# claims nothing at all.
cat > "$SHAPES/docs/tests/acceptance/WALK.md" <<'MD'
---
type: "[[reference]]"
title: "Walk order"
status: active
owner: user:fixture
created: 2026-09-13
updated: 2026-09-13
---

# Walk order

### The navigator sitting

```yaml
surfaces: ["SUR-0001"]          # SUR-* ids, or the area: strings themselves
state: "A signed-in account."   # the cheapest way there is the dev toggle
bench: ["A second device on the same Wi-Fi, for the tablet row", "The tablet"]
```

### The empty sitting

```yaml
checks:
  - TST-0203
state: "Nothing is claimed here."
```
MD
# Retiring a check means kept, and no longer asked. A sheet that printed one
# would undo the only thing retirement does -- and did, reporting five owed
# rows where the cockpit's page reported four (project-os-cockpit ISS-0303).
retired_check() { # retired_check <id> <status>
  cat > "$SHAPES/docs/tests/acceptance/$1-Fixture.md" <<MD
---
type: "[[test]]"
id: $1
title: "The $2 check"
status: $2
owner: user:fixture
scope: system
level: acceptance
area: "Navigator"
---

# The $2 check

## Setup
A signed-in account.

## Steps
1. Open it.

## Expect
- It opens.
MD
}
retired_check TST-0301 retired
# `superseded` is not a legal test status, and the sheet must not invent a
# filter the cockpit's `_is_retired` does not have: one disagreement fixed by
# introducing another is not a fix (project-os-cockpit ISS-0303).
retired_check TST-0302 superseded
OUT="$(python3 "$SHEET" --release REL-0050 --platform testbed --repo-root "$SHAPES" 2>&1)"
hasnt "a retired check is kept and no longer asked"       '^### \[TST-0301\]'
has   "a check at a status the sheet does not filter is still asked" '^### \[TST-0302\]'
has   "a check at active in the same area is still asked" '^### \[TST-0201\]'
has "a check on the pre-ADR-0027 headings still prints its procedure" '^1\. Press the old button\.'
has "and its expected result"                                         '^- The old banner appears\.'
has "an HTML comment above the title is not read as the steps"        '^Press the button and watch the row settle\.'
hasnt "that comment does not reach the sheet"                         'imported from the v2.1.1 plan'
has "a regression check is a manual row and stays on the sheet"       '^### \[TST-0203\]'
has "an invalidation naming a CHANGE resolves its full id and title"  '^- \*\*CHG-20260913-The-Banner-Moves\*\* . The banner moves to the second row'
# A ledger may name the same change by its canonical id instead. The fixture's
# second surface carries that form, and it must resolve to the same note.
has "an invalidation naming a change by its canonical id resolves too" '^- \*\*CHG-20260913\*\* . The banner moves to the second row'
# A ledger may name the same change by its canonical id instead. The fixture's
# second surface carries that form, and it must resolve to the same note.
has "an invalidation naming a change by its canonical id resolves too" '^- \*\*CHG-20260913\*\* . The banner moves to the second row'
has "and quotes that change notes reopened section"                   '^> - TST-0201 the banner it asserts against'
has "a SUR note labels its surface in the survey"                     '^### Navigator \(SUR-0001\) . 1 owed'
has "a sitting may claim its checks by SUR id"                        '^## Sitting 1 . The navigator sitting'
has "a trailing comment is stripped from a sittings state"            'State this sitting needs:\*\* A signed-in account\.$'
# The template's own example puts a comment on `surfaces:`. Reading it as part
# of the list would leave the sitting claiming nothing and its rows unplaced.
has "a trailing comment is stripped from a sittings surfaces too"    '^## Sitting 1 . The navigator sitting'
nav=$(line_of '^### \[TST-0201\]'); unp=$(line_of '^## Unplaced')
check "so the navigator rows do not fall through to Unplaced" \
  "$( { [[ -n "$nav" && -n "$unp" && "$nav" -lt "$unp" ]]; }; echo $?)" "TST-0201=$nav Unplaced=$unp"
# A fenced block inside a section carries heading-shaped lines; treating one as
# a heading truncates the steps at exactly the interesting part.
has "a fenced block does not end a section early"                    '^2\. Watch the row settle\.'
has "and the fenced content itself prints"                           '^\./run --once$'
# `bench:` is the field written as sentences, and a comma in one is ordinary.
# Splitting on every comma turned one item into two, the second of which --
# "for the tablet row" -- is an instruction to fetch nothing (ISS-0304).
has "a comma inside a quoted bench entry does not split it"          '^- A second device on the same Wi-Fi, for the tablet row$'
hasnt "so no half-sentence reaches the bench list"                   '^- for the tablet row$'
has "and the entry beside it is still its own item"                  '^- The tablet$'
# Block style is reported, not learned: ADR-0029 acceptance box 1 fixes one
# syntax. This sitting writes its only claim as a block list, so it claims
# nothing after all -- and BOTH warnings have to fire, because the second
# without the first would send an author looking for the wrong mistake.
has "a block-style list is reported rather than silently dropped"     'writes .checks:. as a block list'
has "a sitting claiming nothing is reported"                          'names neither .surfaces. nor .checks.'
has "the block-style sitting really did claim nothing"                '^### \[TST-0203\]'
has "a cycle in after: is reported and names both checks"             'forms a cycle over TST-0204, TST-0205'
has "a cycle drops no row: the first is still there"                  '^### \[TST-0204\]'
has "a cycle drops no row: the second is still there"                 '^### \[TST-0205\]'

# ---------------------------------------------------------------------------
# What the generator refuses. Each of these was a defect an independent review
# found in the cockpit's ledger reader; the fix was copied here, the test was
# not, and a mutation of each survived the 38-assertion suite.
# ---------------------------------------------------------------------------
refuse() { # refuse <label> <dir> <platform> <pattern>
  local out code
  out="$(python3 "$SHEET" --release REL-0001 --platform "$3" --repo-root "$2" 2>&1)"; code=$?
  check "$1" "$( { [[ $code -eq 2 ]] && printf '%s' "$out" | grep -Eq "$4"; }; echo $?)" "exit $code: $out"
}
BAD="$TMP/bad"
mkdir -p "$BAD/docs/tests/acceptance" "$BAD/docs/releases/ledgers"
cp "$REPO/SNAPSHOT.yaml" "$BAD/SNAPSHOT.yaml"
cp "$LAYERS/docs/tests/acceptance/TST-0107-Fixture.md" "$BAD/docs/tests/acceptance/"
refuse "an empty ledgers directory is refused, naming ISS-0059" "$BAD" testbed "ISS-0059"
cp "$LAYERS/docs/releases/ledgers/WORKING-testbed.json" "$BAD/docs/releases/ledgers/"
refuse "a platform with no ledger of its own is refused, not answered" "$BAD" andriod "no ledger for platform"
# Captured first, then grepped: under `pipefail` the refusal's exit 2 beats
# grep's 0 and the assertion fails on a message that is in fact correct.
named="$(python3 "$SHEET" --release REL-0001 --platform andriod --repo-root "$BAD" 2>&1)"
check "the refusal names the platforms that do have one" \
  "$(printf '%s' "$named" | grep -q 'testbed' && echo 0 || echo 1)" "$named"
cp "$BAD/docs/releases/ledgers/WORKING-testbed.json" "$BAD/docs/releases/ledgers/testbed.json"
refuse "a ledger whose filename names no platform is refused, not skipped" "$BAD" testbed "does not name a platform"
rm "$BAD/docs/releases/ledgers/testbed.json"
python3 - "$BAD/docs/releases/ledgers/WORKING-testbed.json" <<'FIXDATE'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["entries"].append({"check": "TST-0107", "mark": "pass", "date": "2026-13-45",
                     "by": "user:fixture", "method": "manual"})
json.dump(d, open(p, "w"))
FIXDATE
refuse "a date-shaped string that is not a date is refused" "$BAD" testbed "no usable date"

echo "test-walk-sheet: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

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

# --- the survey. It named invalidated checks and their `area:` until
# 2026-09-14; ADR-0045 decision 1 replaced that with the screens the change
# notes name, so these assertions cover the new answer and the old ones were
# rewritten here rather than deleted (TASK-0118).
has "the survey prints WALK.md's gallery command"          'Regenerate and compare before walking anything: `make screens`'
has "a repo with no released REL-* note says so in the survey" 'No release to compare against.*no released REL-\* note'
has "and says why nothing is listed rather than printing an empty list" 'nothing says which change notes are new'
hasnt "the survey no longer groups owed checks by their area" '^### Beta — 1 owed'
hasnt "and no longer names the note that reopened one"       '^- \*\*TASK-0001\*\*'

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
# The survey reads change notes now, not invalidation events. This fixture has
# no released REL-* note, so it has no tag to date them against and says so --
# the screens-and-captures answer is asserted on its own fixture below (TST-0011).
hasnt "an invalidation no longer puts its change note in the survey" '^- \*\*CHG-20260913-The-Banner-Moves\*\*'
hasnt "and its reopened section is no longer quoted"                 '^> - TST-0201 the banner it asserts against'
hasnt "a surface is no longer headed by how many checks it owes"     '^### Navigator \(SUR-0001\) . 1 owed'
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

# ---------------------------------------------------------------------------
# TST-0011: the survey is the screens the change notes named since the last
# release tag, with their sentences and their before and after pictures, and
# no test id (ADR-0045 decision 1, TASK-0118). A real git repo, because the
# tag and "added since it" are git questions.
# ---------------------------------------------------------------------------
SURVEY="$TMP/survey"
mkdir -p "$SURVEY/docs/tests/acceptance" "$SURVEY/docs/releases/ledgers" \
         "$SURVEY/docs/surfaces" "$SURVEY/docs/changes" \
         "$SURVEY/docs/tests/acceptance/gallery/v1.0" \
         "$SURVEY/docs/tests/acceptance/gallery/candidate"
cp "$REPO/SNAPSHOT.yaml" "$SURVEY/SNAPSHOT.yaml"
git_do() { git -C "$SURVEY" -c user.email=f@f -c user.name=fixture "$@" >/dev/null 2>&1; }

surface_note() { # surface_note <id> <title> <parent> <gallery inline list>
  cat > "$SURVEY/docs/surfaces/$1-Fixture.md" <<MD
---
type: "[[surface]]"
id: $1
title: "$2"
status: active
owner: user:fixture
kind: screen
parent: "$3"
gallery: $4
---

# $2
MD
}
surface_note SUR-0001 "Equipment panel" "" '[equipment-hub, "equipment-hub-dataonly:data-only"]'
surface_note SUR-0002 "Ride cockpit"    "" '[cockpit]'
surface_note SUR-0003 "Sensor dialog"   "[[SUR-0001]]" '[]'

change_note() { # change_note <id> <title> <impact body>
  cat > "$SURVEY/docs/changes/$1.md" <<MD
---
type: "[[change]]"
id: $1
title: "$2"
status: merged
owner: user:fixture
---

# $2

## Impact

$3

## Follow-ups
- [ ] none
MD
}
change_note CHG-20260701-Before-The-Tag "The old shipped change" \
  '- [[SUR-0002]]: the cockpit gained a lap counter before the tag.'
cat > "$SURVEY/docs/releases/REL-0010-v1.0.md" <<'MD'
---
type: "[[release]]"
id: REL-0010
title: "v1.0"
status: released
owner: user:fixture
version: "1.0"
tag: "v1.0"
date: "2026-08-01"
platform: "testbed"
---

# v1.0
MD
cat > "$SURVEY/docs/tests/acceptance/TST-0501-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0501
title: "The survey fixture check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Equipment panel"
---

# The survey fixture check

## Setup
The bench.

## Steps
1. Open it.

## Expect
- It opens.
MD
cat > "$SURVEY/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{"platform": "testbed", "entries": [], "evidence": []}
JSON
printf 'before\n' > "$SURVEY/docs/tests/acceptance/gallery/v1.0/equipment-hub.png"
printf 'after\n'  > "$SURVEY/docs/tests/acceptance/gallery/candidate/equipment-hub.png"
printf 'after\n'  > "$SURVEY/docs/tests/acceptance/gallery/candidate/cockpit.png"
git -C "$SURVEY" init -q 2>/dev/null
git_do add -A
git_do commit -m "before the tag"
git_do tag v1.0
# Added AFTER the tag: these are the survey.
change_note CHG-20260902-The-Panel-Gains-A-Slot "The panel gains a slot" \
  '- [[SUR-0001]]: a third slot appears, for a power meter.
- [[SUR-0003]]: the dialog now asks which sensor kind to pair.'
change_note CHG-20260903-The-Cockpit-Shows-Cadence "The cockpit shows cadence" \
  '- SUR-0002: the cadence number sits beside the power number.'
# A wikilink with display text is the ordinary Obsidian shape, and the sentence
# starts after the link rather than after the id.
change_note CHG-20260905-The-Panel-Names-The-Sensor "The panel names the sensor" \
  '- [[SUR-0001-Equipment-Panel|the equipment panel]]: the sensor name is shown under the slot.'
change_note CHG-20260904-A-Build-Script "A build script moved" \
  '- No screen changed: it is a build script.

```
- [[SUR-0003]]: this is the shape, inside a fence, and it altered nothing.
```'
# One line naming two screens: both are surveyed, and the sentence is the
# sentence rather than the markup between them.
change_note CHG-20260907-Two-Screens-One-Line "Two screens on one line" \
  '- [[SUR-0002]] and [[SUR-0003]]: both gained a gradient arrow.'
# An Impact line that MENTIONS a screen id in passing is not a line about that
# screen. One of your-trainer's twelve change notes since v2.1.8 reads
# "intervals.icu got its own, SUR-0016" in a sentence about `area:` values.
change_note CHG-20260906-A-Passing-Mention "A passing mention" \
  '- **Renamed:** eleven checks now point at SUR-0002, which is where the old label went.

SUR-0002 also gained a tab, and this paragraph is not a list item.'
git_do add -A
git_do commit -m "after the tag"

OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$SURVEY" 2>&1)"; code=$?
check "the survey fixture generates a sheet" "$code" "$OUT"
# The survey is everything between its heading and the first sitting.
SURVEY_TEXT="$(printf '%s' "$OUT" | awk '/^## Survey/{on=1} on&&/^## Sitting/{on=0} on')"
has "the survey says which release and tag it compared against" 'Compared against \*\*REL-0010\*\*, tagged `v1.0`'
has "a screen a change note named since the tag is listed"  '^### Equipment panel \(SUR-0001\)'
has "so is a screen named by the other change note"         '^### Ride cockpit \(SUR-0002\)'
has "each screen carries the sentence its change wrote"     '^- a third slot appears, for a power meter\. — The panel gains a slot'
has "a bare SUR id in an Impact line is read too"           '^- the cadence number sits beside the power number\.'
has "a wikilink with display text is cut off the sentence"  '^- the sensor name is shown under the slot\. — The panel names the sensor'
hasnt "a change note added BEFORE the tag is not in the survey" 'lap counter'
# A dialog is a child surface (ADR-0044 rule 2) and prints under its parent.
has "a child surface prints one level under its parent"     '^#### Sensor dialog \(SUR-0003\)'
parent_line=$(line_of '^### Equipment panel'); child_line=$(line_of '^#### Sensor dialog')
next_top=$(line_of '^### Ride cockpit')
check "and prints between its parent and the next screen" \
  "$( { [[ -n "$parent_line" && -n "$child_line" && -n "$next_top" && "$parent_line" -lt "$child_line" && "$child_line" -lt "$next_top" ]]; }; echo $?)" \
  "parent=$parent_line child=$child_line next=$next_top"
has "a screen with both pictures shows the one from the last release" '^!\[equipment-hub, at the last release\]\(docs/tests/acceptance/gallery/v1\.0/equipment-hub\.png\)'
has "and the one of the build being walked"            '^!\[equipment-hub, now\]\(docs/tests/acceptance/gallery/candidate/equipment-hub\.png\)'
has "a screen captured only now is marked new"         '`cockpit` . \*\*new\*\*'
hasnt "a gallery key with no picture at either end prints nothing" 'equipment-hub-dataonly'
hasnt "a No screen changed line is not printed as a screen"  'it is a build script'
hasnt "an Impact list inside a fenced block is an example, not a screen" 'inside a fence, and it altered nothing'
# One item, two screens. The first used to keep a sentence beginning "and
# [[SUR-...]]:" -- raw markup -- and the second was dropped in silence.
has   "both screens on one Impact line reach the survey"     '^- both gained a gradient arrow\. — Two screens on one line'
check "and that sentence appears under each of them" \
  "$(printf '%s' "$SURVEY_TEXT" | grep -c 'both gained a gradient arrow' | grep -q '^2$' && echo 0 || echo 1)" \
  "$(printf '%s' "$SURVEY_TEXT" | grep -c 'both gained a gradient arrow')"
hasnt "and neither sentence carries the markup between the two ids" 'and \[\[SUR-'
hasnt "an Impact line that only mentions an id is not a screen" 'which is where the old label went'
hasnt "a paragraph under Impact is not read as a screen either"  'also gained a tab'
check "the survey names no check at all" \
  "$(printf '%s' "$SURVEY_TEXT" | grep -q 'TST-' && echo 1 || echo 0)" \
  "$(printf '%s' "$SURVEY_TEXT" | grep -n 'TST-' | head -2 | tr '\n' ' ')"
has "the rest of the sheet still prints its rows" '^### \[TST-0501\]'

# A shallow clone has the commits and not the tag. The survey must say so and
# the sheet must still print: a walker in CI is not helped by a crash.
SHALLOW="$TMP/shallow"
git clone -q --depth 1 "file://$SURVEY" "$SHALLOW" 2>/dev/null
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$SHALLOW" 2>&1)"
has "a shallow clone says the tag is not in this checkout" 'the tag `v1.0` is not in this checkout'
has "and still prints the rows below it"                   '^### \[TST-0501\]'
hasnt "and lists no screen it cannot vouch for"            '^### Equipment panel'

# A released note with no tag: the other way the survey loses its anchor.
python3 - "$SURVEY/docs/releases/REL-0010-v1.0.md" <<'NOTAG'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text().replace('tag: "v1.0"', 'tag: ""'))
NOTAG
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$SURVEY" 2>&1)"
has "a released note carrying no tag says which note and why" 'REL-0010 is the newest released note for testbed and it carries no .tag:.'


# ---------------------------------------------------------------------------
# TST-0010: a procedure covers every owed part exactly once, the validator
# refuses one that does not, and the sheet prints only the owed steps
# (ADR-0045 decisions 3 to 5; TASK-0120, TASK-0121).
#
# One good fixture and one edit per defect. Each variant changes exactly one
# line of the procedure, so an assertion that passes is pinned to the rule it
# names rather than to a fixture that is broken in several ways at once.
# ---------------------------------------------------------------------------
PROC="$TMP/proc"
mkdir -p "$PROC/docs/tests/acceptance/walk" "$PROC/docs/releases/ledgers" "$PROC/docs/surfaces"
cp "$REPO/SNAPSHOT.yaml" "$PROC/SNAPSHOT.yaml"
for n in 1 2; do
  title="Equipment panel"; [[ "$n" == "2" ]] && title="Ride cockpit"
  cat > "$PROC/docs/surfaces/SUR-000$n-Fixture.md" <<MD
---
type: "[[surface]]"
id: SUR-000$n
title: "$title"
status: active
owner: user:fixture
kind: screen
---

# $title
MD
done
# proc_check <id> <area> <steps block> <expect block>
proc_check() {
  cat > "$PROC/docs/tests/acceptance/$1-Fixture.md" <<MD
---
type: "[[test]]"
id: $1
title: "The $1 check"
status: ${5:-active}
owner: user:fixture
scope: system
level: acceptance
area: "$2"
---

# The $1 check

## Setup
The bench.

## Steps
$3
$4
MD
}
proc_check TST-0401 Bench "1. Open the panel.
2. Start the workout.
3. Swap the trainer." "
## Expect
- The panel lists the trainer.
- The target power is shown.
- The trainer holds the target."
proc_check TST-0402 Bench "1. Open the panel.
2. Start the workout." "
## Expect
- The slot reads empty.
- The cadence field stays empty."
# Unnumbered steps: one owed part, cited by the bare id. 53 of your-trainer's
# 61 owed rows looked like this on 2026-09-13 (project-os-dev ISS-0064).
proc_check TST-0403 Bench "Open the panel and wait for the reading to arrive." "
## Expect
- The reading arrives."
proc_check TST-0404 Bench "1. Unpair everything.
2. Wait for the reading." "
## Expect
- The panel is empty again.
- The reading arrives."
proc_check TST-0405 Loose "1. Open it." "
## Expect
- It opens."
proc_check TST-0406 Bench "1. Open the old thing." "
## Expect
- The old thing still works." retired
# A check that never said what should happen. Its quote cannot be compared
# against anything, so the validator says nothing rather than claiming a
# mismatch it has no evidence for.
proc_check TST-0407 Bench "1. Reboot the tablet." ""
cat > "$PROC/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{
  "platform": "testbed",
  "entries": [
    {"check": "TST-0404", "mark": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"}
  ],
  "evidence": []
}
JSON
cat > "$PROC/docs/tests/acceptance/WALK.md" <<'MD'
---
type: "[[reference]]"
title: "Walk order"
status: active
owner: user:fixture
created: 2026-09-14
updated: 2026-09-14
---

# Walk order

### The bench

```yaml
surfaces: ["Bench"]
state: "The bench powered."
bench: ["The trainer"]
```

### No script

```yaml
surfaces: ["Loose"]
state: "Anything."
```
MD
cat > "$PROC/docs/tests/acceptance/walk/the-bench.md" <<'MD'
---
type: "[[reference]]"
title: "Procedure — The bench"
status: active
owner: user:fixture
created: 2026-09-14
updated: 2026-09-14
sitting: "The bench"
---

# Procedure — The bench

## Setup

The bench powered and the tablet awake.

## Steps

1. **Equipment panel (SUR-0001).** Open the panel.
   - The panel lists the trainer. `TST-0401.1`
   - The slot reads empty. `TST-0402.1`
2. **Ride cockpit (SUR-0002).** Start the workout.
   - The target power is shown. `TST-0401.2`
   - The cadence field stays empty. `TST-0402.2`
3. **Ride cockpit (SUR-0002).** Swap the trainer and read the panel.
   - The trainer holds the target. `TST-0401.3`
   - The reading arrives. `TST-0403` `TST-0404.2`
4. **Equipment panel (SUR-0001).** Unpair everything.
   - The panel is empty again. `TST-0404.1`
5. **Equipment panel (SUR-0001).** Reboot the tablet.
   - Nothing in this line is in any Expect section. `TST-0407.1`
MD

# --- step 1 of TST-0010: the procedure that covers every owed part once
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$PROC" 2>&1)"; code=$?
check "--check passes a procedure that cites every owed part once" "$code" "$OUT"
has "and says which sittings still have no procedure" 'no procedure yet for: No script'
hasnt "a check that states no expected result is not called a mismatch" 'quotes TST-0407'
hasnt "and citing a part that is NOT owed is not a failure"            'TST-0404'

variant() { # variant <name> <old line> <new line> -> echoes the repo path
  local dir="$TMP/proc-$1"
  rm -rf "$dir"; cp -R "$PROC" "$dir"
  OLD="$2" NEW="$3" python3 - "$dir/docs/tests/acceptance/walk/the-bench.md" <<'PY'
import os, pathlib, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
old, new = os.environ["OLD"], os.environ["NEW"]
assert old in t, "variant fixture: %r is not in the procedure" % old
p.write_text(t.replace(old, new, 1), encoding="utf-8")
PY
  printf '%s' "$dir"
}
procfail() { # procfail <label> <dir> <pattern>
  local out code
  out="$(python3 "$SHEET" --check --platform testbed --repo-root "$2" 2>&1)"; code=$?
  check "$1" "$( { [[ $code -eq 1 ]] && printf '%s' "$out" | grep -Eq "$3"; }; echo $?)" "exit $code: $out"
}

# --- steps 2 to 5a of TST-0010: one defect each, each message naming the
# check and the step involved
UNCITED="$(variant uncited '   - The reading arrives. `TST-0403` `TST-0404.2`' '   - The reading arrives. `TST-0404.2`')"
procfail "an owed part no step cites is refused, and named" "$UNCITED" \
  'owes TST-0403 \(one part, its steps are not numbered\) and no step cites it'
TWICE="$(variant twice '   - The target power is shown. `TST-0401.2`' '   - The target power is shown. `TST-0401.2` `TST-0401.1`')"
procfail "an owed part two steps cite is refused, and both steps named" "$TWICE" \
  'TST-0401 step 1 is cited by steps 1, 2'
RETIRED_V="$(variant retired '   - The slot reads empty. `TST-0402.1`' '   - The slot reads empty. `TST-0402.1`
   - The old thing still works. `TST-0406.1`')"
procfail "a tag naming a retired check is refused" "$RETIRED_V" \
  'step 1 of .*the-bench\.md cites TST-0406, which is retired'
MISSING="$(variant missing '`TST-0401.3`' '`TST-0401.9`')"
procfail "a tag naming a step the check does not have is refused" "$MISSING" \
  'cites step 9 of TST-0401, which has steps 1, 2, 3'
MISMATCH="$(variant mismatch '   - The target power is shown. `TST-0401.2`' '   - The target power is showing. `TST-0401.2`')"
procfail "a quoted expectation that does not match the check is refused" "$MISMATCH" \
  'quotes TST-0401 as .The target power is showing'
# Decided in TASK-0120: a check belongs to one sitting (rule 3), so a tag from
# another sitting's procedure either walks it twice or hides it.
CROSS="$(variant cross '`TST-0403` `TST-0404.2`' '`TST-0403` `TST-0404.2` `TST-0405.1`')"
procfail "a tag naming a check another sitting claims is refused" "$CROSS" \
  'cites TST-0405, which the sitting "No script" claims'
BARE="$(variant bare '`TST-0401.1`' '`TST-0401`')"
procfail "a bare tag on a check that numbers its steps is refused" "$BARE" \
  'cites TST-0401 with no step number, and that check numbers 3 steps'
UNKNOWN="$(variant unknown '`TST-0402.1`' '`TST-0402.1` `TST-0999.1`')"
procfail "a tag naming no check at all is refused" "$UNKNOWN" \
  'cites TST-0999, which matches no acceptance check in this repo'
NOSITTING="$(variant nositting 'sitting: "The bench"' 'sitting: ""')"
procfail "a procedure naming no sitting is refused" "$NOSITTING" \
  'no .sitting:. in its frontmatter'
WRONGSITTING="$(variant wrongsitting 'sitting: "The bench"' 'sitting: "The benches"')"
procfail "a procedure naming a sitting WALK.md does not have is refused" "$WRONGSITTING" \
  'matches no .### . heading in docs/tests/acceptance/WALK.md'
TWOFILES="$TMP/proc-twofiles"; rm -rf "$TWOFILES"; cp -R "$PROC" "$TWOFILES"
cp "$TWOFILES/docs/tests/acceptance/walk/the-bench.md" "$TWOFILES/docs/tests/acceptance/walk/the-bench-again.md"
procfail "a second procedure for one sitting is refused" "$TWOFILES" \
  'a second procedure for "The bench"'
# A step that says where it happens is a rule; a step that does not is reported
# and does not fail the release, because no owed part goes unwalked for it.
NOSCREEN="$(variant noscreen '2. **Ride cockpit (SUR-0002).** Start the workout.' '2. Start the workout.')"
out_noscreen="$(python3 "$SHEET" --check --platform testbed --repo-root "$NOSCREEN" 2>&1)"; code=$?
check "a step naming no screen is reported and does not fail the check" "$code" "$out_noscreen"
check "and the report names the step" \
  "$(printf '%s' "$out_noscreen" | grep -Eq 'step 2 names no screen' && echo 0 || echo 1)" "$out_noscreen"

# --- steps 6 and 7 of TST-0010: what the sheet prints
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PROC" 2>&1)"
has   "a sitting with a procedure says which file it walks"   'Walked from a procedure: \[docs/tests/acceptance/walk/the-bench\.md\]'
has   "the setup is printed once for the whole sitting"       '^The bench powered and the tablet awake\.$'
check "and exactly once" \
  "$(printf '%s' "$OUT" | grep -c '^The bench powered and the tablet awake\.$' | grep -q '^1$' && echo 0 || echo 1)" \
  "$(printf '%s' "$OUT" | grep -c '^The bench powered and the tablet awake\.$')"
has   "an owed step is printed with its screen in the heading" '^#### Step 1 — Equipment panel'
has   "its expectation lines keep their tags"                  'The panel lists the trainer\. `TST-0401\.1`'
hasnt "a step citing only checks that have passed is left out" 'Unpair everything'
has   "and the sheet says how many steps it left out"          '1 further step in this procedure is left out because it is not needed'
has   "a step mixing an owed tag with a passed one still prints" 'The reading arrives\.'
has   "and marks the tag that has already been walked"          '_\(already walked: TST-0404 step 2\)_'
has   "the sitting ends with one tick box per owed check"       '^- \[ \] \[TST-0401\]\(docs/tests/acceptance/TST-0401-Fixture\.md\)'
hasnt "a sitting walked from a procedure prints no per-check rows" '^### \[TST-0401\]'
has   "a sitting with no procedure prints per-check rows as before" '^### \[TST-0405\]'
has   "and that row still carries its own setup, steps and expect"  '^- It opens\.$'

# A procedure that no longer covers what the release owes must not hide it.
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$UNCITED" 2>&1)"
has "a procedure the validator refuses says so on the sheet" 'has a procedure and it no longer matches what the release owes'
has "and names what is wrong with it"                        '^- The bench owes TST-0403'
has "and falls back to per-check rows, so nothing owed is hidden" '^### \[TST-0403\]'
has "including the check the procedure did cover"                 '^### \[TST-0401\]'
# The sheet is not the only consumer: the cockpit renders `steps` from this
# payload. A refused procedure that still carried printable steps would show a
# stale script there while the sheet fell back here.
payload="$(SHEET_PATH="$SHEET" REPO_ROOT="$UNCITED" python3 - <<'PY'
import importlib.util as ilu, os, pathlib, sys
spec = ilu.spec_from_file_location("walk", os.environ["SHEET_PATH"])
walk = ilu.module_from_spec(spec)
#: Registered before it runs: a dataclass whose annotations are strings looks
#: its own module up in sys.modules, and an unregistered one fails there.
sys.modules["walk"] = walk
spec.loader.exec_module(walk)
sheet = walk.generate(pathlib.Path(os.environ["REPO_ROOT"]), "REL-0011", "testbed")
bench = [p for p in sheet.sittings if p.sitting.name == "The bench"][0]
print("problems=%d steps=%d owed_checks=%d walked=%s"
      % (len(bench.procedure.problems), len(bench.steps),
         len(bench.owed_checks), bench.walked_from_procedure))
PY
)"
check "a refused procedure carries no printable steps in the payload" \
  "$(printf '%s' "$payload" | grep -q '^problems=1 steps=0 owed_checks=0 walked=False$' && echo 0 || echo 1)" "$payload"

# --check over every platform at once is what validate-docs.sh runs.
allout="$(python3 "$SHEET" --check --repo-root "$UNCITED" 2>&1)"; code=$?
check "--check with no platform walks every ledger it finds" \
  "$( { [[ $code -eq 1 ]] && printf '%s' "$allout" | grep -q 'testbed'; }; echo $?)" "exit $code: $allout"
noproc="$(python3 "$SHEET" --check --repo-root "$LAYERS" 2>&1)"; code=$?
check "--check on a repo with no procedures at all passes quietly" \
  "$( { [[ $code -eq 0 ]] && [[ -z "$noproc" ]]; }; echo $?)" "exit $code: $noproc"
nolegder="$(python3 "$SHEET" --check --repo-root "$NOLEDGER" 2>&1)"; code=$?
check "--check on a repo with no ledger is not an error" "$code" "$nolegder"


# ---------------------------------------------------------------------------
# What an independent review found on 2026-09-14, one fixture per defect. Each
# of these passed the 139-assertion suite and was wrong.
# ---------------------------------------------------------------------------

# A step's number is its POSITION. Markdown's ordinary "every item is 1." style
# made two steps share a number, and the doubly-cited rule counted numbers.
ALLONE="$(variant allone '2. **Ride cockpit (SUR-0002).** Start the workout.' '1. **Ride cockpit (SUR-0002).** Start the workout.')"
out_allone="$(python3 "$SHEET" --check --platform testbed --repo-root "$ALLONE" 2>&1)"; code=$?
check "a procedure written 1. on every item still passes" "$code" "$out_allone"
DUPNUM="$TMP/proc-dupnum"; rm -rf "$DUPNUM"; cp -R "$PROC" "$DUPNUM"
python3 - "$DUPNUM/docs/tests/acceptance/walk/the-bench.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
t = t.replace("2. **Ride cockpit (SUR-0002).** Start the workout.",
              "1. **Ride cockpit (SUR-0002).** Start the workout.", 1)
t = t.replace("   - The cadence field stays empty. `TST-0402.2`",
              "   - The cadence field stays empty. `TST-0402.2`\n"
              "   - The panel lists the trainer. `TST-0401.1`", 1)
p.write_text(t)
PY
procfail "two steps that share a written number are still two steps" "$DUPNUM" \
  'TST-0401 step 1 is cited by steps 1, 2'
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$ALLONE" 2>&1)"
has "and the sheet numbers them by position, not by the digit" '^#### Step 2 — Ride cockpit'

# A tag inside a fenced block is an example. It used to satisfy coverage on its
# own, and could equally refuse a correct procedure for citing a part twice.
FENCED="$(variant fenced '   - The reading arrives. `TST-0403` `TST-0404.2`' '   - The reading arrives. `TST-0403` `TST-0404.2`

   ```
   - The panel lists the trainer. `TST-0401.1`
   ```
')"
out_fenced="$(python3 "$SHEET" --check --platform testbed --repo-root "$FENCED" 2>&1)"; code=$?
check "a fenced example does not refuse a correct procedure" "$code" "$out_fenced"
FENCEONLY="$(variant fenceonly '   - The reading arrives. `TST-0403` `TST-0404.2`' '   - The reading arrives. `TST-0404.2`

   ```
   - The reading arrives. `TST-0403`
   ```
')"
procfail "and a fenced example does not cover an owed part either" "$FENCEONLY" \
  'owes TST-0403 \(one part, its steps are not numbered\) and no step cites it'

# A check whose own Steps repeat a number owes one part per step, not one part.
CHKNUM="$TMP/proc-chknum"; rm -rf "$CHKNUM"; cp -R "$PROC" "$CHKNUM"
python3 - "$CHKNUM/docs/tests/acceptance/TST-0401-Fixture.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("1. Open the panel.\n2. Start the workout.\n3. Swap the trainer.",
                       "1. Open the panel.\n1. Start the workout.\n1. Swap the trainer."))
PY
out_chknum="$(python3 "$SHEET" --check --platform testbed --repo-root "$CHKNUM" 2>&1)"; code=$?
check "a check written 1. on every step still owes three parts" "$code" "$out_chknum"
python3 - "$CHKNUM/docs/tests/acceptance/walk/the-bench.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("   - The trainer holds the target. `TST-0401.3`\n", ""))
PY
procfail "and dropping one of them is still refused" "$CHKNUM" \
  'owes TST-0401 step 3 and no step cites it'

# A procedure covers its whole sitting, so it cites checks that have already
# passed. A reader that knew only the owed set called every such tag unknown.
has "the base fixture's procedure cites an already-passed check" '`TST-0404\.2`'

# A host may hold its own owed set and pass a smaller `checks` -- the cockpit
# does. `known` is what a tag is resolved against, so a procedure citing a
# check that has already passed must still be accepted. Asserted through the
# module's API, because the generator always passes the full set and so cannot
# reach this on its own.
known_out="$(SHEET_PATH="$SHEET" REPO_ROOT="$PROC" python3 - <<'PY'
import importlib.util as ilu, os, pathlib, sys
spec = ilu.spec_from_file_location("walk", os.environ["SHEET_PATH"])
walk = ilu.module_from_spec(spec); sys.modules["walk"] = walk
spec.loader.exec_module(walk)
root = pathlib.Path(os.environ["REPO_ROOT"])
read = walk.read_repo(root, "testbed")
owed = {c.id for c in walk.owed_checks(read.checks, read.events)}
thin = {i: c for i, c in read.checks.items() if i in owed}
sheet = walk.build_walk(
    thin, read.events, read.sittings, release="REL-0011", platform="testbed",
    surfaces=read.surfaces, surface_notes=read.surface_notes,
    procedures=read.procedures, known=read.checks, retired=read.retired,
    authored_order=read.authored)
bench = [p for p in sheet.sittings if p.sitting.name == "The bench"][0]
print("problems=%d walked=%s" % (len(bench.procedure.problems),
                                 bench.walked_from_procedure))
PY
)"
check "a host passing only its owed checks still accepts a passed-check tag" \
  "$(printf '%s' "$known_out" | grep -q '^problems=0 walked=True$' && echo 0 || echo 1)" "$known_out"

# Nothing to check is not a failure: validate-docs.sh runs --check on every
# commit, and a repo whose checks are all retired has no procedure to hold to
# anything.
ALLRET="$TMP/proc-allret"; rm -rf "$ALLRET"; cp -R "$PROC" "$ALLRET"
python3 - "$ALLRET" <<'PY'
import pathlib, sys
for p in (pathlib.Path(sys.argv[1]) / "docs/tests/acceptance").glob("TST-*.md"):
    p.write_text(p.read_text().replace("status: active", "status: retired"))
PY
out_allret="$(python3 "$SHEET" --check --quiet --repo-root "$ALLRET" 2>&1)"; code=$?
check "a repo whose checks are all retired is not a failing commit" "$code" "exit $code: $out_allret"
check "and it says nothing under --quiet" "$([[ -z "$out_allret" ]]; echo $?)" "$out_allret"
# ...and a BROKEN ledger is still a failing commit. The first version of the
# rule above caught every WalkError, so a ledger naming no platform and an
# entry dated 2026-13-45 both stopped being reported anywhere: the generator
# refused them and validate-docs.sh, which is the only thing that reads a
# ledger on every commit, did not. Found by independent review, round two.
BADLEDGER="$TMP/proc-badledger"; rm -rf "$BADLEDGER"; cp -R "$PROC" "$BADLEDGER"
cp "$BADLEDGER/docs/releases/ledgers/WORKING-testbed.json" "$BADLEDGER/docs/releases/ledgers/testbed.json"
out_bad="$(python3 "$SHEET" --check --quiet --repo-root "$BADLEDGER" 2>&1)"; code=$?
check "a ledger whose filename names no platform still fails --check" \
  "$( { [[ $code -eq 2 ]] && printf '%s' "$out_bad" | grep -q 'does not name a platform'; }; echo $?)" \
  "exit $code: $out_bad"
rm "$BADLEDGER/docs/releases/ledgers/testbed.json"
python3 - "$BADLEDGER/docs/releases/ledgers/WORKING-testbed.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["entries"].append({"check": "TST-0401", "mark": "pass", "date": "2026-13-45",
                     "by": "user:fixture", "method": "manual"})
json.dump(d, open(p, "w"))
PY
out_bad="$(python3 "$SHEET" --check --quiet --repo-root "$BADLEDGER" 2>&1)"; code=$?
check "a date-shaped string that is not a date still fails --check" \
  "$( { [[ $code -eq 2 ]] && printf '%s' "$out_bad" | grep -q 'no usable date'; }; echo $?)" \
  "exit $code: $out_bad"

# --check reads every change note, whatever the tag says: a repo with no
# released REL-* note still gets told which notes have no Impact list.
NOTAGCHG="$TMP/proc-nochg"; rm -rf "$NOTAGCHG"; cp -R "$PROC" "$NOTAGCHG"
mkdir -p "$NOTAGCHG/docs/changes"
cat > "$NOTAGCHG/docs/changes/CHG-20260914-Silent.md" <<'MD'
---
type: "[[change]]"
id: CHG-20260914-Silent
title: "A change that says nothing"
status: merged
owner: user:fixture
---

# A change that says nothing

## Summary
It shipped.
MD
out_nochg="$(python3 "$SHEET" --check --platform testbed --repo-root "$NOTAGCHG" 2>&1)"; code=$?
check "a change note with no Impact list is named even with no release tag" \
  "$( { [[ $code -eq 0 ]] && printf '%s' "$out_nochg" | grep -q 'CHG-20260914-Silent.md has no'; }; echo $?)" \
  "exit $code: $out_nochg"


echo "test-walk-sheet: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

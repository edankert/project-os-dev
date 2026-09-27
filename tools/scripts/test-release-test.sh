#!/usr/bin/env bash
# TST-0009 (project-os-dev): the release test sheet is the ledger's owed set, in the
# order RELEASE-TEST.md authored, with each check testable on the page (ADR-0029).
#
# One fixture repo under a tempdir, eight acceptance checks across three areas,
# one working ledger and one RELEASE-TEST.md. It asserts what a tester would notice:
#
#   rows      the automated, passed and excused checks are absent; the
#             invalidated and never-tested ones are present
#   changed   names the invalidated check's surface, the task that reopened it
#             with that task's title, and quotes its reopened section
#   order     sections in file order (NOT alphabetical -- the fixture's first
#             section sorts last on purpose), `after:` before id inside one,
#             the first section to claim a check keeps it
#   labels    a check with no Setup heading prints "Setup: not stated", and a
#             check no section claims lands under "Unplaced"
#   silence   no duration anywhere on the sheet, which is the guard rail the
#             cancelled ordering attempt left behind
#
# Eight checks rather than the six the task sketched: six cannot carry a
# passed, an excused, an automated, an invalidated, an ordered pair AND an
# unplaced row at the same time.
# Paths resolve from this script's location. Exit 0 = every assertion holds.
set -uo pipefail
# No bytecode, ever. This harness loads a module by path, and a cached compile
# that Python judges current is used in place of the source: on 2026-09-20 this
# reported two failures against code that passes, from a 14 September compile
# kept outside the repo (Apple's python3 sets sys.pycache_prefix). Writing no
# cache means none can go stale (project-os-dev ISS-0073).
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SHEET="$ROOT/tools/scripts/release-test.py"
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
# the what-changed list is asserted to carry.
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

# TST-0002's pass is stored under `mark`, the key an entry used before
# `result` (project-os-dev ADR-0050). Every reader accepts it for good, because
# sealed ledgers are never rewritten.
cat > "$REPO/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{
  "platform": "testbed",
  "entries": [
    {"check": "TST-0002", "mark": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0003", "result": "excused", "date": "2026-09-01", "by": "user:fixture", "method": "manual", "reason": "not tested this cycle, by decision"},
    {"check": "TST-0006", "result": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0006", "invalidated_by": "TASK-0001", "date": "2026-09-05", "reason": "the banner moved"}
  ],
  "evidence": []
}
JSON

# Section order is FILE order: "The trainer on the bench" sorts after "A fresh
# install" alphabetically, and must still render first.
cat > "$REPO/docs/tests/acceptance/RELEASE-TEST.md" <<'MD'
---
type: "[[reference]]"
title: "Section order"
status: active
owner: user:fixture
created: 2026-09-13
updated: 2026-09-13
gallery: "make screens"
---

# Section order

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
hasnt "the automated check (command:) never reaches the sheet" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0001[-.]'
hasnt "a pass stored under the old key mark still clears the check" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0002[-.]'
hasnt "an excused check is absent while its ledger is open"    '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0003[-.]'
has   "a check invalidated after its pass is owed again"       '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0006[-.]'
has   "a never-tested check is owed"                           '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0004[-.]'
has   "the header counts rows and sections"                    '\*\*6 checks in 3 sections, from 6 owed test notes\.\*\*'
has   "the header says which count the validator reports"      'ISS-0060'
# REQ-0033: before any section, a table lists every section in order with
# its owed count and one line of what it needs on the bench.
has   "the sections table lists the first section with its count and bench line" '^\| 1 \| The trainer on the bench \| 3 \| The trainer, powered \|$'
has   "and the next one after it"                                  '^\| 2 \| A fresh install \| 1 \| The tablet with the candidate build \|$'
has   "and the unplaced checks last, needing nothing extra"        '^\| – \| Unplaced \| 2 \| Nothing extra \|$'
check "a section's setup comes before its checks" \
  "$( s=$(line_of '^### Setup'); c=$(line_of '^### Checks'); [[ -n "$s" && -n "$c" && "$s" -lt "$c" ]]; echo $?)"

# --- what changed. It named invalidated checks and their `area:` until
# 2026-09-14; ADR-0045 decision 1 replaced that with the screens the change
# notes name, so these assertions cover the new answer and the old ones were
# rewritten here rather than deleted (TASK-0118).
has "what changed prints RELEASE-TEST.md's gallery command"          'Regenerate and compare before testing anything: `make screens`'
has "a repo with no released REL-* note says so under what changed" 'No release to compare against.*no released REL-\* note'
has "and says why nothing is listed rather than printing an empty list" 'nothing says which change notes are new'
hasnt "what changed no longer groups owed checks by their area" '^### Beta — 1 owed'
hasnt "and no longer names the note that reopened one"       '^- \*\*TASK-0001\*\*'

# --- order
first=$(line_of '^## Section 1 — The trainer on the bench')
second=$(line_of '^## Section 2 — A fresh install')
check "sections render in RELEASE-TEST.md file order, not alphabetically" \
  "$( { [[ -n "$first" && -n "$second" && "$first" -lt "$second" ]]; }; echo $?)" "1=$first 2=$second"
a=$(line_of '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0005[-.]'); b=$(line_of '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0004[-.]')
check "a check with after: renders after its prerequisite, against id order" \
  "$( { [[ -n "$a" && -n "$b" && "$a" -lt "$b" ]]; }; echo $?)" "TST-0005=$a TST-0004=$b"
pulled=$(line_of '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0007[-.]')
check "a check named by id joins that section, not its own area's later one" \
  "$( { [[ -n "$pulled" && "$pulled" -lt "$second" ]]; }; echo $?)" "TST-0007=$pulled section2=$second"

# --- labels
has "a check no section claims lands under Unplaced" '^## Unplaced'
unplaced=$(line_of '^## Unplaced'); gamma=$(line_of '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0008[-.]')
check "the unclaimed area's check is the row under Unplaced" \
  "$( { [[ -n "$gamma" && "$gamma" -gt "$unplaced" ]]; }; echo $?)" "Unplaced=$unplaced TST-0008=$gamma"
has "a check with no Setup heading says so"   '\*\*Setup: not stated\.\*\*'
# A corpus written before the four headings existed keeps its procedure in an
# unheaded paragraph. Printing nothing for those rows would make the sheet
# useless on the only corpus big enough to need it.
has "a check with no Steps heading prints its own description"   '\*\*Steps: no heading\.\*\*'
has "that description is the note's prose, verbatim"             '^    Open the panel and confirm the reading arrives\.'
hasnt "the fallback stops at the next heading"                   '^Migrated from the old document'
has "a check with no prose at all says the note states no steps" '_The note states no steps\._'
# A row's link has to work in a checkout, not only on the machine that
# generated the sheet.
has   "a row links its note by a repo-relative path" '^- \[ \] \*\*[0-9]+\.\*\* \[The TST-0004 check\]\(docs/tests/acceptance/TST-0004-'
hasnt "no row link is an absolute filesystem path"   '\]\(/'
has "a check with a Setup heading prints it"  '^  - Setup: A fresh install\.'
has "each row prints the note's steps verbatim"    '^    1\. Open the screen\.'
has "each row prints the note's expected result"   '^    - The banner reads DONE\. `TST-'
has "each row carries an empty tick box"           '^- \[ \] \*\*1\.\*\* '
has "a section prints the state it needs, as the thing to do before starting" '^1\. A fresh install, no account yet\.'
has "a section prints what must be on the bench"   '^- The tablet with the candidate build'

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

# --- a repo with no RELEASE-TEST.md still gets a sheet, and is told its order is nobody's
rm "$REPO/docs/tests/acceptance/RELEASE-TEST.md"
OUT="$(python3 "$SHEET" --release REL-0042 --platform testbed --repo-root "$REPO" 2>&1)"
has "without RELEASE-TEST.md the sheet says the order is unauthored" 'authored no section order'
has "without RELEASE-TEST.md the rows are still grouped by area"     '^## Section [0-9]+ — Alpha'
has "without RELEASE-TEST.md every owed row is still on the sheet"   '\*\*6 checks in [0-9]+ sections, from 6 owed'

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
    {"check": "TST-0101", "result": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0102", "result": "excused", "date": "2026-07-01", "by": "user:fixture", "method": "manual", "reason": "not this cycle"},
    {"check": "TST-0103", "result": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0103", "result": "blocked", "date": "2026-07-02", "by": "user:fixture", "method": "manual", "reason": "the rig was down"},
    {"check": "TST-0104", "invalidated_by": "TASK-0001", "date": "2026-07-03", "reason": "the banner moved"},
    {"check": "TST-0105", "result": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0108", "result": "pass", "date": "2026-07-01", "by": "user:fixture", "method": "manual"}
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
    {"check": "TST-0104", "result": "pass", "date": "2026-08-15", "by": "user:fixture", "method": "manual"}
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
    {"check": "TST-0105", "result": "blocked", "date": "2026-09-02", "by": "user:fixture", "method": "manual", "reason": "the rig was down"}
  ],
  "evidence": []
}
JSON
cat > "$LAYERS/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{
  "platform": "testbed",
  "entries": [
    {"check": "TST-0101", "result": "excused", "date": "2026-09-10", "by": "user:fixture", "method": "manual", "reason": "not this cycle"},
    {"check": "TST-0106", "result": "pass", "date": "2026-09-10", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0108", "invalidated_by": "TASK-0001", "date": "2026-09-10", "reason": "the screen changed after the seal"}
  ],
  "evidence": []
}
JSON
OUT="$(python3 "$SHEET" --release REL-0043 --platform testbed --repo-root "$LAYERS" 2>&1)"
hasnt "an excuse in the OPEN ledger does not destroy the pass beneath it" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0101[-.]'
has   "an excuse expires when its ledger seals, and the check is owed again"  '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0102[-.]'
hasnt "a blocked in a SEALED ledger expires and leaves the pass under it"     '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0103[-.]'
hasnt "a pass in a later ledger overtakes an invalidation in an earlier one"  '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0104[-.]'
hasnt "sealing is read from the sealed field, not from the release field"     '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0105[-.]'
hasnt "a pass in the open ledger clears"                                      '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0106[-.]'
has   "a check nobody ever tested is owed"                                    '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0107[-.]'
# The sealed ledgers resolve BEFORE the open one. Nothing pinned that boundary
# until this row: every other invalidation in the fixture sits in the earliest
# sealed ledger, so resolving the open ledger first changed nothing here while
# dropping 35 of your-trainer's 61 owed rows. Found by independent review,
# round two, 2026-09-13.
has   "an invalidation in the OPEN ledger reopens a pass from a sealed one"   '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0108[-.]'
has   "only the three genuinely owed rows are on the sheet"                   '\*\*3 checks in [0-9]+ sections?, from 3 owed'

# ---------------------------------------------------------------------------
# Note shapes and RELEASE-TEST.md shapes a real corpus turns out to have.
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
    {"check": "TST-0201", "result": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0201", "invalidated_by": "CHG-20260913-The-Banner-Moves", "date": "2026-09-05", "reason": "the banner moved"},
    {"check": "TST-0206", "result": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"},
    {"check": "TST-0206", "invalidated_by": "CHG-20260913", "date": "2026-09-05", "reason": "the banner moved"}
  ],
  "evidence": []
}
JSON
# A section claiming its checks by SUR-* id rather than by the area string, a
# `state:` carrying a trailing comment, a bench entry whose sentence holds a
# comma, a block-style list, and a section that
# claims nothing at all.
cat > "$SHAPES/docs/tests/acceptance/RELEASE-TEST.md" <<'MD'
---
type: "[[reference]]"
title: "Section order"
status: active
owner: user:fixture
created: 2026-09-13
updated: 2026-09-13
---

# Section order

### The navigator section

```yaml
surfaces: ["SUR-0001"]          # SUR-* ids, or the area: strings themselves
state: "A signed-in account."   # the cheapest way there is the dev toggle
bench: ["A second device on the same Wi-Fi, for the tablet row", "The tablet"]
```

### The empty section

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
hasnt "a retired check is kept and no longer asked"       '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0301[-.]'
has   "a check at a status the sheet does not filter is still asked" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0302[-.]'
has   "a check at active in the same area is still asked" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0201[-.]'
has "a check on the pre-ADR-0027 headings still prints its procedure" '^    1\. Press the old button\.'
has "and its expected result"                                         '^    - The old banner appears\.'
has "an HTML comment above the title is not read as the steps"        '^    Press the button and watch the row settle\.'
hasnt "that comment does not reach the sheet"                         'imported from the v2.1.1 plan'
has "a regression check is a manual row and stays on the sheet"       '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0203[-.]'
# What changed reads change notes now, not invalidation events. This fixture has
# no released REL-* note, so it has no tag to date them against and says so --
# the screens-and-captures answer is asserted on its own fixture below (TST-0011).
hasnt "an invalidation no longer puts its change note under what changed" '^- \*\*CHG-20260913-The-Banner-Moves\*\*'
hasnt "and its reopened section is no longer quoted"                 '^> - TST-0201 the banner it asserts against'
hasnt "a surface is no longer headed by how many checks it owes"     '^### Navigator \(SUR-0001\) . 1 owed'
has "a section may claim its checks by SUR id"                        '^## Section 1 . The navigator section'
has "a trailing comment is stripped from a sections state"            '^1\. A signed-in account\.$'
# The template's own example puts a comment on `surfaces:`. Reading it as part
# of the list would leave the section claiming nothing and its rows unplaced.
has "a trailing comment is stripped from a sections surfaces too"    '^## Section 1 . The navigator section'
nav=$(line_of '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0201[-.]'); unp=$(line_of '^## Unplaced')
check "so the navigator rows do not fall through to Unplaced" \
  "$( { [[ -n "$nav" && -n "$unp" && "$nav" -lt "$unp" ]]; }; echo $?)" "TST-0201=$nav Unplaced=$unp"
# A fenced block inside a section carries heading-shaped lines; treating one as
# a heading truncates the steps at exactly the interesting part.
has "a fenced block does not end a section early"                    '^    2\. Watch the row settle\.'
has "and the fenced content itself prints"                           '^    \./run --once$'
# `bench:` is the field written as sentences, and a comma in one is ordinary.
# Splitting on every comma turned one item into two, the second of which --
# "for the tablet row" -- is an instruction to fetch nothing (ISS-0304).
has "a comma inside a quoted bench entry does not split it"          '^- A second device on the same Wi-Fi, for the tablet row$'
hasnt "so no half-sentence reaches the bench list"                   '^- for the tablet row$'
has "and the entry beside it is still its own item"                  '^- The tablet$'
# Block style is reported, not learned: ADR-0029 acceptance box 1 fixes one
# syntax. This section writes its only claim as a block list, so it claims
# nothing after all -- and BOTH warnings have to fire, because the second
# without the first would send an author looking for the wrong mistake.
has "a block-style list is reported rather than silently dropped"     'writes .checks:. as a block list'
has "a section claiming nothing is reported"                          'names neither .surfaces. nor .checks.'
has "the block-style section really did claim nothing"                '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0203[-.]'
has "a cycle in after: is reported and names both checks"             'forms a cycle over TST-0204, TST-0205'
has "a cycle drops no row: the first is still there"                  '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0204[-.]'
has "a cycle drops no row: the second is still there"                 '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0205[-.]'

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
d["entries"].append({"check": "TST-0107", "result": "pass", "date": "2026-13-45",
                     "by": "user:fixture", "method": "manual"})
json.dump(d, open(p, "w"))
FIXDATE
refuse "a date-shaped string that is not a date is refused" "$BAD" testbed "no usable date"

# ---------------------------------------------------------------------------
# TST-0011: what changed is the screens the change notes named since the last
# release tag, with their sentences and their before and after pictures, and
# no test id (ADR-0045 decision 1, TASK-0118). A real git repo, because the
# tag and "added since it" are git questions.
# ---------------------------------------------------------------------------
CHANGED="$TMP/what-changed"
mkdir -p "$CHANGED/docs/tests/acceptance" "$CHANGED/docs/releases/ledgers" \
         "$CHANGED/docs/surfaces" "$CHANGED/docs/changes" \
         "$CHANGED/docs/tests/acceptance/gallery/v1.0" \
         "$CHANGED/docs/tests/acceptance/gallery/candidate"
cp "$REPO/SNAPSHOT.yaml" "$CHANGED/SNAPSHOT.yaml"
git_do() { git -C "$CHANGED" -c user.email=f@f -c user.name=fixture "$@" >/dev/null 2>&1; }

surface_note() { # surface_note <id> <title> <parent> <gallery inline list>
  cat > "$CHANGED/docs/surfaces/$1-Fixture.md" <<MD
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
  cat > "$CHANGED/docs/changes/$1.md" <<MD
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
cat > "$CHANGED/docs/releases/REL-0010-v1.0.md" <<'MD'
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
cat > "$CHANGED/docs/tests/acceptance/TST-0501-Fixture.md" <<'MD'
---
type: "[[test]]"
id: TST-0501
title: "The what-changed fixture check"
status: active
owner: user:fixture
scope: system
level: acceptance
area: "Equipment panel"
---

# The what-changed fixture check

## Setup
The bench.

## Steps
1. Open it.

## Expect
- It opens.
MD
cat > "$CHANGED/docs/releases/ledgers/WORKING-testbed.json" <<'JSON'
{"platform": "testbed", "entries": [], "evidence": []}
JSON
printf 'before\n' > "$CHANGED/docs/tests/acceptance/gallery/v1.0/equipment-hub.png"
printf 'after\n'  > "$CHANGED/docs/tests/acceptance/gallery/candidate/equipment-hub.png"
printf 'after\n'  > "$CHANGED/docs/tests/acceptance/gallery/candidate/cockpit.png"
git -C "$CHANGED" init -q 2>/dev/null
git_do add -A
git_do commit -m "before the tag"
git_do tag v1.0
# Added AFTER the tag: these are what changed.
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
# One line naming two screens: both are listed, and the sentence is the
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

OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$CHANGED" 2>&1)"; code=$?
check "the what-changed fixture generates a sheet" "$code" "$OUT"
# What changed on the platform is everything between its heading and the
# first section; each section's own list runs from its heading to its row count.
CHANGED_TEXT="$(printf '%s' "$OUT" | awk '/^## What changed/{on=1} on&&/^## Section/{on=0} on')"
SECTION_CHANGED="$(printf '%s' "$OUT" | awk '/^### What changed on the screens/{on=1} on&&/^### (Setup|Checks)/{on=0} on')"
has "what changed says which release and tag it compared against" 'Compared against \*\*REL-0010\*\*, tagged `v1.0`'
# REQ-0035: a changed screen is listed at the head of the section that tests
# it, and a screen no section tests is listed once before the sections.
has "a screen a change note named since the tag is listed"  '^#### Equipment panel \(SUR-0001\)'
has "so is a screen named by the other change note"         '^### Ride cockpit \(SUR-0002\)'
check "the screen its section tests is listed in that section, not before it" \
  "$(printf '%s' "$SECTION_CHANGED" | grep -q '^#### Equipment panel' && ! printf '%s' "$CHANGED_TEXT" | grep -q 'Equipment panel' && echo 0 || echo 1)" "$CHANGED_TEXT"
check "the screen no section tests is listed before the sections, and only there" \
  "$(printf '%s' "$CHANGED_TEXT" | grep -q '^### Ride cockpit' && [[ $(printf '%s' "$OUT" | grep -c 'Ride cockpit (SUR-0002)') -eq 1 ]] && echo 0 || echo 1)" "$CHANGED_TEXT"
has "and the part before the sections says why it is there" '^No section on this sheet tests these changed screens'
has "the section's list says what it is"                    '^### What changed on the screens this section tests$'
wc_line=$(line_of '^### What changed on the screens'); setup_line=$(line_of '^### Setup'); checks_line=$(line_of '^### Checks')
check "a section prints what changed, then setup, then its checks" \
  "$( { [[ -n "$wc_line" && -n "$checks_line" && "$wc_line" -lt "$checks_line" && ( -z "$setup_line" || ( "$wc_line" -lt "$setup_line" && "$setup_line" -lt "$checks_line" ) ) ]]; }; echo $?)" \
  "what changed=$wc_line setup=$setup_line checks=$checks_line"
has "a repo with no short lines says the Impact sentences are shown" '^\*\*Short lines not used:\*\* no short lines are written for this platform'
has "each screen carries the sentence its change wrote"     '^- a third slot appears, for a power meter\. — The panel gains a slot'
has "a bare SUR id in an Impact line is read too"           '^- the cadence number sits beside the power number\.'
has "a wikilink with display text is cut off the sentence"  '^- the sensor name is shown under the slot\. — The panel names the sensor'
hasnt "a change note added BEFORE the tag is not under what changed" 'lap counter'
# A dialog is a child surface (ADR-0044 rule 2) and prints under its parent.
has "a child surface prints one level under its parent"     '^##### Sensor dialog \(SUR-0003\)'
parent_line=$(line_of '^#### Equipment panel'); child_line=$(line_of '^##### Sensor dialog')
next_top=$(line_of '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0501[-.]')
check "and prints between its parent and the section's first check" \
  "$( { [[ -n "$parent_line" && -n "$child_line" && -n "$next_top" && "$parent_line" -lt "$child_line" && "$child_line" -lt "$next_top" ]]; }; echo $?)" \
  "parent=$parent_line child=$child_line next=$next_top"
has "a screen with both pictures shows the one from the last release" '^!\[equipment-hub, at the last release\]\(docs/tests/acceptance/gallery/v1\.0/equipment-hub\.png\)'
has "and the one of the build being tested"            '^!\[equipment-hub, now\]\(docs/tests/acceptance/gallery/candidate/equipment-hub\.png\)'
has "a screen captured only now is marked new"         '`cockpit` . \*\*new\*\*'
hasnt "a gallery key with no picture at either end prints nothing" 'equipment-hub-dataonly'
hasnt "a No screen changed line is not printed as a screen"  'it is a build script'
hasnt "an Impact list inside a fenced block is an example, not a screen" 'inside a fence, and it altered nothing'
# One item, two screens. The first used to keep a sentence beginning "and
# [[SUR-...]]:" -- raw markup -- and the second was dropped in silence.
has   "both screens on one Impact line reach what changed"     '^- both gained a gradient arrow\. — Two screens on one line'
check "and that sentence appears under each of them" \
  "$(printf '%s' "$OUT" | grep -c 'both gained a gradient arrow' | grep -q '^2$' && echo 0 || echo 1)" \
  "$(printf '%s' "$OUT" | grep -c 'both gained a gradient arrow')"
hasnt "and neither sentence carries the markup between the two ids" 'and \[\[SUR-'
hasnt "an Impact line that only mentions an id is not a screen" 'which is where the old label went'
hasnt "a paragraph under Impact is not read as a screen either"  'also gained a tab'
check "what changed names no check at all" \
  "$(printf '%s%s' "$CHANGED_TEXT" "$SECTION_CHANGED" | grep -q 'TST-' && echo 1 || echo 0)" \
  "$(printf '%s%s' "$CHANGED_TEXT" "$SECTION_CHANGED" | grep -n 'TST-' | head -2 | tr '\n' ' ')"
has "the rest of the sheet still prints its rows" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0501[-.]'

# A shallow clone has the commits and not the tag. What changed must say so and
# the sheet must still print: a tester in CI is not helped by a crash.
SHALLOW="$TMP/shallow"
git clone -q --depth 1 "file://$CHANGED" "$SHALLOW" 2>/dev/null
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$SHALLOW" 2>&1)"
has "a shallow clone says the tag is not in this checkout" 'the tag `v1.0` is not in this checkout'
has "and still prints the rows below it"                   '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0501[-.]'
hasnt "and lists no screen it cannot vouch for"            'Equipment panel \(SUR-0001\)'

# ---------------------------------------------------------------------------
# REQ-0035 (TASK-0191): what changed is for one platform, a picture older than
# its change is flagged, and short lines written at release preparation
# replace the Impact sentences while they match the last release tag.
# ---------------------------------------------------------------------------
PLAT="$TMP/what-changed-platforms"; rm -rf "$PLAT"; cp -R "$CHANGED" "$PLAT"
gp() { git -C "$PLAT" -c user.email=f@f -c user.name=fixture "$@" >/dev/null 2>&1; }
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PLAT" 2>&1)"
# The fixture's candidate pictures were committed before the tag, and the
# change notes after it, so neither picture can show its change.
has "a candidate picture committed before its change is flagged, with its date" \
  '^`equipment-hub` — \*\*this picture is older than the change\*\*: it was committed on [0-9]{4}-[0-9]{2}-[0-9]{2}, before CHG-20260902-The-Panel-Gains-A-Slot'
printf 'recaptured\n' > "$PLAT/docs/tests/acceptance/gallery/candidate/equipment-hub.png"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PLAT" 2>&1)"
hasnt "a picture recaptured and not yet committed is not flagged" '^`equipment-hub` — \*\*this picture is older'
gp add -A; gp commit -m "recapture the panel"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PLAT" 2>&1)"
hasnt "nor is one committed after the change" '^`equipment-hub` — \*\*this picture is older'
has   "while the picture nobody recaptured still is" '^`cockpit` — \*\*this picture is older than the change\*\*'

# A second platform, and change notes that say which platform they changed.
printf '{"platform": "other", "entries": [], "evidence": []}\n' > "$PLAT/docs/releases/ledgers/WORKING-other.json"
plat_note() { # plat_note <id> <frontmatter line or -> <impact body>
  {
    printf -- '---\ntype: "[[change]]"\nid: %s\ntitle: "%s"\nstatus: merged\nowner: user:fixture\n' "$1" "$1"
    [[ "$2" != "-" ]] && printf '%s\n' "$2"
    printf -- '---\n\n# %s\n\n## Impact\n\n%s\n' "$1" "$3"
  } > "$PLAT/docs/changes/$1.md"
}
plat_note CHG-20260910-Only-On-Other 'platforms: [other]' \
  '- [[SUR-0002]]: the other build gained a menu.'
plat_note CHG-20260911-Marked-Lines 'platforms: [testbed, other]' \
  '- [other] [[SUR-0001]]: only the other build moved the slot.
- [testbed] [[SUR-0001]]: the testbed build renamed the slot.'
plat_note CHG-20261001-After-The-Rule - \
  '- [[SUR-0002]]: a note written after platforms: became required.'
plat_note CHG-20260912-An-Unknown-Platform 'platforms: [desktop]' \
  '- [[SUR-0002]]: a platform this project keeps no ledger for.'
gp add -A; gp commit -m "notes that name their platforms"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PLAT" 2>&1)"
hasnt "a change declared for another platform is not listed" 'gained a menu'
has   "an Impact line marked for this platform is listed"      '^- the testbed build renamed the slot\.'
hasnt "an Impact line marked for another platform is not"      'only the other build moved the slot'
has   "change notes declaring no platforms: are named, once, as listed everywhere" \
  '^\*\*Listed on every platform:\*\* [0-9]+ change notes declare no `platforms:`.*CHG-20260902-The-Panel-Gains-A-Slot'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$PLAT" 2>&1)"; code=$?
check "--check fails when a new change note declares no platforms:" "$([[ $code -eq 1 ]]; echo $?)" "exit $code"
has   "and names that note as an error"   '^ERROR \[RELEASE-TEST\] .*CHG-20261001-After-The-Rule\.md names a screen .* declares no `platforms:`'
has   "an older note without platforms: is only a warning" '^WARN  \[RELEASE-TEST\] .*CHG-20260902-The-Panel-Gains-A-Slot\.md names a screen .* declares no `platforms:`'
has   "a platform with no ledger is an error" '^ERROR \[RELEASE-TEST\] .*CHG-20260912-An-Unknown-Platform\.md names the platform `desktop`'

# The short lines, written against the last release tag.
mkdir -p "$PLAT/docs/tests/acceptance/release-test"
cat > "$PLAT/docs/tests/acceptance/release-test/what-changed-testbed.md" <<'MD'
---
type: "[[reference]]"
title: "What changed on testbed since v1.0"
status: active
owner: user:fixture
tag: "v1.0"
---

# What changed on testbed since v1.0

- [[SUR-0001]]: A third slot, for a power meter. ([[CHG-20260902-The-Panel-Gains-A-Slot]])
- [[SUR-0002]]: This line names no change note.
MD
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PLAT" 2>&1)"
has   "a short line replaces its change's Impact sentence" '^- A third slot, for a power meter\.$'
hasnt "and the Impact sentence is not printed as well"      'a third slot appears, for a power meter'
has   "a change with no short line keeps its Impact sentence" '^- the sensor name is shown under the slot\. — The panel names the sensor'
hasnt "short lines that match the tag draw no notice"       'Short lines not used'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$PLAT" 2>&1)"
has   "--check warns about a change with no short line" \
  '^WARN  \[RELEASE-TEST\] .*what-changed-testbed\.md has no short line for SUR-0003 on testbed, which CHG-20260902-The-Panel-Gains-A-Slot changed'
has   "and about a line that names no change note" '^WARN  \[RELEASE-TEST\] .*the line for SUR-0002 names no change note'
hasnt "the short lines file is not read as a procedure" 'what-changed-testbed\.md: no `section:`'
sed -i.bak 's/^tag: "v1.0"/tag: "v0.9"/' "$PLAT/docs/tests/acceptance/release-test/what-changed-testbed.md"; rm -f "$PLAT"/docs/tests/acceptance/release-test/*.bak
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PLAT" 2>&1)"
has   "short lines written against an older tag are not used, and the sheet says why" \
  '^\*\*Short lines not used:\*\* the short lines in `docs/tests/acceptance/release-test/what-changed-testbed\.md` were written against `v0\.9` and the last release is `v1\.0`'
hasnt "and none of them is printed" '^- A third slot, for a power meter\.$'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$PLAT" 2>&1)"
hasnt "--check does not hold out-of-date short lines to this release" 'has no short line for'

# A released note with no tag: the other way what changed loses its anchor.
python3 - "$CHANGED/docs/releases/REL-0010-v1.0.md" <<'NOTAG'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text().replace('tag: "v1.0"', 'tag: ""'))
NOTAG
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$CHANGED" 2>&1)"
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
mkdir -p "$PROC/docs/tests/acceptance/release-test" "$PROC/docs/releases/ledgers" "$PROC/docs/surfaces"
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
    {"check": "TST-0404", "result": "pass", "date": "2026-09-01", "by": "user:fixture", "method": "manual"}
  ],
  "evidence": []
}
JSON
cat > "$PROC/docs/tests/acceptance/RELEASE-TEST.md" <<'MD'
---
type: "[[reference]]"
quoted_lines: warning
title: "Section order"
status: active
owner: user:fixture
created: 2026-09-14
updated: 2026-09-14
---

# Section order

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
cat > "$PROC/docs/tests/acceptance/release-test/the-bench.md" <<'MD'
---
type: "[[reference]]"
title: "Procedure — The bench"
status: active
owner: user:fixture
created: 2026-09-14
updated: 2026-09-14
section: "The bench"
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
has "and says which sections still have no procedure" 'no procedure yet for: No script'
hasnt "a check that states no expected result is not called a mismatch" 'quotes TST-0407'
hasnt "and citing a part that is NOT owed is not a failure"            'TST-0404'

variant() { # variant <name> <old line> <new line> -> echoes the repo path
  local dir="$TMP/proc-$1"
  rm -rf "$dir"; cp -R "$PROC" "$dir"
  OLD="$2" NEW="$3" python3 - "$dir/docs/tests/acceptance/release-test/the-bench.md" <<'PY'
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
# Decided in TASK-0120: a check belongs to one section (rule 3), so a tag from
# another section's procedure either tests it twice or hides it.
CROSS="$(variant cross '`TST-0403` `TST-0404.2`' '`TST-0403` `TST-0404.2` `TST-0405.1`')"
procfail "a tag naming a check another section claims is refused" "$CROSS" \
  'cites TST-0405, which the section "No script" claims'
BARE="$(variant bare '`TST-0401.1`' '`TST-0401`')"
procfail "a bare tag on a check that numbers its steps is refused" "$BARE" \
  'cites TST-0401 with no step number, and that check numbers 3 steps'
UNKNOWN="$(variant unknown '`TST-0402.1`' '`TST-0402.1` `TST-0999.1`')"
procfail "a tag naming no check at all is refused" "$UNKNOWN" \
  'cites TST-0999, which matches no acceptance check in this repo'
NOSECTION="$(variant nosection 'section: "The bench"' 'section: ""')"
procfail "a procedure naming no section is refused" "$NOSECTION" \
  'no .section:. in its frontmatter'
WRONGSECTION="$(variant wrongsection 'section: "The bench"' 'section: "The benches"')"
procfail "a procedure naming a section RELEASE-TEST.md does not have is refused" "$WRONGSECTION" \
  'matches no .### . heading in docs/tests/acceptance/RELEASE-TEST.md'
# project-os-dev ADR-0050: `sitting:` is the old name of `section:`. It is
# refused, and the message names the new key and the migration command.
OLDKEY="$(variant oldkey 'section: "The bench"' 'sitting: "The bench"')"
procfail "a procedure still keyed sitting: is refused, naming section:" "$OLDKEY" \
  '`sitting:` is the old name; it is now `section:`\. Run `python3 tools/scripts/migrate-release-test-names\.py --apply`'
OLDREADY="$TMP/proc-oldready"; rm -rf "$OLDREADY"; cp -R "$PROC" "$OLDREADY"
python3 - "$OLDREADY/docs/tests/acceptance/TST-0405-Fixture.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
p.write_text(t.replace("level: acceptance\n", "level: acceptance\nwalk_readiness_for:\n  testbed: {kind: decision, reason: \"Waits for a product call.\"}\n", 1), encoding="utf-8")
PY
procfail "a check still keyed walk_readiness_for: is refused, naming readiness_for:" "$OLDREADY" \
  '`walk_readiness_for` is the old name; it is now `readiness_for`'
TWOFILES="$TMP/proc-twofiles"; rm -rf "$TWOFILES"; cp -R "$PROC" "$TWOFILES"
cp "$TWOFILES/docs/tests/acceptance/release-test/the-bench.md" "$TWOFILES/docs/tests/acceptance/release-test/the-bench-again.md"
procfail "a second procedure for one section is refused" "$TWOFILES" \
  'a second procedure for "The bench"'
# A step no longer has to name its screen: the action line alone is enough
# (project-os-dev REQ-0033, TASK-0189). It used to draw a remark.
NOSCREEN="$(variant noscreen '2. **Ride cockpit (SUR-0002).** Start the workout.' '2. Start the workout.')"
out_noscreen="$(python3 "$SHEET" --check --platform testbed --repo-root "$NOSCREEN" 2>&1)"; code=$?
check "a step naming no screen passes the check" "$code" "$out_noscreen"
check "and draws no remark about a screen" \
  "$(printf '%s' "$out_noscreen" | grep -Eq 'names no screen' && echo 1 || echo 0)" "$out_noscreen"

# --- steps 6 and 7 of TST-0010: what the sheet prints
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PROC" 2>&1)"
has   "a section with a procedure says which file it tests"   '^From \[docs/tests/acceptance/release-test/the-bench\.md\]'
has   "the setup is printed once for the whole section, as the thing to do before starting" '^1\. The bench powered and the tablet awake\.$'
check "and exactly once" \
  "$(printf '%s' "$OUT" | grep -c 'The bench powered and the tablet awake\.$' | grep -q '^1$' && echo 0 || echo 1)" \
  "$(printf '%s' "$OUT" | grep -c 'The bench powered and the tablet awake\.$')"
has   "an owed step prints as its number and its one action line" '^- \[ \] \*\*1\.\*\* \*\*Equipment panel \(SUR-0001\)\.\*\* Open the panel\.$'
has   "its expectation lines keep their tags"                  'The panel lists the trainer\. `TST-0401\.1`'
hasnt "a step citing only checks that have passed is left out" 'Unpair everything'
has   "and the sheet says how many steps it left out"          '^1 step of it is left out'
has   "a step mixing an owed tag with a passed one still prints" 'The reading arrives\.'
has   "and prints only the tag it still owes beside that line"  '^  - The reading arrives\. `TST-0403`$'
has   "each printed step has its own tick box, numbered from 1 in the section" '^- \[ \] \*\*4\.\*\* '
hasnt "a section tested from a procedure prints no per-check rows" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0401[-.]'
has   "a section with no procedure prints per-check rows as before" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0405[-.]'
has   "and that row still carries its own setup, steps and expect"  '^    - It opens\. `TST-0405`$'

# A procedure that no longer covers what the release owes must not hide it.
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$UNCITED" 2>&1)"
has "a procedure the validator refuses says so on the sheet" 'has a procedure and it no longer matches what the release owes'
has "and names what is wrong with it"                        '^- The bench owes TST-0403'
has "and falls back to per-check rows, so nothing owed is hidden" '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0403[-.]'
has "including the check the procedure did cover"                 '^- \[ \] \*\*[0-9]+\.\*\* \[.*\]\([^)]*TST-0401[-.]'
# The sheet is not the only consumer: the cockpit renders `steps` from this
# payload. A refused procedure that still carried printable steps would show a
# stale script there while the sheet fell back here.
payload="$(SHEET_PATH="$SHEET" REPO_ROOT="$UNCITED" python3 - <<'PY'
import importlib.util as ilu, os, pathlib, sys
spec = ilu.spec_from_file_location("release_test", os.environ["SHEET_PATH"])
rt = ilu.module_from_spec(spec)
#: Registered before it runs: a dataclass whose annotations are strings looks
#: its own module up in sys.modules, and an unregistered one fails there.
sys.modules["release_test"] = rt
spec.loader.exec_module(rt)
sheet = rt.generate(pathlib.Path(os.environ["REPO_ROOT"]), "REL-0011", "testbed")
bench = [p for p in sheet.sections if p.section.name == "The bench"][0]
print("problems=%d steps=%d owed_checks=%d tested=%s"
      % (len(bench.procedure.problems), len(bench.steps),
         len(bench.owed_checks), bench.tested_from_procedure))
PY
)"
check "a refused procedure carries no printable steps in the payload" \
  "$(printf '%s' "$payload" | grep -q '^problems=1 steps=0 owed_checks=0 tested=False$' && echo 0 || echo 1)" "$payload"

# --check over every platform at once is what validate-docs.sh runs.
allout="$(python3 "$SHEET" --check --repo-root "$UNCITED" 2>&1)"; code=$?
check "--check with no platform reads every ledger it finds" \
  "$( { [[ $code -eq 1 ]] && printf '%s' "$allout" | grep -q 'testbed'; }; echo $?)" "exit $code: $allout"
# project-os-dev ISS-0089: a disagreement reads as an error to a reader who
# filters the output for ERROR, as the validator's own lines do.
check "every --check disagreement is marked ERROR [RELEASE-TEST]" \
  "$( { printf '%s\n' "$allout" | grep -q '^ERROR \[RELEASE-TEST\] release-test --check (testbed): '; ! printf '%s\n' "$allout" | grep -q '^release-test --check ([a-z]*): [^n]'; }; echo $?)" "$allout"
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
python3 - "$DUPNUM/docs/tests/acceptance/release-test/the-bench.md" <<'PY'
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
has "and the sheet numbers them by position, not by the digit" '^- \[ \] \*\*2\.\*\* \*\*Ride cockpit \(SUR-0002\)\.\*\* Start the workout\.$'

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
python3 - "$CHKNUM/docs/tests/acceptance/release-test/the-bench.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("   - The trainer holds the target. `TST-0401.3`\n", ""))
PY
procfail "and dropping one of them is still refused" "$CHKNUM" \
  'owes TST-0401 step 3 and no step cites it'

# A procedure covers its whole section, so it cites checks that have already
# passed. A reader that knew only the owed set called every such tag unknown.
check "the base fixture's procedure cites an already-passed check" \
  "$(grep -q '`TST-0404\.2`' "$PROC/docs/tests/acceptance/release-test/the-bench.md" && echo 0 || echo 1)"
OUT_JSON="$(python3 "$SHEET" --json --release REL-0011 --platform testbed --repo-root "$PROC" 2>&1)"
check "and the page keeps that line apart as passed, not as something to observe" \
  "$(printf '%s' "$OUT_JSON" | python3 -c 'import json,sys; p=json.load(sys.stdin); c=[c for s in p["sections"] for g in s["groups"] for c in g["checks"] if c["number"]==3 and s["number"]==1][0]; sys.exit(0 if any("TST-0404.2" in l["passed"] for l in c["expected"]) and all("TST-0404.2" not in l["tags"] for l in c["expected"]) else 1)'; echo $?)" "$OUT_JSON"

# A host may hold its own owed set and pass a smaller `checks` -- the cockpit
# does. `known` is what a tag is resolved against, so a procedure citing a
# check that has already passed must still be accepted. Asserted through the
# module's API, because the generator always passes the full set and so cannot
# reach this on its own.
known_out="$(SHEET_PATH="$SHEET" REPO_ROOT="$PROC" python3 - <<'PY'
import importlib.util as ilu, os, pathlib, sys
spec = ilu.spec_from_file_location("release_test", os.environ["SHEET_PATH"])
rt = ilu.module_from_spec(spec); sys.modules["release_test"] = rt
spec.loader.exec_module(rt)
root = pathlib.Path(os.environ["REPO_ROOT"])
read = rt.read_repo(root, "testbed")
owed = {c.id for c in rt.owed_checks(read.checks, read.events)}
thin = {i: c for i, c in read.checks.items() if i in owed}
sheet = rt.build_release_test(
    thin, read.events, read.sections, release="REL-0011", platform="testbed",
    surfaces=read.surfaces, surface_notes=read.surface_notes,
    procedures=read.procedures, known=read.checks, retired=read.retired,
    authored_order=read.authored, quoted_refused=read.quoted_refused)
bench = [p for p in sheet.sections if p.section.name == "The bench"][0]
print("problems=%d tested=%s" % (len(bench.procedure.problems),
                                 bench.tested_from_procedure))
PY
)"
check "a host passing only its owed checks still accepts a passed-check tag" \
  "$(printf '%s' "$known_out" | grep -q '^problems=0 tested=True$' && echo 0 || echo 1)" "$known_out"

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
# rule above caught every ReleaseTestError, so a ledger naming no platform and an
# entry dated 2026-13-45 both stopped being reported anywhere: the generator
# refused them and validate-docs.sh, which is the only thing that reads a
# ledger on every commit, did not. Found by independent review, round two.
BADLEDGER="$TMP/proc-badledger"; rm -rf "$BADLEDGER"; cp -R "$PROC" "$BADLEDGER"
cp "$BADLEDGER/docs/releases/ledgers/WORKING-testbed.json" "$BADLEDGER/docs/releases/ledgers/testbed.json"
out_bad="$(python3 "$SHEET" --check --quiet --repo-root "$BADLEDGER" 2>&1)"; code=$?
check "a ledger whose filename names no platform still fails --check, marked ERROR [RELEASE-TEST]" \
  "$( { [[ $code -eq 2 ]] && printf '%s' "$out_bad" | grep -q '^ERROR \[RELEASE-TEST\] .*does not name a platform'; }; echo $?)" \
  "exit $code: $out_bad"
rm "$BADLEDGER/docs/releases/ledgers/testbed.json"
python3 - "$BADLEDGER/docs/releases/ledgers/WORKING-testbed.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["entries"].append({"check": "TST-0401", "result": "pass", "date": "2026-13-45",
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


# --check refuses a check's broken `readiness_for` (FEAT-0033 review,
# 2026-09-24: removing that line in check_repo failed no test), names a
# platform the repo has no ledger for, and prints a problem that holds on
# every platform once rather than once per platform.
READY="$TMP/proc-readiness"; rm -rf "$READY"; cp -R "$PROC" "$READY"
FIRST="$(ls "$READY"/docs/tests/acceptance/TST-*.md | head -1)"
python3 - "$FIRST" <<'PY'
import sys
p = sys.argv[1]; lines = open(p).read().split("\n")
lines[1:1] = ["readiness_for:", "  testbed: {kind: maybe, reason: \"\"}", "  andriod: {kind: decision, reason: \"Choose.\"}"]
open(p, "w").write("\n".join(lines))
PY
out_ready="$(python3 "$SHEET" --check --platform testbed --quiet --repo-root "$READY" 2>&1)"; code=$?
check "--check fails on a malformed readiness_for" \
  "$( { [[ $code -eq 1 ]] && printf '%s' "$out_ready" | grep -q "readiness_for\` entry 'testbed' needs"; }; echo $?)" "exit $code: $out_ready"
check "--check names a readiness_for platform with no ledger" \
  "$(printf '%s' "$out_ready" | grep -q 'names platform andriod, and this repo keeps ledgers only for testbed'; echo $?)" "$out_ready"
cp "$READY/docs/releases/ledgers/WORKING-testbed.json" "$READY/docs/releases/ledgers/WORKING-bench.json"
out_both="$(python3 "$SHEET" --check --quiet --repo-root "$READY" 2>&1)"
check "a problem that holds on every platform prints once" \
  "$([[ $(printf '%s\n' "$out_both" | grep -c "entry 'testbed' needs") -eq 1 ]]; echo $?)" "$out_both"

# ---------------------------------------------------------------------------
# Tag-only expectation lines (project-os-dev ISS-0088, ADR-0049). A step may
# cite a check's step without quoting it; the sheet and the payload print the
# check's current Expect words, so editing the check breaks nothing.
# ---------------------------------------------------------------------------
TAGONLY="$(variant tagonly '   - The panel lists the trainer. `TST-0401.1`' '   - `TST-0401.1`')"
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$TAGONLY" 2>&1)"; code=$?
check "--check accepts a tag-only line" "$code" "$OUT"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$TAGONLY" 2>&1)"
has "the sheet prints the check's own words for it" '^  - The panel lists the trainer\. `TST-0401\.1`$'
check "only the Expect line paired with step 1, not all three" \
  "$([[ $(printf '%s\n' "$OUT" | grep -c 'TST-0401\.1') -eq 1 ]]; echo $?)" "$OUT"
hasnt "the bare tag line itself is not printed" '^   - `TST-0401\.1`$'
tag_payload() { SHEET_PATH="$SHEET" REPO_ROOT="$1" python3 - <<'PY2'
import importlib.util as ilu, os, pathlib, sys
spec = ilu.spec_from_file_location("release_test", os.environ["SHEET_PATH"])
rt = ilu.module_from_spec(spec); sys.modules["release_test"] = rt
spec.loader.exec_module(rt)
sheet = rt.generate(pathlib.Path(os.environ["REPO_ROOT"]), "REL-0011", "testbed")
bench = [p for p in sheet.sections if p.section.name == "The bench"][0]
step = [s for s in bench.steps if s.number == 1][0]
for e in step.expectations:
    print("%s|%s|%s" % (e.quote, ",".join("%s.%s" % t for t in e.tags), ",".join("%s.%s" % t for t in sorted(e.owed))))
PY2
}
pl="$(tag_payload "$TAGONLY")"
check "the payload carries the words, the tag and the owed part" \
  "$(printf '%s\n' "$pl" | grep -qx 'The panel lists the trainer.|TST-0401.1|TST-0401.1'; echo $?)" "$pl"

# Reword the check: the quoting procedure breaks, the tag-only one does not.
reword() { python3 - "$1/docs/tests/acceptance/TST-0401-Fixture.md" <<'PY2'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
assert "- The panel lists the trainer." in t
p.write_text(t.replace("- The panel lists the trainer.", "- The panel lists every paired trainer."))
PY2
}
QUOTED="$TMP/proc-quoted-reworded"; rm -rf "$QUOTED"; cp -R "$PROC" "$QUOTED"; reword "$QUOTED"
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$QUOTED" 2>&1)"; code=$?
check "a reworded check still breaks a procedure that quotes it (the ISS-0088 case)" \
  "$( { [[ $code -ne 0 ]] && printf '%s' "$OUT" | grep -q 'quotes TST-0401'; }; echo $?)" "exit $code: $OUT"
reword "$TAGONLY"
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$TAGONLY" 2>&1)"; code=$?
check "and does not break a tag-only one" "$code" "$OUT"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$TAGONLY" 2>&1)"
has "whose sheet prints the new words" '^  - The panel lists every paired trainer\. `TST-0401\.1`$'

# The sheet prints a check's Expect line as written: emphasis that runs to
# the end of the line keeps its closing marks (TASK-0186).
BOLD="$(variant bold '   - The panel lists the trainer. `TST-0401.1`' '   - `TST-0401.1`')"
python3 - "$BOLD/docs/tests/acceptance/TST-0401-Fixture.md" <<'PY2'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("- The panel lists the trainer.", "- Step 1: **the panel lists the trainer.** (`GRADE  N.N%`)"))
PY2
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$BOLD" 2>&1)"
has "a tag-only line keeps the check's emphasis whole and its code spacing" '^  - \*\*The panel lists the trainer\.\*\* \(`GRADE  N\.N%`\) `TST-0401\.1`$'

# unpair <repo>: TST-0404 gets a third Expect line for its two steps, so its
# steps and Expect lines no longer pair and a tag names all three.
unpair() { python3 - "$1/docs/tests/acceptance/TST-0404-Fixture.md" <<'PY2'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
assert "- The reading arrives." in t
p.write_text(t.replace("- The reading arrives.", "- The reading arrives.\n- The panel shows no error."))
PY2
}
# A check that does not pair steps with Expect lines: a tag `.N` would print
# every line, lines meant for other steps among them, so --check refuses the
# tag and names the check, the platform, the step count and the line count.
ALLLINES="$(variant alllines '   - The reading arrives. `TST-0403` `TST-0404.2`' '   - The reading arrives. `TST-0403`
   - `TST-0404.2`')"
unpair "$ALLLINES"
# TST-0403 numbers no steps and is cited by its bare id; a second Expect line
# gives it two lines for no numbered step, and that is not a pairing problem.
python3 - "$ALLLINES/docs/tests/acceptance/TST-0403-Fixture.md" <<'PY2'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
assert "- The reading arrives." in t
p.write_text(t.replace("- The reading arrives.", "- The reading arrives.\n- The panel stays quiet."))
PY2
procfail "a tag .N on a check whose Expect lines do not number one per step is refused, naming the check, platform and counts" "$ALLLINES" \
  'step 3 of .*the-bench\.md cites step 2 of TST-0404, and on testbed that check has 2 numbered steps and 3 Expect lines'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$ALLLINES" 2>&1)"
hasnt "a check cited by its bare id is not held to the pairing" 'of TST-0403, and on testbed'

# The converter: only what loses nothing, and --refresh for the rest.
WT="$PROC-tags"; rm -rf "$WT"; cp -R "$PROC" "$WT"
python3 - "$WT/docs/tests/acceptance/release-test/the-bench.md" <<'PY2'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("   - The reading arrives. `TST-0403` `TST-0404.2`",
                       "   - The reading arrives. `TST-0403`\n   - The reading arrives. `TST-0404.2`"))
PY2
unpair "$WT"
# A reader that has already gone, with every print written at once: the first
# print fails, and the rewrite must be done by then (TASK-0186).
PYTHONUNBUFFERED=1 python3 "$HERE/release-test-tags.py" --repo-root "$WT" --apply 2>/dev/null | (exit 0)
conv="$(python3 "$HERE/release-test-tags.py" --repo-root "$WT" 2>&1)"
proc="$(cat "$WT/docs/tests/acceptance/release-test/the-bench.md")"
check "the converter rewrites a line whose tag prints exactly its quote" \
  "$( { printf '%s' "$proc" | grep -qx '   - `TST-0401.1`' && printf '%s' "$proc" | grep -qx '   - `TST-0403`'; }; echo $?)" "$conv"
check "and keeps a line that quotes one of several unpaired Expect lines" \
  "$(printf '%s' "$proc" | grep -qx '   - The reading arrives. `TST-0404.2`'; echo $?)" "$conv"
# The tags left on the unpaired TST-0404 are refused (the pairing check
# above); nothing else in the converted procedure is.
only_unpaired() { printf '%s\n' "$1" | grep '^ERROR' | grep -vq 'of TST-0404, and on testbed that check has 2 numbered steps and 3 Expect lines' && echo 1 || echo 0; }
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$WT" 2>&1)"; code=$?
check "the converted procedure draws no --check problem but the unpaired TST-0404" "$(only_unpaired "$OUT")" "$OUT"

RF="$PROC-refresh"; rm -rf "$RF"; cp -R "$WT" "$RF"
(cd "$RF" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -q -m base)
python3 - "$RF/docs/tests/acceptance/TST-0404-Fixture.md" <<'PY2'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text()
assert "- The reading arrives.\n" in t
p.write_text(t.replace("- The reading arrives.\n", "- The reading arrives within a second.\n"))
PY2
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$RF" 2>&1)"; code=$?
check "rewording an unpaired Expect line breaks the quoting line" "$(printf '%s' "$OUT" | grep -q 'quotes TST-0404'; echo $?)" "$OUT"
ref="$(python3 "$HERE/release-test-tags.py" --repo-root "$RF" --refresh --apply 2>&1)"
check "--refresh re-quotes it from the check's current Expect" \
  "$(grep -qx '   - The reading arrives within a second. `TST-0404.2`' "$RF/docs/tests/acceptance/release-test/the-bench.md"; echo $?)" "$ref"
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$RF" 2>&1)"; code=$?
check "after which --check reports nothing but the unpaired TST-0404" "$(only_unpaired "$OUT")" "$OUT"

# ---------------------------------------------------------------------------
# Expect lines marked for one platform (project-os-dev TASK-0188, REQ-0034).
# A line starting `[testbed]` or `[bench]` prints only on that platform, a tag
# `.N` pairs with the Nth line that applies there, a bracketed platform with
# no ledger is refused, and a quoted procedure line is a warning.
# ---------------------------------------------------------------------------
PLAT="$TMP/proc-platforms"; rm -rf "$PLAT"; cp -R "$PROC" "$PLAT"
cp "$PLAT/docs/releases/ledgers/WORKING-testbed.json" "$PLAT/docs/releases/ledgers/WORKING-bench.json"
sed -i.bak 's/"platform": "testbed"/"platform": "bench"/' "$PLAT/docs/releases/ledgers/WORKING-bench.json"; rm -f "$PLAT"/docs/releases/ledgers/*.bak
python3 - "$PLAT" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
def edit(rel, old, new):
    p = root / rel; t = p.read_text(encoding="utf-8")
    assert old in t, (rel, old)
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
# Four Expect lines for three steps; on each platform three apply, so step N
# still pairs with line N there.
edit("docs/tests/acceptance/TST-0401-Fixture.md", "- The target power is shown.\n",
     "- [testbed] The target power is shown.\n- [bench] The target power reads in watts.\n")
edit("docs/tests/acceptance/release-test/the-bench.md",
     "   - The target power is shown. `TST-0401.2`", "   - `TST-0401.2`")
edit("docs/tests/acceptance/release-test/the-bench.md",
     "   - The trainer holds the target. `TST-0401.3`", "   - `TST-0401.3`")
# A section with no procedure prints per-check rows; one line is for bench only.
edit("docs/tests/acceptance/TST-0405-Fixture.md", "- It opens.", "- It opens.\n- [bench] It opens slowly.")
PY
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$PLAT" 2>&1)"; code=$?
check "--check passes a check whose Expect lines are marked per platform (testbed)" "$code" "$OUT"
OUT="$(python3 "$SHEET" --check --platform bench --repo-root "$PLAT" 2>&1)"; code=$?
check "and on the other platform (bench)" "$code" "$OUT"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$PLAT" 2>&1)"
has   "a line marked [testbed] prints on testbed, without its mark" '^  - The target power is shown\. `TST-0401\.2`$'
hasnt "a line marked [bench] does not print on testbed"             'reads in watts'
hasnt "no platform mark reaches the page"                           '\[(testbed|bench)\]'
has   "an unmarked line prints on testbed"                          'The panel lists the trainer\. `TST-0401\.1`'
# Four lines, three steps: without counting per platform the tag names all four.
check "tag .3 pairs with the third line that applies on testbed, and only that line" \
  "$( { printf '%s\n' "$OUT" | grep -qx '  - The trainer holds the target\. `TST-0401\.3`' && [[ $(printf '%s\n' "$OUT" | grep -c '`TST-0401\.3`') -eq 1 ]]; } && echo 0 || echo 1)" "$OUT"
has   "a per-check row prints its unmarked Expect line on testbed"  '^    - It opens\. `TST-0405`$'
hasnt "and leaves out the line marked for bench"                    'It opens slowly'
OUT="$(python3 "$SHEET" --release REL-0011 --platform bench --repo-root "$PLAT" 2>&1)"
has   "a line marked [bench] prints on bench, without its mark"     '^  - The target power reads in watts\. `TST-0401\.2`$'
hasnt "a line marked [testbed] does not print on bench"             'The target power is shown'
has   "an unmarked line prints on bench too"                        'The panel lists the trainer\. `TST-0401\.1`'
has   "a per-check row prints the bench line on bench, mark removed" '^    - It opens slowly\. `TST-0405`$'
# A bracketed platform with no ledger prints nowhere, so it is refused, naming
# the check and the line.
TYPO="$TMP/proc-platform-typo"; rm -rf "$TYPO"; cp -R "$PLAT" "$TYPO"
python3 - "$TYPO/docs/tests/acceptance/TST-0405-Fixture.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("- [bench] It opens slowly.", "- [bench] It opens slowly.\n- [andriod] It opens on the phone."))
PY
procfail "an Expect line marked for a platform with no ledger is refused, naming the check and the line" "$TYPO" \
  'TST-0405: an Expect line is marked \[andriod\], and this repo keeps ledgers only for bench, testbed: - \[andriod\] It opens on the phone\.'
# The last line of TST-0401 marked for bench leaves testbed two lines for three
# steps. Unrefused, tag .3 on testbed printed both lines, meant for steps 1 and
# 2, and nothing said so. Bench still has one line per step and passes.
SHORT="$TMP/proc-platform-short"; rm -rf "$SHORT"; cp -R "$PLAT" "$SHORT"
python3 - "$SHORT/docs/tests/acceptance/TST-0401-Fixture.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
assert "- The trainer holds the target." in t
p.write_text(t.replace("- The trainer holds the target.", "- [bench] The trainer holds the target."))
PY
procfail "a platform whose Expect lines do not number one per step refuses the tag .N, naming the platform and counts" "$SHORT" \
  'cites step 3 of TST-0401, and on testbed that check has 3 numbered steps and 2 Expect lines'
OUT="$(python3 "$SHEET" --check --platform bench --repo-root "$SHORT" 2>&1)"; code=$?
check "and the platform where they do pair still passes" "$code" "$OUT"
# With `quoted_lines: warning`, a quoted procedure line prints and --check still passes.
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$PLAT" 2>&1)"; code=$?
check "a quoted expectation line is reported as a warning and does not fail --check" \
  "$( { [[ $code -eq 0 ]] && printf '%s' "$OUT" | grep -q "^WARN  \[RELEASE-TEST\] .*step 1 of .*the-bench\.md quotes an expectation instead of giving its tags alone: 'The panel lists the trainer\.'"; }; echo $?)" "exit $code: $OUT"
check "a tag-only line draws no such warning" \
  "$(printf '%s' "$OUT" | grep -q 'quotes an expectation.*TST-0401\.2\|target power' && echo 1 || echo 0)" "$OUT"
QUIETW="$(python3 "$SHEET" --check --quiet --repo-root "$PLAT" 2>&1)"; code=$?
check "under --quiet the quoted lines are one line with their count, printed once for both platforms" \
  "$( { [[ $code -eq 0 ]] && [[ $(printf '%s\n' "$QUIETW" | grep -c 'WARN') -eq 1 ]] && printf '%s' "$QUIETW" | grep -q '^WARN  \[RELEASE-TEST\] release-test --check: 6 procedure line(s) state an expectation in their own words'; }; echo $?)" "exit $code: $QUIETW"
ACTIONTAG="$(variant actiontag '4. **Equipment panel (SUR-0001).** Unpair everything.
   - The panel is empty again. `TST-0404.1`' '4. **Equipment panel (SUR-0001).** Unpair everything. `TST-0404.1`')"
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$ACTIONTAG" 2>&1)"
check "tags on an action line are reported too" \
  "$(printf '%s' "$OUT" | grep -q 'step 4 of .*carries tags on its action line' && echo 0 || echo 1)" "$OUT"
# By default a quoted line is refused (the consumers have moved to tags alone);
# `quoted_lines: warning` in the section order file makes it a warning.
refused="$(SHEET_PATH="$SHEET" REPO_ROOT="$PLAT" python3 - <<'PY'
import importlib.util as ilu, os, pathlib, sys
spec = ilu.spec_from_file_location("release_test", os.environ["SHEET_PATH"])
rt = ilu.module_from_spec(spec); sys.modules["release_test"] = rt
spec.loader.exec_module(rt)
root = pathlib.Path(os.environ["REPO_ROOT"])
before = rt.check_repo(root, "testbed")[0]
order = root / "docs/tests/acceptance/RELEASE-TEST.md"
order.write_text(order.read_text().replace("quoted_lines: warning\n", "", 1))
after = rt.check_repo(root, "testbed")[0]
order.write_text(order.read_text().replace('type: "[[reference]]"\n', 'type: "[[reference]]"\nquoted_lines: warning\n', 1))
print("before=%d after=%d" % (sum("quotes an expectation" in p for p in before),
                              sum("quotes an expectation" in p for p in after)))
PY
)"
check "without quoted_lines: warning, a quoted line is refused by default" \
  "$(printf '%s' "$refused" | grep -qx 'before=0 after=6' && echo 0 || echo 1)" "$refused"
# release-test-tags.py --all rewrites every quoted line, so the warnings go.
ALL="$TMP/proc-platform-all"; rm -rf "$ALL"; cp -R "$PLAT" "$ALL"
cp "$ACTIONTAG/docs/tests/acceptance/release-test/the-bench.md" "$ALL/docs/tests/acceptance/release-test/the-bench.md"
python3 - "$ALL/docs/tests/acceptance/release-test/the-bench.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
for old, new in (("   - The target power is shown. `TST-0401.2`", "   - `TST-0401.2`"),
                 ("   - The trainer holds the target. `TST-0401.3`", "   - `TST-0401.3`")):
    t = t.replace(old, new)
p.write_text(t)
PY
allout="$(python3 "$HERE/release-test-tags.py" --repo-root "$ALL" --all --apply 2>&1)"
proc="$(cat "$ALL/docs/tests/acceptance/release-test/the-bench.md")"
check "--all rewrites a quoted line as its tags alone" \
  "$(printf '%s\n' "$proc" | grep -qx '   - `TST-0401.1`' && echo 0 || echo 1)" "$allout"
check "--all moves an action line's tags to a line of their own under it" \
  "$( { printf '%s\n' "$proc" | grep -qx '4. \*\*Equipment panel (SUR-0001).\*\* Unpair everything.' && printf '%s\n' "$proc" | grep -qx '   - `TST-0404.1`'; } && echo 0 || echo 1)" "$allout
$proc"
check "--all reports a line whose page text changes" \
  "$(printf '%s' "$allout" | grep -q "Nothing in this line is in any Expect section" && echo 1 || echo 0)" "$allout"
OUT="$(python3 "$SHEET" --check --repo-root "$ALL" 2>&1)"; code=$?
check "after --all, --check passes with no quoted-line warning on either platform" \
  "$( { [[ $code -eq 0 ]] && ! printf '%s' "$OUT" | grep -q 'quotes an expectation\|carries tags on its action line'; }; echo $?)" "exit $code: $OUT"
# The lossless rewrite counts per platform: a quote of the testbed line is
# exactly what testbed prints and not what bench prints, so it stays quoted.
LOSS="$TMP/proc-platform-loss"; rm -rf "$LOSS"; cp -R "$PLAT" "$LOSS"
python3 - "$LOSS/docs/tests/acceptance/release-test/the-bench.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("   - `TST-0401.2`", "   - The target power is shown. `TST-0401.2`"))
PY
lossout="$(python3 "$HERE/release-test-tags.py" --repo-root "$LOSS" 2>&1)"
check "the lossless rewrite keeps a quote that one platform would print differently" \
  "$(printf '%s' "$lossout" | grep -q "keep  .*step 2: TST-0401's tags print 1 Expect line(s) on bench, 'The target power reads in watts\.'" && echo 0 || echo 1)" "$lossout"
# ...and rewrites it when the step runs on testbed alone, where it is exactly
# what the page prints.
python3 - "$LOSS/docs/tests/acceptance/release-test/the-bench.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace('section: "The bench"\n', 'section: "The bench"\nstep_platforms:\n  2: [testbed]\n', 1))
PY
lossout="$(python3 "$HERE/release-test-tags.py" --repo-root "$LOSS" 2>&1)"
check "and rewrites it when the step runs only on the platform that prints those words" \
  "$(printf '%s' "$lossout" | grep -q 'the-bench.md: - `TST-0401.2`' && echo 0 || echo 1)" "$lossout"

# ---------------------------------------------------------------------------
# Groups (project-os-dev TASK-0189, REQ-0033). A `### ` heading under
# `## Steps` starts a group and a `Start:` line under it is the group's start
# state. `state_for:` is still read, with a warning. `readiness_for:` may name
# the result the tester is offered, and only a stored result value.
# ---------------------------------------------------------------------------
GRPS="$TMP/proc-groups"; rm -rf "$GRPS"; cp -R "$PROC" "$GRPS"
cp "$GRPS/docs/releases/ledgers/WORKING-testbed.json" "$GRPS/docs/releases/ledgers/WORKING-bench.json"
sed -i.bak 's/"platform": "testbed"/"platform": "bench"/' "$GRPS/docs/releases/ledgers/WORKING-bench.json"; rm -f "$GRPS"/docs/releases/ledgers/*.bak
cat > "$GRPS/docs/tests/acceptance/release-test/the-bench.md" <<'MD'
---
type: "[[reference]]"
title: "Procedure — The bench"
status: active
owner: user:fixture
created: 2026-09-27
updated: 2026-09-27
section: "The bench"
step_platforms:
  2: [bench]
action_for:
  1: {testbed: "Open the panel from the top bar."}
readiness_for:
  6: {kind: decision, reason: "Waits for a product call.", result: question}
---

# Procedure — The bench

## Setup

The bench powered and the tablet awake.

## Steps

### The panel

Start: The trainer connected, nothing else bound.

1. Open the panel.
   - `TST-0401.1`
   - `TST-0402.1`

### Riding

Start: A ride running on the trainer.

2. Plug in the bench trainer.
3. Start the workout.
   - `TST-0401.2`
   - `TST-0402.2`
4. Swap the trainer and read the panel.
   - `TST-0401.3`
   - `TST-0403` `TST-0404.2`
5. Unpair everything.
   - `TST-0404.1`
6. Reboot the tablet.
   - `TST-0407.1`
MD
OUT="$(python3 "$SHEET" --check --repo-root "$GRPS" 2>&1)"; code=$?
check "--check passes a grouped procedure with Start lines and actions that name no screen" \
  "$( { [[ $code -eq 0 ]] && ! printf '%s' "$OUT" | grep -q 'WARN\|ERROR'; }; echo $?)" "exit $code: $OUT"
groups="$(SHEET_PATH="$SHEET" REPO_ROOT="$GRPS" python3 - <<'PY'
import importlib.util as ilu, os, pathlib, sys
spec = ilu.spec_from_file_location("release_test", os.environ["SHEET_PATH"])
rt = ilu.module_from_spec(spec); sys.modules["release_test"] = rt
spec.loader.exec_module(rt)
root = pathlib.Path(os.environ["REPO_ROOT"])
proc = rt.load_procedures(root / "docs", root)[0]
for g in proc.groups:
    print("%s|%s|%s" % (g.title, g.start, ",".join(str(n) for n in g.steps)))
print("step4=%s" % [s.group for s in proc.steps if s.number == 4][0])
PY
)"
check "the generator reads each group's heading, Start line and steps" \
  "$(printf '%s\n' "$groups" | tr '\n' '#' | grep -qx 'The panel|The trainer connected, nothing else bound.|1#Riding|A ride running on the trainer.|2,3,4,5,6#step4=Riding#' && echo 0 || echo 1)" "$groups"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$GRPS" 2>&1)"
has "a group's Start line is printed once under its heading" '^Start: The trainer connected, nothing else bound\.$'
# Step 2, the first of "Riding", runs on bench only; on testbed the group
# starts at step 3, and the Start line must reach it rather than the last one.
s3="$(printf '%s\n' "$OUT" | awk '/^#### Riding/{on=1;next} on&&/^- \[ \]/{exit} on')"
check "a group whose first step is on the other platform states its start at its first step here" \
  "$(printf '%s' "$s3" | grep -qx 'Start: A ride running on the trainer\.' && echo 0 || echo 1)" "$s3"
# Step 5 has passed and is left out, so step 6 follows a gap: the start of
# "Riding" is printed again before it.
has   "a group's start prints again before a check that follows skipped ones" '^Start again: A ride running on the trainer\.$'
check "and only there" \
  "$(printf '%s' "$OUT" | grep -c 'A ride running on the trainer\.' | grep -q '^2$' && echo 0 || echo 1)" \
  "$(printf '%s' "$OUT" | grep -c 'A ride running on the trainer\.')"
# The Markdown sheet is rendered from the JSON payload, so the two carry the
# same sections, groups, numbers and lines. Rendering the JSON the generator
# printed gives back the sheet it printed, byte for byte.
python3 "$SHEET" --json --release REL-0011 --platform testbed --repo-root "$GRPS" > "$TMP/grps.json" 2>&1
python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$GRPS" > "$TMP/grps.md" 2>&1
same="$(SHEET_PATH="$SHEET" JSON="$TMP/grps.json" MD="$TMP/grps.md" python3 - <<'PY'
import importlib.util as ilu, json, os, sys
spec = ilu.spec_from_file_location("release_test", os.environ["SHEET_PATH"])
rt = ilu.module_from_spec(spec); sys.modules["release_test"] = rt
spec.loader.exec_module(rt)
page = json.load(open(os.environ["JSON"]))
md = open(os.environ["MD"]).read()
numbers = [c["number"] for s in page["sections"] for g in s["groups"] for c in g["checks"]]
print("same" if rt.render_page(page) == md and numbers else "differ")
PY
)"
check "the JSON payload renders to exactly the Markdown sheet" "$([[ "$same" == same ]]; echo $?)" "$same"
has   "action_for replaces the whole action when the step names no screen" '^- \[ \] \*\*1\.\*\* Open the panel from the top bar\.$'
hasnt "and the authored action is not printed beside it"                    '\*\* Open the panel\.$'
has   "a declared readiness result is printed as the suggested result"      'Waits for a product call\. Suggested: Question\.'
# state_for still works on a procedure that has not moved to groups, and warns.
OLDSTATE="$(variant oldstate 'section: "The bench"' 'section: "The bench"
state_for:
  2: "The workout is running."')"
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$OLDSTATE" 2>&1)"; code=$?
check "a procedure keeping state_for: passes and is warned that Start: replaces it" \
  "$( { [[ $code -eq 0 ]] && printf '%s' "$OUT" | grep -q '^WARN  \[RELEASE-TEST\] .*the-bench\.md: `state_for:` is replaced by a `Start:` line'; }; echo $?)" "exit $code: $OUT"
QUIETS="$(python3 "$SHEET" --check --quiet --platform testbed --repo-root "$OLDSTATE" 2>&1)"
check "under --quiet the state_for warning is one counted line" \
  "$(printf '%s' "$QUIETS" | grep -q '^WARN  \[RELEASE-TEST\] release-test --check: 1 procedure(s) still declare `state_for:`' && echo 0 || echo 1)" "$QUIETS"
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$OLDSTATE" 2>&1)"
has "and its state_for is still printed" '^Start: The workout is running\.$'
# A Start line and state_for on the same step are two instructions for one thing.
TWICE_START="$TMP/proc-groups-twice"; rm -rf "$TWICE_START"; cp -R "$GRPS" "$TWICE_START"
python3 - "$TWICE_START/docs/tests/acceptance/release-test/the-bench.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace('section: "The bench"\n', 'section: "The bench"\nstate_for:\n  1: "Something else."\n', 1))
PY
procfail "a Start line and state_for on the same step are refused" "$TWICE_START" \
  'step 1 has a start state twice, from the `Start:` line of "The panel" and from `state_for`'
# result: must be a stored result value, on a procedure step and on a check.
BADRESULT="$TMP/proc-groups-badresult"; rm -rf "$BADRESULT"; cp -R "$GRPS" "$BADRESULT"
sed -i.bak 's/result: question}/result: maybe}/' "$BADRESULT/docs/tests/acceptance/release-test/the-bench.md"; rm -f "$BADRESULT"/docs/tests/acceptance/release-test/*.bak
procfail "a procedure readiness result that is not a stored value is refused" "$BADRESULT" \
  "readiness_for. entry '6' has .result: maybe.; a result is one of pass, partial, na, excused, blocked, fail, question"
CHKRESULT="$TMP/proc-groups-checkresult"; rm -rf "$CHKRESULT"; cp -R "$GRPS" "$CHKRESULT"
python3 - "$CHKRESULT/docs/tests/acceptance/TST-0405-Fixture.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace("level: acceptance\n", 'level: acceptance\nreadiness_for:\n  testbed: {kind: preparation, reason: "Bring the meter.", result: blocked}\n', 1))
PY
OUT="$(python3 "$SHEET" --release REL-0011 --platform testbed --repo-root "$CHKRESULT" 2>&1)"
has "a check's readiness result is printed on its row" 'Bring the meter\. Suggested: Blocked\.'
sed -i.bak 's/result: blocked}/result: skipped}/' "$CHKRESULT/docs/tests/acceptance/TST-0405-Fixture.md"; rm -f "$CHKRESULT"/docs/tests/acceptance/*.bak
procfail "a check readiness result that is not a stored value is refused" "$CHKRESULT" \
  "readiness_for. entry 'testbed' has .result: skipped."

# ---------------------------------------------------------------------------
# REQ-0036 (TASK-0192): the length check counts the words a tester sees, and
# reports an action line, an expected line or a section over its limit.
# ---------------------------------------------------------------------------
LEN="$TMP/proc-length"; rm -rf "$LEN"; cp -R "$GRPS" "$LEN"
python3 - "$LEN" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
proc = root / "docs/tests/acceptance/release-test/the-bench.md"
t = proc.read_text()
t = t.replace("3. Start the workout.",
              "3. Start the workout from the list of workouts on the main screen, then wait until the trainer holds the target power steadily.", 1)
proc.write_text(t)
chk = next((root / "docs/tests/acceptance").glob("TST-0402-*.md"))
t = chk.read_text()
t = t.replace("- The slot reads empty.",
              "- The slot reads empty, and it stays empty for the whole ride, whatever the trainer does and however often the rider opens and closes the panel.", 1)
chk.write_text(t)
PY
# The limits and the budget are set in the section order file's frontmatter.
limits() { # limits <dir> <yaml map>
  python3 - "$1/docs/tests/acceptance/RELEASE-TEST.md" "$2" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); t = p.read_text()
p.write_text(t.replace('type: "[[reference]]"\n', 'type: "[[reference]]"\nlength_limits: %s\n' % sys.argv[2], 1))
PY
}
# By default the reports are errors (project-os-dev TASK-0196).
DEF="$TMP/proc-length-default"; rm -rf "$DEF"; cp -R "$LEN" "$DEF"
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$DEF" 2>&1)"; code=$?
check "by default an over-long line fails --check" "$([[ $code -eq 1 ]]; echo $?)" "exit $code: $OUT"
has   "and is printed as an error" '^ERROR \[RELEASE-TEST\] .*check 2 .*the action is'
limits "$LEN" '{error: false}'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$LEN" 2>&1)"; code=$?
check "with error: false an over-long line is a warning, and --check still passes" "$code" "$OUT"
has "an action over 20 words is reported with its section, check number and tag" \
  '^WARN  \[RELEASE-TEST\] .*section 1, "The bench", check 2 \(`TST-0401\.2` `TST-0402\.2`\): the action is 2[0-9] words, over the limit of 20: "Start the workout from the list of workouts ...'
has "an expected line over 25 words is reported with its own tag" \
  '^WARN  \[RELEASE-TEST\] .*section 1, "The bench", check 1 \(`TST-0402\.1`\): an expected line is 2[6-9] words, over the limit of 25'
hasnt "a short line is not reported" 'check 1 \(`TST-0401\.1`\)'
hasnt "a section inside its budget is not reported" 'over its budget'
QUIETLEN="$(python3 "$SHEET" --check --quiet --platform testbed --repo-root "$LEN" 2>&1)"
check "under --quiet the length warnings are one counted line" \
  "$(printf '%s' "$QUIETLEN" | grep -q '^WARN  \[RELEASE-TEST\] release-test --check: 2 line(s) or section(s) are longer than their word limit' && echo 0 || echo 1)" "$QUIETLEN"
BUDGET="$TMP/proc-length-budget"; rm -rf "$BUDGET"; cp -R "$DEF" "$BUDGET"
limits "$BUDGET" '{action: 40, expected: 40, section_base: 10, section_per_check: 5, error: false}'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$BUDGET" 2>&1)"; code=$?
hasnt "a raised action limit lets the long action through" 'the action is'
hasnt "and a raised expected limit the long line"            'an expected line is'
has   "a section over its budget is reported with the sum" \
  '^WARN  \[RELEASE-TEST\] .*Section 1, "The bench" prints [0-9]+ words, over its budget of 30 \(10 \+ 5 for each of its 4 checks\)'
STRICT="$TMP/proc-length-strict"; rm -rf "$STRICT"; cp -R "$DEF" "$STRICT"
limits "$STRICT" '{error: true}'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$STRICT" 2>&1)"; code=$?
check "with error: true an over-long line fails --check" "$([[ $code -eq 1 ]]; echo $?)" "exit $code: $OUT"
has   "and is printed as an error" '^ERROR \[RELEASE-TEST\] .*check 2 .*the action is'
BADLIM="$TMP/proc-length-bad"; rm -rf "$BADLIM"; cp -R "$GRPS" "$BADLIM"
limits "$BADLIM" '{action: 0, words: 30}'
OUT="$(python3 "$SHEET" --check --platform testbed --repo-root "$BADLIM" 2>&1)"; code=$?
check "a malformed length_limits fails --check" "$([[ $code -eq 1 ]]; echo $?)" "exit $code: $OUT"
has   "naming an unknown key"   '`length_limits` has `words`; the keys are action, error, expected, section_base, section_per_check'
has   "and a limit that is not above 0" '`length_limits.action` must be a whole number of words above 0'

echo "test-release-test: $assertions assertions, $failures failure(s)"
[[ "$failures" -eq 0 ]]

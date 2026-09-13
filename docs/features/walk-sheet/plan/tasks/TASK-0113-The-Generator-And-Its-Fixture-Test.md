---
type: "[[task]]"
id: TASK-0113
aliases: ["TASK-0113"]
title: "tools/scripts/walk-sheet.py generates the sheet from the ledger, the notes and WALK.md, and test-walk-sheet.sh proves the rows, the order, the survey and the labels on a fixture"
status: done
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]] rules 1 to 5 and 7", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]"]
parent: "[[FEAT-0029-The-Walk-Sheet]]"
effort: L
due: ""
depends: ["[[TASK-0110-ADR-0027s-Four-Headings-Land-In-The-Test-Template]]", "[[TASK-0111-TESTING-md-States-The-Walk-Once]]", "[[TASK-0112-The-WALK-md-Template]]"]
blocks: ["[[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[ISS-0059-A-New-Project-Starts-On-The-Pre-Ledger-Write-Path]]", "[[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger]]", "[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
tests: ["[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
---

# The generator and its fixture test

## What

`python3 tools/scripts/walk-sheet.py --release REL-0017 --platform android` prints a walk sheet to stdout, or writes it with `--out PATH`. It reads three things and nothing else: the acceptance notes (`level: acceptance`, their `area:`, `after:`, `covers:`, and the Setup, Steps and Expect sections), the ledgers under `docs/releases/ledgers/` for the platform (sealed and working), and `docs/tests/acceptance/WALK.md`. It writes markdown a person walks from and never reads a sheet back.

## What the sheet contains, top to bottom

1. **A header**: release id, platform, the date generated, the count of owed rows, the count of sittings. No duration anywhere.
2. **The survey.** For every owed check whose latest ledger event is an invalidation: group by surface (`area:`, or the `SUR-*` note whose title matches). Under each surface, the invalidating ids from `invalidated_by:` with the titles of those task and change notes, and the `## Acceptance checks reopened` section of each such note quoted when present. If the repo's `SNAPSHOT.yaml` or WALK.md names a gallery command (an optional `gallery:` line in WALK.md's frontmatter is the simplest place), print it under the survey as "Regenerate and compare: `<command>`".
3. **The sittings**, in WALK.md order, omitting any with nothing owed. Under each: its `state`, its `bench`, then the rows. A row is: the check id as a link to the note, its title, "Setup:" followed by the Setup section or "not stated", the Steps as a numbered list, the Expect lines, and an empty tick box. Rows are ordered by `after:` topologically, then by id.
4. **"Unplaced"**, the final sitting, for owed checks no sitting claimed, with the same row shape.

The owed predicate is: a manual check (no `command:`; section feature or regression per the cockpit's ADR-0039, which the generator reproduces from `command:` and `covers:`) with no surviving clearing verdict in the ledger for the platform, where clearing is `pass`, `partial`, `na` or `excused` and an invalidation dated after a verdict overtakes it. This is the cockpit's `ledger.owed()`; the fixture test carries a ledger the cockpit's tests also use so the two cannot drift silently.

## Definition of Done

- [x] `~/Dev/repos/project-os/tools/scripts/walk-sheet.py` exists, standard library only, with `--release`, `--platform`, `--out`, `--repo-root` and `--help` whose text links to TESTING.md "The walk" and states that a repo without `SUR-*` notes groups the survey by `area:` string.
- [x] Running it in a repo with no `docs/releases/ledgers/` exits 2 with a one-line message naming project-os-dev ISS-0059 and saying a ledger is created by the first verdict written through the ledger path.
- [x] `~/Dev/repos/project-os/tools/scripts/test-walk-sheet.sh` builds a fixture repo under a temp dir (six acceptance notes across three areas, one with `after:`, one with no Setup heading, one with a `command:`; a working ledger with two passes, one excused, one invalidation after a pass, one never-walked; a WALK.md with two sittings claiming two of the three areas and one check by id) and asserts: the `command:` check is absent; the excused and passed checks are absent; the invalidated and never-walked checks are present; the survey names the invalidated check's area and its `invalidated_by:` id with the note's title; sitting order is file order; the `after:` check follows its prerequisite; the unclaimed area's check is under "Unplaced"; the Setup-less row prints "Setup: not stated"; the output contains no string matching a duration (`min`, `hour`, `~`).
- [~] A `TST-*` note carries `command:` for the harness and `covers: [FEAT-0029]`, following ADR-0025 (no verdict on the note). **Reconciled, not delivered as written**: the note is [[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order|TST-0009]] in *this* repo, at `docs/features/walk-sheet/plan/tests/`, with `command: bash ../project-os/tools/scripts/test-walk-sheet.sh`. That is where TST-0005 to TST-0008 already live and how all four already reach their scripts; putting it in the template's `docs/tests/` instead would seed a note about the template's own harness into every project created from it. The consequence the DoD was reaching for is real and is now filed as [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]]: the template's own CI runs none of its seven harnesses.
- [x] `tools/scripts/README` or the scripts index the template keeps lists the script in one line.
- [x] ADR-0029 acceptance box 3 (may a generated sheet be committed) is decided and recorded; the default for `--out` follows it.

## Steps

- [x] Reuse the frontmatter reader and note walker the other `tools/scripts/*.py` share; do not add a YAML dependency.
- [x] Implement the ledger reader: parse every `REL-*-<platform>.json` and `WORKING-<platform>.json`, resolve last-event-wins per check with an invalidation overtaking an earlier verdict, exactly as the cockpit's `ledger.resolve()` does. Read that file once before writing this one.
- [x] Implement the section predicate from `command:` and `covers:`.
- [x] Implement the survey, the sitting placement, the `after:` sort (detect a cycle and print the checks in id order with a warning line rather than failing).
- [x] Implement the renderer; print each row's Steps and Expect verbatim from the note, and never summarise them.
- [x] Write the fixture test and the TST note; run both.
- [x] Run the generator against your-trainer at HEAD for REL-0017 android and paste the header and the survey section into this note as evidence of shape, not as a verdict.

## Notes

- The sheet's count of owed rows will differ from what `validate-docs.py` reports while ISS-0060 is open, because the validator reads `mark:` on the note. Say so in the header as one line: "The validator counts from mark:; this sheet counts from the ledger (ISS-0060)." Remove the line when ISS-0060 closes.
- No time estimates. A `~10 min` in a Setup section is the check author's text and prints verbatim; the generator adds none of its own and the fixture test asserts only on the generator's own strings.
- Print Steps and Expect from the note even when the note still uses the pre-ADR-0027 headings Procedure and Expected results; map those two names as fallbacks so a corpus not yet rewritten on contact still yields a walkable row. Setup has no fallback, which is the point of "not stated".

## Evidence

- `~/Dev/repos/project-os/tools/scripts/walk-sheet.py`, standard library only, `--release --platform --out --repo-root`. Its `--help` epilogue links TESTING.md "The walk", says the survey groups by the `SUR-*` note whose title matches a check's `area:` and by the `area:` string alone where a repo keeps no surface notes, and says a sheet kept as a record is never edited and never read back.
- **The owed predicate is the cockpit's, checked rather than claimed.** Run over your-trainer's live corpus on 2026-09-13: 431 acceptance notes after retired ones are dropped, 366 of them manual. `ledger.owed()` from project-os-cockpit and this generator's `resolve()` returned the same 39 owed checks on android and the same 327 on ios, with zero differences in the resolved verdicts, and `section_of` agreed on every note. The same comparison on the cockpit's own corpus returns 3 and 3.
- `~/Dev/repos/project-os/tools/scripts/test-walk-sheet.sh`: **80 assertions, 0 failures**, over four fixture repos — the walk itself, the ledger's resolution layer, the note and WALK.md shapes a real corpus turns out to have, and the four refusals. Nine checks in the first fixture rather than the six sketched here; six cannot carry a passed, an excused, an automated, an invalidated, an ordered pair and an unplaced row at once.
- **Adequacy.** Five mutations against the pristine harness: the automated exclusion removed (3 failures), sittings sorted by name (2), `after:` edges dropped (1), an invalidation no longer clearing a verdict (10), the "Setup: not stated" label removed (27, but that edit also broke the module, so it proves less). Reverted each time; pristine tree passes.
- [[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order|TST-0009]] carries `command: bash ../project-os/tools/scripts/test-walk-sheet.sh` and `covers: [[FEAT-0029]]`, following ADR-0025: the note records no verdict.
- ADR-0029 acceptance box 3 is decided and ticked: `--out` has no default, the sheet goes to stdout, and nothing enters git unless a person names a path.

## What was not done, and why

- **The template keeps no scripts index.** There is no `tools/scripts/README`, and no file lists the eighteen scripts. Rather than start one inside this task, the generator is named where a person looks for it: TESTING.md "The walk" (twice), `SCHEMAS.md`, `docs/tests/README.md`, and the release-prep and release-verification skills (TASK-0114).
- **The generator and the cockpit scope the corpus differently, and that is the cockpit's call.** `walk-sheet.py` reads every `level: acceptance` note under `docs/`, which is what LIFECYCLE.md "Test storage" allows; `acceptance.load_notes` globs `docs/tests/acceptance/TST-*.md` alone. On your-trainer that is 649 notes against 431. Both agree on every note they both see, so nothing is wrong today, but the two could report different owed counts for one corpus, which is the disagreement rule 7 exists to prevent. Filed as [[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently|ISS-0063]].

## Two defects the harness did not catch, found by reading a real sheet

The 32-assertion suite passed while both of these were live. They were found by generating your-trainer's REL-0017 sheet and reading it, which is the check no fixture performs.

1. **Every row linked its note by an absolute filesystem path** — `](/Users/Edwin/Dev/repos/your-trainer/docs/tests/...)` — so a sheet was unusable in anyone else's checkout. `load_checks` now takes `repo_root=` and records the path relative to it.
2. **Most owed rows printed "the note states no steps"** — 53 of the 61 the sheet then reported, and 31 of the 39 that survive the retired-check fix below. The pre-ADR-0027 corpus keeps a check's whole procedure in an unheaded paragraph under the title, so neither `## Steps` nor `## Procedure` exists on it — and the two named fallbacks TASK-0113 asked for cover neither. A sheet whose rows are mostly empty fails rule 5 on the one corpus large enough to need it. `lead_paragraph()` now prints that prose under "**Steps: no heading.**", so the row is walkable and still reads as a worklist entry. Every row now carries its procedure text.

The suite grew to **38 assertions** for both, and three fresh mutations confirm the additions guard: reverting the relative path (2 failures), removing the lead fallback (2), and letting the fallback run past the next heading (1). The general lesson is recorded rather than the two fixes: a fixture asserts what its author thought to put in the fixture, and the corpus is where the shapes nobody anticipated live.

## Round one of the independent review, and what it changed

The review reproduced ten findings and returned `changes-requested`. Six were defects in the generator and are fixed here; the rest are recorded where they belong.

- **An invalidation naming a change note produced an empty survey entry.** Two causes, both fixed. The id pattern was `\d{3,4}`, and a change id carries an eight-digit date, so `CHG-20260913-The-Banner-Moves` matched nothing. And `CHG` is deliberately absent from the validator's `ID_PREFIXES`, so even a matched id resolved to no note: `change_notes()` is a second index over `docs/changes/`, keyed by full id, by filename stem, and by the canonical `CHG-<date>` where that picks out one note. REQ-0028 criterion 2 says "tasks **and changes**", so this one blocked.
- **`resolve()` and the cockpit's `ledger.owed()` disagreed when `sealed:` and `release:` did.** The ledgers were sorted on `sealed` and excuse expiry decided on `release`; the cockpit uses `sealed` for both. A ledger with `sealed` and no `release` lost an owed row here and kept it there — which ADR-0029's Conformance clause calls a defect in the generator. `Event.working` is now derived from `sealed` alone.
- **A mistyped `--platform` printed a confident sheet of every check in the repo**, 545 rows on your-trainer, with no warning. `platforms()` now refuses an unknown name and lists the ones this repo has.
- **A block-style YAML list in WALK.md vanished silently.** ADR-0029 acceptance box 1 fixes one syntax and calls a second a defect, so the parser did not learn block style; it reports it, which is what dropping it quietly was not doing.
- **`lead_paragraph()` took the first prose in the file, not the prose under the title**, so an HTML comment above a check's title became its steps and rendered as a blank.
- **`--release` was a label read by nothing**, so a sheet could name a release it did not describe. Naming an already-sealed release now prints a Note saying the sheet is what the platform owes now.

Two findings were about the documents, and both were amendments rather than fixes: TESTING.md rule 5 now states all three heading fallbacks, and rule 8 now says the *generator* writes no duration while quoted note text prints verbatim — a real sheet carries three, all of them the check author's words. REQ-0028's Amendments section records the matching criteria changes.

Two were filed rather than fixed: [[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect|ISS-0064]] and [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]].

**The guarding finding was the sharpest.** The fixture had one open ledger and no sealed one, so the whole expiry layer — an excuse expiring with its release, a persisting verdict surviving a transient one, the order two sealed ledgers resolve in — was unexercised, and the reviewer mutated all three without the suite noticing. Twelve of its twenty-two extra mutations survived. Eleven of those twelve are now caught; the twelfth, misrouting the regression branch, changes no sheet by construction, because feature and regression are both manual and a row does not say which it is. That is now said in the code rather than left for the next reader.

## Two more defects, found downstream

The cockpit built its page against this generator the same day and filed two findings, both owned here and both fixed before this landed.

- **project-os-cockpit ISS-0303 — a retired check was still being asked.** `load_checks` read `type:` and `level:` and never `status:`. your-trainer keeps 217 retired acceptance checks, so its REL-0017 android sheet went from 61 owed rows to **39**; both implementations now load the same 431 notes and agree on 39 for android, 327 for ios, and 3 on the cockpit's own corpus. The fix is narrower than the issue proposed: adding `superseded` beside `retired` introduced a second disagreement, because `acceptance._is_retired` matches `retired` alone and `superseded` is not a legal `[[test]]` status. Both branches are asserted.
- **project-os-cockpit ISS-0304 — a comma inside a quoted walk-order entry split it in two.** `_inline_list` split first and stripped quotes after, so the quotes protected nothing and one bench sentence became two items, the second an instruction to fetch nothing. The split now respects quotes, following `_strip_comment`'s existing shape.

The harness is 80 assertions; the two fixes and the narrowness of the first are each mutated and caught. Neither defect was found by the independent review or by the fixture — both came from pointing a second implementation at the same corpus, which is what bundling was decided for.

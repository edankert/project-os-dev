---
type: "[[task]]"
id: TASK-0191
aliases: ["TASK-0191"]
title: "Change notes declare their platforms, and each section lists what changed on its own screens for this platform"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0187]]"]
blocks: []
related: ["[[REQ-0035-Each-Section-Says-What-Changed-On-This-Platform]]", "[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey]]"]
tests: ["[[TST-0044-Each-Section-Lists-What-Changed-On-Its-Own-Screens-For-One-Platform]]"]
---

# Change notes declare their platforms, and each section lists what changed on its own screens for this platform

"What changed" moves from one 4,400-word list at the top to a short list at the head of each section, for one platform.

## Definition of Done
- [x] `docs/__templates__/change.md` and SCHEMAS.md gain `platforms:`, and an Impact line may be marked `[android]` or `[ios]`. project-os 0a14cef: the template carries `platforms: []` with a comment and shows a marked line; SCHEMAS.md, "`change.md`", states the field and the mark. `Change.platforms`, `Change.marks` and `Change.on(platform)` read them.
- [x] The validator reports a change note with a screen in its Impact list and no `platforms:`. It is a warning for notes created before this lands. `release-test.py --check` warns for a note created before 2026-09-28 (`PLATFORMS_REQUIRED_FROM`) and refuses one created on or after it, and only in a project with ledgers for more than one platform. A platform with no ledger is refused. TST-0044; mutations: new note not refused, 1 failure; unknown platform not refused, 1.
- [x] Each section lists only changes to its own screens on this platform, grouped by screen, one line per change. `Placed.what_changed`, built by `build_what_changed(..., platform, keep=...)`; `screen_homes` gives each screen one section. TST-0044; mutations: platform ignored, 1; marked line kept, 1; section share unfiltered, 2 and 1 unit.
- [x] The generator reads `docs/tests/acceptance/release-test/what-changed-<platform>.md` when its frontmatter tag is the last release tag. Otherwise it uses the Impact sentences and prints one line saying the short lines are missing or out of date. `load_short_lines`, `short_lines_for`; the line starts "**Short lines not used:**". New template `docs/__templates__/what-changed.md`; SCHEMAS.md, "`what-changed.md`". Mutations: tag not compared, 2; short lines not used, 2.
- [x] The validator reports a change in range with no short line in that file. A `--check` warning of kind `short_lines`, also for a line naming no change note, only while the file names the last release tag. Mutation: missing line not warned, 1.
- [x] A candidate screenshot whose last commit is older than the change note that altered its screen is flagged with its date. `stale_finder` compares commit order, not clock time, so two commits in one second still compare; a picture with uncommitted edits counts as new. Mutations: flag off, 2; uncommitted picture flagged, 1.
- [x] A changed screen that belongs to no section is listed once on the platform overview. `ReleaseTest.what_changed_overview`, printed before the first section. Mutation: overview unfiltered, 2 and 1 unit.
- [x] Tests cover each of the above, and each fails when its guard is removed. TST-0044: 22 new shell assertions (the harness has 245) and 4 unit tests (25 in all); fifteen mutations, each failing, listed in its adequacy.

## Steps
- [x] Add `platforms:` to the change template and schema.
- [x] Split the current survey builder by section and platform.
- [x] Define the what-changed file's shape and read it.
- [x] Add the stale-screenshot comparison.
- [x] Update TESTING.md, "The release test", rule 2.

## Notes
- Existing change notes have no `platforms:`. For those, the agent step in TASK-0193 decides the platform from the note's Impact lines and diff while writing the short lines; the generator treats an undeclared note as all platforms and says so.
- **Which section a screen belongs to.** REQ-0035 says "the first section whose `surfaces:` names it". Read literally, your-trainer's Equipment section would list nothing, because it claims its four checks by id and names no surface, and the pilot needs it to open with the Equipment panel's changes. So a section also tests the screens of the checks its `checks:` names. That keeps the rule static: it does not depend on which checks a release owes.
- **A screen whose section owes nothing this release** is listed on the overview, because no printed section would show it.
- **The cut-off date.** `PLATFORMS_REQUIRED_FROM` is 2026-09-28, the day after this lands. A consumer that syncs later and has written change notes without `platforms:` since then gets errors on its first `--check`. your-trainer has none today.
- your-trainer on a scratch copy (Android and iOS, REL-0017, after `migrate-release-test-names.py --apply`): the Equipment section now opens with the Equipment panel's 13 lines under its top-level screen, Workouts. Ten Android pictures are flagged as older than their change, all committed on 2026-09-14, which is ISS-0516. The overview lists three screens no section tests: App shell & UX, Files in and out, Localization. 23 change notes are named as declaring no `platforms:`, including iOS-only ones now listed on Android; TASK-0193 fixes that when it writes the short lines. `--check --quiet` adds one warning line, for those 23, and still exits 0. The Android page grows from 37,263 to 37,787 words; the iOS page shrinks from 78,607 to 78,567.
- Commits in project-os: 61421da (code and tests), 0a14cef (templates and instructions).

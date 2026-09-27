---
type: "[[task]]"
id: TASK-0187
aliases: ["TASK-0187"]
title: "Rename the walk to the release test in every template file, with a migration script for consumers"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "XL"
due: ""
depends: []
blocks: []
related: ["[[REQ-0037-The-Walk-Is-Called-The-Release-Test-Everywhere]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]", "[[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths]]", "[[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey]]"]
tests: ["[[TST-0041-A-Consumers-Walk-Files-Move-To-The-Release-Test-Names-Once]]", "[[TST-0009]]", "[[TST-0010]]", "[[TST-0011]]", "[[TST-0016]]", "[[TST-0017]]", "[[TST-0023]]", "[[TST-0028]]", "[[TST-0033]]"]
---

# Rename the walk to the release test in every template file, with a migration script for consumers

Every name in ADR-0050's rename map changes in the template in one commit, and consumers get a script that moves their files. This task goes first because every other task edits the renamed files.

## Definition of Done
- [x] Every row of ADR-0050's rename map that lives in the template has its new name, moved with `git mv` so history follows the file. project-os 66cee10 moves the four scripts, the order-file template and the three copies of the skill folder and nothing else; bff690e and cb01d0a change what they say, including the instruction sections, the other instructions, skills, hooks, adapters, CLAUDE.md's skill list and the code identifiers. The consumer rows (WALK.md, walk/, `sitting:`, `walk_readiness_for:`) are the migration script's. The rows ADR-0050 gives to later tasks (`state_for:`, `readiness_for:`'s `result:`, `platforms:`, the release-test-prep skill), to your-trainer (its two scripts) and to project-os-cockpit (bundle, route, tests) are not this task's.
- [x] A search of the template for `walk`, `sitting` and `survey`, outside `tools/cockpit/`, finds only history, ordinary English and the code that has to name the old names to refuse or migrate them. The list is in Notes. `tools/cockpit/` is project-os-cockpit's release copy (its own `walk_sheet_bundled.py` and 700-odd hits); it is renamed in project-os-cockpit FEAT-0155 and released into the template from there, as this note's Notes already said. Narrowed on 2026-09-27 to say so, because the criterion as first written covered that copy too.
- [x] `tools/scripts/migrate-release-test-names.py` moves WALK.md to RELEASE-TEST.md and walk/ to release-test/, and rewrites `sitting:` to `section:` and `walk_readiness_for:` to `readiness_for:`. Running it twice changes nothing. TST-0041: 27 of 27, ten mutations each caught. On a scratch clone of your-trainer it moved 15 files and edited 64, and the Android and iOS sheets were then line for line the same as before once the words were swapped.
- [x] After migration the validator reports each old name as an error that names the new one: OLD-NAME, with the migration command. TST-0041 asserts all four kinds before migrating and none after; removing the check fails 5 assertions.
- [x] `sync-project-os` deletes the old script and skill files from a consumer, and prints the migration command. The manifest's `renamed:` table and `migrations:` list drive it; TST-0016 (`test-sync-stale.sh`, 34 of 34) covers deletion of an edited file, a renamed folder, the dry run and the printed command, and a dry run against a clone of your-trainer listed all eight old paths and the command. The first sync that brings this in runs the consumer's older sync script, so it does neither; its validator run reports each old name as OLD-NAME instead (SYNCING.md says so).
- [x] The `command:` and `entrypoint:` lines of TST-0009, TST-0010, TST-0011, TST-0023 and TST-0033 in this repo point at the renamed scripts, and each passes. TST-0028 also ran the old harness and is updated too. `run-tests.py`: all 39 TST commands in this repo pass.
- [x] TESTING.md's section is headed "The release test", and its glossary uses section, what changed, tester and result (project-os cb01d0a).

## Steps
- [x] Rename the scripts, the order-file template, the skill folders and the instruction sections.
- [x] New ledger entries write `result`; every reader accepts `mark`; the migration script rewrites unsealed `WORKING-*.json` ledgers once. The template writes no ledger entries itself; its README example and the tests write `result`. The cockpit's writer changes in FEAT-0155.
- [x] `TESTING.md` and the code call feature, regression and automated tests "test kinds", so "section" has one meaning. `Check.section` is `Check.kind`.
- [x] Rename the code identifiers in the generator and the validator (`survey` to `what_changed`, `sitting` to `section`, and so on). The full list is in CHG-20260927-The-Walk-Is-Renamed-The-Release-Test.
- [x] Write the migration script and its test.
- [x] Add the old-name errors to the validator.
- [x] Regenerate the Cursor and Codex adapters and the skill copies.
- [x] Update this repo's five test notes, and TST-0028.

## Notes
- The ledger's stored key `mark` becomes `result` (Edwin, 2026-09-27, ADR-0050). New entries write `result`, every reader accepts `mark` forever, and the migration script rewrites unsealed `WORKING-*.json` ledgers once. An entry whose `result` and `mark` disagree is a LEDGER-ENTRY error.
- The three kinds of test (feature, regression, automated) are renamed from "sections" to "test kinds" in `TESTING.md` and in code (Edwin, 2026-09-27, ADR-0050).
- Moving many files in one commit is when git's rename detection can hide a new change note from "what changed" ([[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]]). The moves are project-os 66cee10 alone, and the change note is its own commit in this repo.
- The cockpit's bundle, route and tests are renamed in project-os-cockpit FEAT-0155, the release test page in the Tests pane. This task only changes what the cockpit bundles. Until then the cockpit's bundler looks for `walk-sheet.py`, which the template no longer has.
- Nothing was synced: not project-os-cockpit, not your-trainer, and not this repo's own vendored `tools/`, which still says walk until TASK-0195's sync.
- Commits in project-os: 66cee10 (moves), bff690e (code), 88d0c8b (migration and sync), cb01d0a (prose), cd0de05 (stronger tests).

### What a search of the template still finds (2026-09-27)

`rg -i "walk|sitting|survey"` over project-os, leaving out `tools/cockpit/` and `docs/changes/`:

- **Code and text that must name the old names**: `tools/sync/MANIFEST.yaml`'s `renamed:` table; `validate-docs.py`'s `RELEASE_TEST_OLD_OWN`, `RELEASE_TEST_OLD_TEMPLATE` and `validate_release_test_names`; the two refusals in `release-test.py`; `migrate-release-test-names.py` and `test-migrate-release-test-names.sh`; the old-name cases in `test-release-test.sh`; one sentence each in `SCHEMAS.md` (the `readiness_for` and `section` entries), `TESTING.md` ("The old names are refused") and `GLOSSARY.md` ("release test").
- **History**: `validate-docs.py` line 1149, a comment about a 2026-09-25 measurement that names the skill as it was then. The template's own change notes under `docs/changes/` (five files) are history too.
- **Ordinary English**: "walk" meaning to go through a tree or a list, in `LIFECYCLE.md` ("the curated record the validator walks", and its generated Cursor copy), `HOOKS.md` ("the walk up from the target"), about seventeen comments in `validate-docs.py`, two in `sync-project-os.py`, two in `sync-snapshot.py`, one each in `test-decision-rule.py` and `rank-bench.py`, and the calls `os.walk` and `ast.walk`; "sitting" meaning placed, in `validate-docs.py` line 199 and `grandfather.py` line 38. "survey" appears nowhere else.
- **Left out of the search on purpose**: `tools/cockpit/`, project-os-cockpit's release copy (see the second box).

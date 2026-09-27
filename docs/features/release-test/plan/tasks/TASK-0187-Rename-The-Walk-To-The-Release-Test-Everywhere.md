---
type: "[[task]]"
id: TASK-0187
aliases: ["TASK-0187"]
title: "Rename the walk to the release test in every template file, with a migration script for consumers"
status: backlog
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
tests: []
---

# Rename the walk to the release test in every template file, with a migration script for consumers

Every name in ADR-0050's rename map changes in the template in one commit, and consumers get a script that moves their files. This task goes first because every other task edits the renamed files.

## Definition of Done
- [ ] Every row of ADR-0050's rename map that lives in the template has its new name, moved with `git mv` so history follows the file.
- [ ] A search of the template for `walk`, `sitting` and `survey` finds only history (closed ADRs, change notes, archived notes) and ordinary English, and the list of remaining hits is recorded in Notes.
- [ ] `tools/scripts/migrate-release-test-names.py` moves a consumer's `docs/tests/acceptance/WALK.md` to `RELEASE-TEST.md` and `walk/` to `release-test/`, and rewrites `sitting:` to `section:` and `walk_readiness_for:` to `readiness_for:`. Running it twice changes nothing.
- [ ] After migration the validator reports each old name as an error that names the new one.
- [ ] `sync-project-os` deletes the old script and skill files from a consumer, and prints the migration command.
- [ ] The `command:` and `entrypoint:` lines of TST-0009, TST-0010, TST-0011, TST-0023 and TST-0033 in this repo point at the renamed scripts, and each passes.
- [ ] TESTING.md's section is headed "The release test", and its glossary uses section, what changed, tester and result.

## Steps
- [ ] Rename the scripts, the order-file template, the skill folders and the instruction sections.
- [ ] Rename the code identifiers in the generator and the validator (`survey` to `what_changed`, `sitting` to `section`, and so on).
- [ ] Write the migration script and its test.
- [ ] Add the old-name errors to the validator.
- [ ] Regenerate the Cursor and Codex adapters and the skill copies.
- [ ] Update this repo's five test notes.

## Notes
- The ledger's stored key `mark` is not touched until Edwin answers ADR-0050's open question. If he picks (b), a follow-up step writes `result` on new entries, reads `mark` forever, and migrates unsealed `WORKING-*.json` ledgers once.
- Moving many files in one commit is when git's rename detection can hide a new change note from "what changed" ([[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]]). Commit the rename separately from any new change note.
- The cockpit's bundle, route and tests are renamed in project-os-cockpit FEAT-0155, the release test page in the Tests pane. This task only changes what the cockpit bundles.

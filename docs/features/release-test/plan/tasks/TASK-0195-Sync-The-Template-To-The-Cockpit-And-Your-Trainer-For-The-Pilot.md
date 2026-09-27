---
type: "[[task]]"
id: TASK-0195
aliases: ["TASK-0195"]
title: "Sync the template to project-os-cockpit and your-trainer and confirm the Equipment section pilot on Android"
status: doing
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "M"
due: ""
depends: ["[[TASK-0190]]", "[[TASK-0191]]", "[[TASK-0192]]", "[[TASK-0193]]", "[[TASK-0194]]"]
blocks: []
related: ["[[TST-0040-A-Release-Test-Section-Reads-As-Short-Lines]]", "[[RISK-0005-Renaming-The-Walk-Breaks-Callers-That-Use-The-Old-Paths]]"]
tests: []
---

# Sync the template to project-os-cockpit and your-trainer and confirm the Equipment section pilot on Android

The template's changes reach the two repositories that use them, and the Equipment section is tested end to end on Android.

## Definition of Done
- [x] project-os-cockpit takes the template sync, and its release test page reads the new JSON (project-os-cockpit FEAT-0155, the release test page in the Tests pane). project-os-cockpit 666c5dc and 3beda27: synced from template 9044d67, and its release test page reads the generator's JSON through `/api/cockpit/release-test` (FEAT-0155, TASK-0639 to TASK-0643).
- [x] your-trainer takes the template sync and runs the migration script. Its validator reports no old name. your-trainer 2f30a82c: synced from 9044d67 and migrated in the same commit; `validate-docs.sh` reports no OLD-NAME.
- [ ] your-trainer's Equipment section on Android passes the length check (your-trainer FEAT-0129, the rewrite of the procedures and test notes with the Equipment section pilot).
- [ ] TST-0040 is walked on that section, and its result is recorded.
- [ ] The section budget is set from the pilot's measured page, or from Edwin's answer if he has given one.

## Steps
- [x] Sync the cockpit first, so its bundle and the sheet change together.
- [x] Sync your-trainer and run the migration.
- [ ] Generate the Equipment section and compare it with the approved example.

## Notes
- Complexity by blast radius: the pilot is Medium. The rest of the Android sections, then iOS, follow in your-trainer's own item.

## Progress, 2026-09-27

Both syncs are done (stage 5 of your-trainer FEAT-0129's plan). your-trainer was synced before the cockpit, the other way round from Step 1: the cockpit's page was rebuilt in the same session, so neither ran against the other's old names for longer than an hour. The sync script had to be run twice in each repository, because the first run used the old copy of the script that the same run replaced.

The other three boxes are the Equipment pilot, stage 7: your-trainer TASK-0975 rewrites the section, and TST-0040 is tested on it.

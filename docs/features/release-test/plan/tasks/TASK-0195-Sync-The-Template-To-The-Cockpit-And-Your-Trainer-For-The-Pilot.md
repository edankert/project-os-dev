---
type: "[[task]]"
id: TASK-0195
aliases: ["TASK-0195"]
title: "Sync the template to project-os-cockpit and your-trainer and confirm the Equipment section pilot on Android"
status: backlog
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
- [ ] project-os-cockpit takes the template sync, and its release test page reads the new JSON (project-os-cockpit: the release test page in the Tests pane, ID to follow).
- [ ] your-trainer takes the template sync and runs the migration script. Its validator reports no old name.
- [ ] your-trainer's Equipment section on Android passes the length check (your-trainer: rewrite of the procedures and test notes, Equipment section pilot, ID to follow).
- [ ] TST-0040 is walked on that section, and its result is recorded.
- [ ] The section budget is set from the pilot's measured page, or from Edwin's answer if he has given one.

## Steps
- [ ] Sync the cockpit first, so its bundle and the sheet change together.
- [ ] Sync your-trainer and run the migration.
- [ ] Generate the Equipment section and compare it with the approved example.

## Notes
- Complexity by blast radius: the pilot is Medium. The rest of the Android sections, then iOS, follow in your-trainer's own item.

---
type: "[[task]]"
id: TASK-0123
aliases: ["TASK-0123"]
title: "Sync the surface rules, the Impact field, the survey, the procedure format, validator and skill into your-trainer and project-os-cockpit, and confirm their plans carry the rest"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: M
due: ""
depends: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]", "[[TASK-0120-The-Procedure-Validator]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]", "[[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure]]"]
blocks: []
related: ["[[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit]]", "[[PHASE-0005-The-Walk-Reads-As-A-Script]]"]
tests: []
---

# Downstream: the consumers and the cockpit

## What

The template changes from FEAT-0030 and FEAT-0031 reach the two repos that use them. This task syncs and confirms. It does not do either repo's work: your-trainer's is its PHASE-024 (FEAT-0120, FEAT-0121) and the cockpit's is its PHASE-044 (FEAT-0150).

## Definition of Done

- [ ] `tools/scripts/sync-project-os.sh` has run in your-trainer. Its diverged `validate-docs.py` is hand-merged, not overwritten, as in TASK-0115. This is your-trainer TASK-0905.
- [ ] The same sync has run in project-os-cockpit, and `walk_sheet_bundled.py` is byte-identical to the template's `walk-sheet.py` again (its `tests/test_walk_bundle.py` passes).
- [ ] The other repos with an acceptance suite (project-os-deck, your-sudoku) are synced, and `bash tools/scripts/validate-fleet.sh` shows no new errors against the pre-sync table.
- [ ] REQ-0028's Amendments section records the survey change. ADR-0029 carries a one-line pointer to ADR-0045.
- [ ] This repo's vendored `tools/` is synced or its deferral is recorded.
- [ ] Adapters regenerated in every synced repo.

## Notes

- your-trainer's TASK-0902 (the `area:` rewrite) does not wait for this sync; its TASK-0906 (procedures) does.

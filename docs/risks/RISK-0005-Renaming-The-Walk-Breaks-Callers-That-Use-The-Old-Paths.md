---
type: "[[risk]]"
id: RISK-0005
aliases: ["RISK-0005"]
title: "Renaming the walk breaks any hook, CI job, bundle or test that still calls the old script names and paths"
status: open
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]", "risk scan 2026-09-27: a directory layout and artifact path change"]
likelihood: high
impact: medium
mitigation: ["Rename in one template release, with no mixed state", "A migration script moves each consumer's files, and running it twice changes nothing", "The validator names the new name for every old one it finds", "The template sync deletes old files and prints the migration command", "Sync project-os-cockpit before your-trainer, so the bundle and the sheet change together"]
related: [FEAT-0040, TASK-0187, TASK-0195, ADR-0050, ISS-0067]
---

# Renaming the walk breaks callers that use the old paths

## Description

ADR-0050 renames `walk-sheet.py`, `walk-tags.py`, their test harnesses, `WALK.md`, the `walk/` folder, the `walk-procedure` skill and several frontmatter fields, with no aliases. Anything that still calls an old name fails:

- this repo's five test notes whose `command:` runs `test-walk-sheet.sh` or `test-walk-preparation.py` (TST-0009, TST-0010, TST-0011, TST-0023, TST-0033);
- the cockpit's bundled copy of the generator, its `/api/cockpit/walk` route and its tests;
- your-trainer's own scripts, CI steps and hooks that call the generator;
- any agent session that follows an older skill text.

Moving many files in one commit can also hide a new change note from "what changed", because git may pair it with a renamed file ([[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]]).

## Mitigation

- Rename in one template release, so no consumer sees half of it.
- The migration script moves a consumer's files and fields, and is safe to run twice.
- The validator reports every old name with the new one.
- The template sync deletes the old files and prints the migration command.
- Sync project-os-cockpit first, then your-trainer.
- Commit the rename apart from any new change note.

## Triggers

- A test note's command fails with "No such file" after the sync.
- The cockpit's Tests pane shows no release test after a sync.
- A consumer's CI fails on a missing `walk-sheet.py`.

---
type: "[[risk]]"
id: RISK-0005
aliases: ["RISK-0005"]
title: "Renaming the walk breaks any hook, CI job, bundle or test that still calls the old script names and paths"
status: closed
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

- this repo's six test notes whose `command:` ran `test-walk-sheet.sh` or `test-walk-preparation.py` (TST-0009, TST-0010, TST-0011, TST-0023, TST-0033, and TST-0028, which ADR-0050's list missed). All six run the new names since TASK-0187;
- the cockpit's bundled copy of the generator, its `/api/cockpit/walk` route and its tests;
- your-trainer's own scripts, CI steps and hooks that call the generator;
- any agent session that follows an older skill text.

Moving many files in one commit can also hide a new change note from "what changed", because git may pair it with a renamed file ([[ISS-0067-Git-Rename-Detection-Can-Hide-A-New-Change-Note-From-The-Survey|ISS-0067]]).

## Mitigation

In place in the template since TASK-0187 (2026-09-27):

- The rename is one template release: project-os commits 66cee10 to cb01d0a.
- `migrate-release-test-names.py` moves a consumer's files and fields, and a second run changes nothing.
- The validator reports every old name it finds as OLD-NAME, with the new name and the migration command.
- The template sync deletes renamed files and prints the migration command. A sync runs the consumer's own copy of the sync script, so the first sync that brings this in does neither. Its validator run reports each old name as OLD-NAME instead, so nothing is missed.
- The rename commits in project-os carry no change note; the change note is in this repo, in its own commit.

Still to do (TASK-0195):

- Sync project-os-cockpit first, then your-trainer. The cockpit's bundle reads `walk-sheet.py` until FEAT-0155 re-bundles `release-test.py` under its new code names.

## Triggers

- A test note's command fails with "No such file" after the sync.
- The cockpit's Tests pane shows no release test after a sync.
- A consumer's CI fails on a missing `walk-sheet.py`.

## Closed 2026-09-27

Every consumer took the rename and runs the new names:

- project-os-cockpit re-bundles `release-test.py` and serves `/api/cockpit/release-test` (FEAT-0155, done).
- your-trainer's procedures, scripts and corpus test use the new paths, and its release test passes on both platforms.
- This repository synced on 2026-09-27 (b5a29ab).
- The template's shipped `tools/cockpit` was re-released without `walk_sheet_bundled.py` (project-os aee9c6a, 2c037dd).

None of the triggers fired after the syncs.

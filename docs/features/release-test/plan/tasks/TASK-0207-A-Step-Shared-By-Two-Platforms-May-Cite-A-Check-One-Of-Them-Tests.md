---
type: "[[task]]"
id: TASK-0207
aliases: ["TASK-0207"]
title: "A procedure step may cite a check that one platform tests by command, while another platform still needs it; and hand steps count a note's `## Procedure` items"
status: done
phase: ""
owner: user:edwin
created: 2026-10-21
updated: 2026-10-21
source: ["[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]", "your-trainer TASK-1129: merging TASK-1131 gave 91 procedure errors on the Android sheet for steps iOS still owes"]
parent: "[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]"
effort: "S"
due: ""
depends: ["[[TASK-0205-A-Command-Covers-One-Platform-Hand-Steps-Stay-Owed-And-The-Sheet-Prints-The-Budget]]"]
blocks: []
related: []
tests: []
---

# A shared step may cite a check that only one platform tests

## Problem

TASK-0205 made `--check` refuse a procedure step that cites a part a command tests on the platform being checked. A procedure is shared by every platform. In your-trainer, 22 checks gained an Android command and no iOS one, so iOS still owes their steps. Every such step then failed the Android check: 91 errors in seven procedures.

The fix the message offers, `step_platforms: [ios]`, does not fit a step that also cites a check Android still owes, because it limits the whole step. Removing the tag breaks the iOS sheet. The sheet already prints only the tags a platform owes, and leaves out a step with none, so the citation does no harm on the platform that has a command.

Separately, the validator counts the steps for `hand_steps:` under `## Steps` only. `release-test.py` also reads `## Procedure`, the older heading, which 35 of your-trainer's checks still use, so the two disagreed about how many steps a note has.

## Definition of Done

- [x] `--check` refuses a citation of a command-tested part only when no platform the step runs on still needs that part. A step runs on its `step_platforms`, or on every platform the repo keeps a ledger for. Evidence: project-os 742fbe9, `_audit_tag` and `Procedure.known_platforms`. Read-only against your-trainer, the Android and iOS checks went from 91 citation errors to one, a tag on TST-0362, which has a `command:` for both platforms and so is rightly refused.
- [x] The validator's hand-step count reads `## Procedure` when the note has no `## Steps`, as `release-test.py` does. Evidence: `_numbered_step_count` in project-os 742fbe9.
- [x] Tests cover both, and each fails with its fix removed; the template's existing release-test tests still pass. Evidence: `test-release-ride.py` 68 assertions pass; with the platform rule removed, the shared-step assertion fails, and with `## Procedure` removed, the heading assertion fails. `test-release-test.sh` 273 assertions and `test-release-test-preparation.py` pass.
- [x] TESTING.md says the rule in one sentence where it describes the citation check. Evidence: "Release gating", rule 2.

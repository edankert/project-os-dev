---
type: "[[issue]]"
id: ISS-0105
aliases: ["ISS-0105"]
title: "The test runner runs a retired test's command, so a push fails on a test whose subject was deleted"
status: fixed
phase: ""
owner: user:edwin
created: 2026-10-06
updated: 2026-10-06
source: ["project-os-deck, 2026-10-06: the pre-push hook refused a push of 144 commits because retired TST-0061 still named a deleted file; Edwin: 'fix the runner upstream in project-os'"]
reported_by: user:edwin
question: ""
severity: medium
component: "testing"
parent: ""
related: []
tests: []
---

# The test runner runs a retired test's command, so a push fails on a test whose subject was deleted

## Problem

A push can be refused because of a test nobody runs any more. `tools/scripts/run-tests.py` runs the `command:` of every `TST-*` note and never reads `status:`. `STATUSES.md` says `retired` means "the subject is gone, or the test was folded into another". When the subject is gone, its command usually names a file that was deleted with it. The runner then fails, the pre-push hook (HC-009) refuses the push, and in CI the same note fails `--ci` in a repo that declares no `ci.suite_command`.

It happened in project-os-deck on 2026-10-06. TST-0061 was retired on 2026-10-01 when [[project-os-deck#TASK-0105]] removed the native Glass prototype. Its `command:` still named `prototypes/native-glass/tools/test-verify-parity.mjs`. The hook reported `passing=45 failing=1` and refused the push. Deck worked around it by removing the command from the note (project-os-deck `10642bf`).

## Expected

A retired test's command is not run. The runner's report does not list it, and it counts towards neither passing nor failing.

## Actual

The command runs, fails with "Could not find ...", and the pre-push hook refuses the push.

## Next Actions
- [x] project-os: `run-tests.py` skips a note whose `status:` is `retired`, including under `--filter`; `test-verdict-model.sh` gets a case that fails when the skip is removed; HC-009 in `HOOKS.md` says so.

## Fixed, 2026-10-06

- **project-os `e9b7744`**: `run-tests.py` skips a note at `status: retired`, even under `--filter`, and leaves it out of the report. Three new checks in `test-verdict-model.sh` each fail when the skip is removed. HC-009 in `HOOKS.md` has a fourth line saying so.
- Downstream repos get it at their next template sync. Nothing was synced as part of this fix.
- Change note: [[CHG-20261006-The-Test-Runner-Skips-A-Retired-Test]].

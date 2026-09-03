---
type: "[[test]]"
id: TST-0008
aliases: ["TST-0008"]
title: "The runner writes nothing, and the gate accepts an executable test at active"
status: draft
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]", "[[TASK-0107]]"]
scope: feature
level: acceptance
entrypoint: "../project-os/tools/scripts/test-verdict-model.sh"
command: "bash ../project-os/tools/scripts/test-verdict-model.sh"
requirements: []
features: ["[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"]
issues: ["[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]"]
tasks: ["[[TASK-0106]]", "[[TASK-0107]]", "[[TASK-0109]]"]
artifacts: []
adequacy: ""
related: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
---

# The runner writes nothing, and the gate accepts an executable test at active

## Purpose

[[ADR-0025-An-Executable-Test-Records-No-Verdict|ADR-0025]] makes two claims a harness can settle: `run-tests.py` leaves every note byte-identical, and the verification gate treats a `command:` test at `active` as settled while warning on one that still carries a verdict. This note executes both against fixture repos. Draft until [[TASK-0107]] writes the harness.

## Procedure

`tools/scripts/test-verdict-model.sh` in `~/Dev/repos/project-os`, fixture repos under a tempdir:

1. A fixture with a task at `done` linked to a `command:` test at `active`: the validator passes.
2. The same test at `passing` with `last_run:`: the validator reports `COMMAND-VERDICT` as a warning, not an error, before the cutover.
3. A manual test (no `command:`) at `ready` linked to a done task: the gate still fails, so the change did not loosen manual tests.
4. `run-tests.py` over a fixture with one passing and one failing command: the notes are byte-identical before and after, the exit code is 1, and `--write` is not an accepted flag.

## Expected results

- Exit 0 once TASK-0106 and TASK-0107 have landed.

## Adequacy (who verifies this test?)

Invert by restoring the `--write` branch in a copy of the runner and by making the gate demand `passing` of a `command:` test again; record both here when the harness first runs green.

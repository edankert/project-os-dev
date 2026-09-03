---
type: "[[test]]"
id: TST-0008
aliases: ["TST-0008"]
title: "The runner writes nothing, and the gate accepts an executable test at active"
status: active
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
adequacy: "Inverted three ways on 2026-09-03 against the template at a8694f0, each on a copy of the file restored afterwards: the gate's skip for a command: test removed, 2 failures (the done task fails VERIFY on the active test); the COMMAND-VERDICT cutover moved to the past, 2 failures (an error instead of a warning, exit 1); the runner made to append a line to each note, 1 failure (byte-identical). Pristine tree 11 of 11."
related: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
---

# The runner writes nothing, and the gate accepts an executable test at active

## Purpose

[[ADR-0025-An-Executable-Test-Records-No-Verdict|ADR-0025]] makes two claims a harness can settle: `run-tests.py` leaves every note byte-identical, and the verification gate treats a `command:` test at `active` as settled while warning on one that still carries a verdict. This note executes both against fixture repos.

## Procedure

`tools/scripts/test-verdict-model.sh` in `~/Dev/repos/project-os`, fixture repos under a tempdir:

1. A fixture with a task at `done` linked to a `command:` test at `active`: the validator passes.
2. The same test at `passing` with `last_run:`: the validator reports `COMMAND-VERDICT` as a warning, not an error, before the cutover.
3. A manual test (no `command:`) at `ready` linked to a done task: the gate still fails, so the change did not loosen manual tests.
4. `run-tests.py` over a fixture with one passing and one failing command: the notes are byte-identical before and after, the exit code is 1, and `--write` is not an accepted flag.

## Expected results

- Exit 0: every assertion holds. First real run 2026-09-03 at template commit a8694f0, 11 of 11; CI runs it on every push through run-tests.py.

## Adequacy (who verifies this test?)

Inverted three ways on 2026-09-03 against the template at `a8694f0`, each mutation confirmed to have landed and reverted by copying the saved file back: the gate's skip for a `command:` test removed (2 failures: the done task fails VERIFY on the `active` test, and a VERIFY error names it); the COMMAND-VERDICT cutover moved to the past (2 failures: an error instead of a warning, and the stamped fixture exits 1); the runner made to append a line to every note it ran (1 failure: byte-identical). The pristine tree passes 11 of 11.

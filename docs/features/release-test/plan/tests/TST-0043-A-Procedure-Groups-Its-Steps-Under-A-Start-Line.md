---
type: "[[test]]"
id: TST-0043
aliases: ["TST-0043"]
title: "A procedure groups its steps under ### headings with a Start: line, state_for still works with a warning, and readiness_for accepts only a stored result"
status: active
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0189-A-Procedure-Groups-Its-Checks-Under-A-Start-State]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-release-test.sh"
command: "bash ../project-os/tools/scripts/test-release-test.sh"
covers: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
tasks: ["[[TASK-0189]]"]
requirements: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]"]
issues: []
artifacts: []
evidence: []
adequacy: "2026-09-27, the block headed 'Groups' in test-release-test.sh (14 assertions) and the rewritten screen-name assertions (the harness has 218). Eleven mutations in a scratch copy of the template, each failing the harness: group headings not read, 4 failures; Start: lines not read, 4; Start: not carried into the required state, 2; Start: applied only to a group's first step even when that step runs on another platform, 1; the state_for warning off, 2; a Start: line and state_for on one step not refused, 1; a procedure's result: not validated, 1; a check's result: not validated, 1; the suggested result not printed, 2; action_for needing a bold screen name again, 2; the no-screen remark put back, 1. Pristine 218 of 218."
related: ["[[TST-0010]]", "[[TST-0023]]"]
---

# A procedure groups its steps under a Start line

## Purpose

REQ-0033 has a procedure group its steps under headings, each with a start state written once, and lets a step be one short action line with no screen name. This test shows the generator reads the groups and their `Start:` lines, still reads `state_for:` with a warning, and accepts a readiness `result:` only when it is one of the seven stored result values.

## Procedure

`bash ../project-os/tools/scripts/test-release-test.sh`. The fixture rewrites the procedure fixture into two groups, "The panel" and "Riding", with a `Start:` line each; the first step of "Riding" runs on a second platform only.

## Expected results

- The module reads both groups with their titles, `Start:` lines and step positions, and `--check` passes with no warning.
- The page prints each group's `Start:` line as the state its first step needs, including a group whose first step runs on the other platform.
- A procedure with `state_for:` still prints it and is warned, one counted line under `--quiet`; a `Start:` line and `state_for` on one step are refused.
- A step with no screen name passes and draws no remark; `action_for` replaces its whole action line.
- `result: question` prints as the suggested result on a procedure step, `result: blocked` on a check's row, and `result: maybe` or `skipped` is refused.

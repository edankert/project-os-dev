---
type: "[[test]]"
id: TST-0046
aliases: ["TST-0046"]
title: "The length check reports an action line, an expected line and a section over their limits, which a project can change and make errors"
status: active
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0192-The-Validator-Reports-Over-Long-Lines-And-Sections]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-release-test.sh"
command: "bash ../project-os/tools/scripts/test-release-test.sh && python3 -B ../project-os/tools/scripts/test-release-test-preparation.py"
covers: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
tasks: ["[[TASK-0192]]"]
requirements: ["[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]"]
issues: []
artifacts: []
evidence: []
adequacy: "2026-09-27, the block headed 'REQ-0036 (TASK-0192)' in test-release-test.sh (14 assertions; the harness has 268) and three unit tests (30 in all). Ten mutations, each failing: action limit ignored, 3; expected limit ignored, 2; budget ignored, 1; override ignored, 3; error switch ignored, 2; unknown key accepted, 1; zero accepted, 1; tags counted, 1 unit; pictures counted, 1 unit; budget per test note, 1 unit. Pristine 268 of 268 and 30 of 30."
related: ["[[TST-0045]]"]
---

# The length check reports what is too long

## Purpose

REQ-0036 has `--check` report every line and section a tester would find too long. This test shows the limits, the budget, the override in the section order file and the switch that makes the reports errors.

## Procedure

`bash ../project-os/tools/scripts/test-release-test.sh`, then `python3 -B ../project-os/tools/scripts/test-release-test-preparation.py`. The shell fixture lengthens one action line to 22 words and one Expect line to 28.

## Expected results

- The long action and the long expected line are each a warning naming the section, the check number and the tag, and `--check` still exits 0. Under `--quiet` they are one counted line.
- Raising the limits in `length_limits:` silences them; a small budget reports the section with the sum it was held to.
- `length_limits: {error: true}` makes them errors and fails `--check`. An unknown key or a limit of 0 fails it too.
- Words are counted without tags and pictures, and the budget counts printed checks, not test notes.

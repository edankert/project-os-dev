---
type: "[[task]]"
id: TASK-0107
aliases: ["TASK-0107"]
title: "The validator treats a command test as settled by CI and warns on a verdict field"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[ADR-0025-An-Executable-Test-Records-No-Verdict]]"]
parent: "[[FEAT-0028-Executable-Tests-Carry-No-Verdict]]"
effort: M
depends: []
related: ["[[ADR-0011-No-Permanent-Warning-Tier]]"]
tests: ["[[TST-0008]]"]
---

# The validator treats a command test as settled by CI and warns on a verdict field

## Definition of Done
- [x] In the verification gate, a linked test that carries a `command:` is settled by CI: no `passing` is demanded of it.
- [x] A new check, `COMMAND-VERDICT`, reports a `command:` test carrying `ready`, `passing`, `failing`, `last_run:` or `exit_code:`, as a warning with a dated promotion under ADR-0011 (90 days) and the fleet count at landing recorded in the `PROMOTIONS` comment.
- [x] The bundled cockpit validator is out of scope (a separate fork; ISS-0047's follow-up).

## Steps
- [x] Measure the fleet before landing: 33 notes carry a verdict on a `command:` test, 5 sit at `ready`.

## Notes

Landed as template commit `a8694f0` on 2026-09-03 with the harness `tools/scripts/test-verdict-model.sh` (11 assertions, three inversions recorded on [[TST-0008]]). Fleet count at landing: 33 stamped command: tests and 5 at ready; cutover 2026-12-02.

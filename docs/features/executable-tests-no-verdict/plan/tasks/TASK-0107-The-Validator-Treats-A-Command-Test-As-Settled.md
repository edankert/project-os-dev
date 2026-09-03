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
- [x] A new check, `COMMAND-VERDICT`, reports a `command:` test carrying `ready`, `passing`, `failing`, `last_run:` or `exit_code:`, as a warning with a dated promotion under ADR-0011 (90 days) and the fleet count at landing recorded in the `PROMOTIONS` comment (the review's count, 98).
- [x] The bundled cockpit validator is out of scope (a separate fork; ISS-0047's follow-up).

## Steps
- [x] Measure the fleet before landing: my count was 33 and 5; the review's, by the check itself, is 98 notes drawing it, 29 by status, 2 at `ready`.

## Notes

Landed as template commits `a8694f0`, `b5e8f9f` (the skip precedes the acceptance branch) and `293e5a2` (after review) on 2026-09-03, with the harness `tools/scripts/test-verdict-model.sh` (18 assertions, six inversions recorded on [[TST-0008]]). The count in the DoD, 33 stamped and 5 at ready, was wrong: the review measured 98 notes drawing the check on the fleet's trees (your-trainer 69, most carrying only an `exit_code:`), 29 by status and 2 at ready, and the PROMOTIONS comment carries those. Cutover 2026-12-02.

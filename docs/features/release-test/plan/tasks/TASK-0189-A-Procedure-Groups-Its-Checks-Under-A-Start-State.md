---
type: "[[task]]"
id: TASK-0189
aliases: ["TASK-0189"]
title: "A procedure groups its checks under headings with a start state, and each step is one action line with tags"
status: backlog
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0187]]"]
blocks: []
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
tests: []
---

# A procedure groups its checks under headings with a start state, and each step is one action line with tags

The procedure file changes shape so the generator can print groups. A `### ` heading under `## Steps` starts a group, a `Start:` line under it gives the start state, and each numbered item is one action line followed by tag-only lines.

## Definition of Done
- [ ] The generator reads groups, their headings and their `Start:` lines from a procedure.
- [ ] `state_for:` is read as before for procedures that have not moved to groups, and the validator warns that it is replaced by `Start:`.
- [ ] A step's action no longer needs a screen name. The rule that the first line names a surface is removed from the validator and from TESTING.md.
- [ ] `readiness_for:` accepts an optional `result:` with one of the seven stored result values, and the validator refuses any other value.
- [ ] `docs/__templates__/procedure.md` shows a procedure with two groups, a `Start:` line, short actions and tag-only lines.
- [ ] Tests cover groups, `Start:` lines, the `result:` value and the old `state_for:` warning, and each fails when its guard is removed.

## Steps
- [ ] Extend the procedure parser.
- [ ] Update the validator's rules for steps.
- [ ] Rewrite the procedure template with the Equipment Hub example's shape.
- [ ] Update TESTING.md, "The release test", rule 9.

## Notes
- `requires:`, `setup_for:`, `step_platforms:`, `action_for:`, `capture_for:`, `use_capture:` and `timer_for:` stay as they are (ADR-0050, amendments).

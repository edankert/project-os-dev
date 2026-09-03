---
type: "[[task]]"
id: TASK-0103
aliases: ["TASK-0103"]
title: "HC-008 serves focus state and recommends the planner selectively"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 3.1"]
parent: "[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"
effort: M
depends: ["[[TASK-0102]]"]
related: ["[[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]]", "[[FEAT-0021-Serve-Orientation-Answer-Lookup]]", "[[ADR-0003-Delegate-Orchestration]]"]
tests: ["[[TST-0007]]"]
---

# HC-008 serves focus state and recommends the planner selectively

## Definition of Done
- [ ] `hooks/model-routing-hint.sh:57-75` emits the focus item, its status and its phase, rather than an instruction.
- [ ] The planner is recommended for a multi-item scaffold or an ambiguous ask, and the hint says the main loop does preflight for a single issue or task.
- [ ] The documentation requirement is restated in one clause so nothing reads as a licence to skip it: every change still gets its note before the code.
- [ ] The review sentence is emitted only in review states.
- [ ] One line says the lead keeps reading the code while the planner runs; HC-001 blocks edits, not reading.
- [ ] `HOOKS.md` HC-008 and the `ADAPTER.md` routing table are updated in the same commit.
- [ ] The hint stays within the size bound [[TST-0007]] asserts.

## Steps
- [ ] Settle the division of state with [[TASK-0080]] before writing the output (see the plan).
- [ ] Land [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]] first; it renames this hook and rewrites the same contract line.

## Notes

**Scope discipline.** [[ADR-0003-Delegate-Orchestration]] keeps coordination in the tool rather than in the snapshot, and this task must not walk that back: the hint informs, the harness routes. What is being removed is an instruction to delegate work that is a handful of tool calls, which is what the guides say not to do.

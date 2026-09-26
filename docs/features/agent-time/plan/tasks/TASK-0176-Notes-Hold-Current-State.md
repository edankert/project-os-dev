---
type: "[[task]]"
id: TASK-0176
aliases: ["TASK-0176"]
title: "Notes hold their current state, and history goes to change notes"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0098-Notes-Grow-Into-Diaries]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0098-Notes-Grow-Into-Diaries]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0034-Notes-Hold-Current-State-And-Link-Rules]]"]
---

# Notes hold their current state, and history goes to change notes

## Definition of Done
- [x] WRITING.md states it, with the reason: rule 11, "A note says what is true now".
- [x] The task and feature templates say where history goes: the task's Notes placeholder and a comment above the feature's Goal point at rule 11.

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0034).

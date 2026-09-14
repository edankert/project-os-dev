---
type: "[[task]]"
id: TASK-0121
aliases: ["TASK-0121"]
title: "walk-sheet.py prints a sitting's procedure with its setup once and only the steps that cite an owed part, and prints per-check rows for a sitting with no procedure"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 5"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: M
due: ""
depends: ["[[TASK-0119-The-Procedure-Format]]"]
blocks: ["[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]", "[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
tests: ["[[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]]"]
---

# The sheet prints the owed parts of a procedure

## What

For a sitting with a procedure, the walk sheet prints the setup once and then only the steps that cite at least one owed part. Inside a printed step, each expectation line keeps its tags, so the walker sees which check it satisfies. A step with a mix of owed and already-passed tags prints once, with the passed tags marked as passed. For a sitting with no procedure, the sheet prints exactly what it prints today.

## Definition of Done

- [ ] `render()` and `build_walk()` read the procedure for each sitting in WALK.md order.
- [ ] Steps citing no owed part are left out, and the sheet header says how many steps were left out, as a count.
- [ ] The payload `walk-sheet.py` exposes to the cockpit carries the procedure structure (setup, steps, lines, tags, owed flag per tag), so project-os-cockpit TASK-0623 renders from data rather than re-parsing markdown.
- [ ] A sitting with a procedure that fails the validator prints the validator's message at the top of the sitting and then per-check rows, so a stale procedure never hides an owed check.
- [ ] Fixture assertions: setup printed once; a step citing only passed parts is absent; a mixed step is present with its passed tags marked; a sitting without a procedure is unchanged; a failing procedure falls back.

## Notes

- Shares `render()` with TASK-0118. Land that first or rebase deliberately.
- No duration appears anywhere (TESTING.md rule 8 still holds for the generator's own text).

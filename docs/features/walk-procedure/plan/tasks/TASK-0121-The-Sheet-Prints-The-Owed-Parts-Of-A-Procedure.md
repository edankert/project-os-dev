---
type: "[[task]]"
id: TASK-0121
aliases: ["TASK-0121"]
title: "walk-sheet.py prints a sitting's procedure with its setup once and only the steps that cite an owed part, and prints per-check rows for a sitting with no procedure"
status: done
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

- [x] `render()` and `build_walk()` read the procedure for each sitting in WALK.md order.
- [x] Steps citing no owed part are left out, and the sheet header says how many steps were left out, as a count.
- [x] The payload `walk-sheet.py` exposes to the cockpit carries the procedure structure (setup, steps, lines, tags, owed flag per tag), so project-os-cockpit TASK-0623 renders from data rather than re-parsing markdown.
- [x] A sitting with a procedure that fails the validator prints the validator's message at the top of the sitting and then per-check rows, so a stale procedure never hides an owed check.
- [x] Fixture assertions: setup printed once; a step citing only passed parts is absent; a mixed step is present with its passed tags marked; a sitting without a procedure is unchanged; a failing procedure falls back.

## Notes

- Shares `render()` with TASK-0118. Land that first or rebase deliberately.
- No duration appears anywhere (TESTING.md rule 8 still holds for the generator's own text).

## What a sitting with a procedure looks like

The setup once, then one `#### Step N — <screen>` per printed step with the step's own lines verbatim, then one tick box per owed check. The tick box is per **check**, not per step: rule 6 still says a verdict is one ledger event per check, and the sheet is not the place to change that. The cockpit's per-step ticks are its TASK-0624, which writes the same one event once every citing step is ticked.

A tag on a printed line whose part is not owed prints `_(already walked: TST-0404 step 2)_` after the line, so a step kept for one check does not read as a second ask for a check that has passed.

The header says how many steps were left out and why, as a count. No duration anywhere; the harness still greps for one.

## The fall-back, and why the payload matters

A procedure the validator refuses prints its message at the top of the sitting, then per-check rows. The rows are always computed, so nothing owed is ever hidden behind a stale script.

`Placed.steps` and `Placed.owed_checks` stay **empty** when a procedure has problems. That is invisible on the sheet, which is why it survived the first mutation pass: the renderer decides from `problems`, so an unfiltered `steps` would have changed nothing on the page. It is not invisible to the cockpit, which renders `steps` from the payload — so the harness now imports the module and asserts `problems=1 steps=0 owed_checks=0 walked=False` directly.

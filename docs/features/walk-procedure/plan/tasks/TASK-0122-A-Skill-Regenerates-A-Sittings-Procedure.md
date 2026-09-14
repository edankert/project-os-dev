---
type: "[[task]]"
id: TASK-0122
aliases: ["TASK-0122"]
title: "A skill regenerates a sitting's procedure with an LLM when its owed checks change, reruns the validator, and keeps the result only when it passes; release-prep points at it"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 6", "Edwin, 2026-09-14: 'an LLM can always be integrated in these solutions'"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: M
due: ""
depends: ["[[TASK-0120-The-Procedure-Validator]]"]
blocks: ["[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]"]
tests: []
---

# A skill regenerates a sitting's procedure

## What

When the validator reports that a sitting's procedure no longer covers its owed parts, an agent follows one skill to rewrite it. The skill gives the LLM the sitting's state and bench from WALK.md, each check's Setup, Steps and Expect, and the surface notes. It asks for setup once, a surface on every step, one shared step where checks share an action, and tags on every expectation. It reruns the validator and keeps the procedure only when it passes.

## Definition of Done

- [ ] `tools/skills/walk-procedure/SKILL.md` exists (name to match the template's skill list), with inputs, outputs and a checklist, linking TESTING.md "The walk" and restating none of it.
- [ ] The checklist says what the agent must not do: invent a step no check has, drop an owed part, or paraphrase an Expect so it asserts something different. It says what to do when two checks' setups conflict: split the sitting in WALK.md, which is the owner's file, and ask.
- [ ] `release-prep` and `release-verification` skills gain one step: run the validator for each sitting, and regenerate any procedure it fails before handing over the sheet.
- [ ] The adapters are regenerated (`tools/skills/adapter-sync/SKILL.md`) so the new skill reaches `.claude/` and the other tools.

## Notes

- The LLM runs in the agent session. The skill adds no model call to any script.

---
type: "[[task]]"
id: TASK-0117
aliases: ["TASK-0117"]
title: "change.md's Impact section lists SUR-* ids with one rider-facing sentence each, and the change-note and close-out skills ask an LLM to draft it from the diff"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 2"]
parent: "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"
effort: M
due: ""
depends: ["[[TASK-0116-TAXONOMY-States-What-A-Surface-Is]]"]
blocks: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
related: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tests: []
---

# A change note names the screens it changed

## What

Every change note says which screens it changed and, for each, one sentence a rider would understand. Example: "SUR-00xx Equipment panel: a third and fourth slot appear, for a power meter and a cadence sensor." The survey reads nothing else.

The template's `change.md` Impact section today says "affected areas/flows/workflows" in free text. Its optional "Acceptance checks reopened" section names checks, not screens.

## Definition of Done

- [ ] `docs/__templates__/change.md`'s Impact section is a list of `[[SUR-####]]` links, each followed by one sentence written for a rider. A change with no screen writes "No screen changed" and why.
- [ ] `SCHEMAS.md`'s `change.md` entry describes the shape a parser reads, including the "No screen changed" line.
- [ ] `tools/skills/change-note/SKILL.md` and `tools/skills/close-out/SKILL.md` each gain one step: ask an LLM to draft the Impact list from the diff and the repo's surface notes, then check that every id resolves. The rule is stated in TESTING.md (TASK-0118) and the skills link there.
- [ ] Decide what happens to the optional "Acceptance checks reopened" section: kept as prose for the ledger's invalidation reason, or removed. Record the answer in the task.
- [ ] Decide whether the validator refuses an Impact line naming a `SUR-*` that does not exist. If yes, it errors from day one only when no consumer has a violation (ADR-0011); otherwise it lands with a dated promotion.

## Steps

- [ ] Draft the template text and the two skill steps.
- [ ] Measure on your-trainer: how many of the 12 change notes since the v2.1.8 tag already have an Impact section, and in what shape. Record the count.

## Notes

- This is a new close-out obligation. ADR-0029 rule 8 and project-os-cockpit ADR-0036 both argued against one. ADR-0045 records why this one is different: the survey's one input is recorded nowhere else. If Edwin declines ADR-0045 decision 2, this task is cancelled.

---
type: "[[task]]"
id: TASK-0094
aliases: ["TASK-0094"]
title: "test-authoring says what a TST note is and is not"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 6.2"]
parent: "[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"
effort: S
depends: []
related: ["[[ADR-0010-Test-Status-Stamped-By-Execution]]"]
tests: []
---

# test-authoring says what a TST note is and is not

## Definition of Done
- [ ] `test-authoring/SKILL.md` carries one paragraph: a `TST-*` note is the record of verification; the scratch checks used to reach it are not kept; committed code tests follow the repo's existing convention and are sized to the behaviours stated in the task, roughly one focused test per behaviour.

## Steps
- [ ] Place it before the checklist, where the skill decides what is being authored.

## Notes

The gap is narrow and real. `feature-scaffold` step 9 mandates one acceptance check per feature, and `test-authoring` covers the note. Neither says anything about the code tests or the throwaway scripts written on the way, and the verification gate rewards linking more `TST-*` notes.

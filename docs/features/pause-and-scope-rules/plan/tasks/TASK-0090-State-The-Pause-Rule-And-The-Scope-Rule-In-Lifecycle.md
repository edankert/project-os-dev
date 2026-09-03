---
type: "[[task]]"
id: TASK-0090
aliases: ["TASK-0090"]
title: "State the pause rule and the scope rule in LIFECYCLE.md"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 2.1, 6.1"]
parent: "[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"
effort: S
blocks: ["[[TASK-0091]]"]
related: []
tests: ["[[TST-0005]]"]
---

# State the pause rule and the scope rule in LIFECYCLE.md

## Definition of Done
- [x] LIFECYCLE.md "Execution" carries the pause rule: pause for the user only for a destructive or irreversible action, a real scope change, or input only the user can provide.
- [x] It carries the second half: first do everything that does not depend on the answer, then put the question at the end of a turn that also delivers that progress.
- [x] It carries the scope rule: a bug, a cleanup or a missing abstraction the task did not ask for is an `ISS-*` at triage or a follow-up in the summary, not a change in this diff — unless the requested behaviour cannot work without it.
- [x] It carries the ambiguity half of the same rule: implement the reading the wording most directly supports and state the assumption in the task note.
- [x] The section has a stable anchor the other files can link to, and the anchor text is recorded in [[TST-0005]].

## Steps
- [x] Draft the three rules, each as a normative sentence plus one line of reason.
- [x] Place them under "Execution", which is where an agent is when it hits either situation.
- [x] Do not add an anecdote. [[REQ-0026]] is about to take 500 words out of this file.

## Notes

The scope rule has a mechanical consequence worth naming in the text: the document-first gate blocks an edit that has no focus item, and an agent that notices an unrelated bug routes around that by widening the current task. Naming the sink (`ISS-*` at triage) is what makes the gate survivable.

Landed as template commit `0154e9d` on 2026-09-03. Anchor: the heading "When to pause for the user" under "Execution" in LIFECYCLE.md; the anchor sentence is "Pause for the user only when the work genuinely requires them". LIFECYCLE.md went from 1,343 to 1,599 words in this commit and 1,632 by the end of the feature; [[TASK-0098]] trims it.

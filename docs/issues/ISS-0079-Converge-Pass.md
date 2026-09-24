---
type: "[[issue]]"
aliases: ["ISS-0079"]
id: ISS-0079
title: "Nothing checks the code against the requirement text, so a feature reaches done on the word of the agent that wrote it"
status: deferred
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-09-22
updated: 2026-09-22
source: ["[[Comparable-Systems-Spec-Kit-2026-09-22]] — GitHub Spec Kit's /speckit-converge, read 2026-09-22"]
reported_by: agent
question: "Is a convergence pass worth building, given that independent review already reads a feature adversarially? Options: (a) a new skill that appends TASK-* notes for unmet criteria, run before close-out; (b) a step inside close-out; (c) decline, because independent review covers it. Recommendation: (a). Review returns a verdict and findings; this returns work, and it is the only one of the five borrows project-os has no partial answer to."
severity: medium
component: lifecycle-rules
parent: ""
related: ["[[Comparable-Systems-Spec-Kit-2026-09-22]]", "[[ADR-0010-Test-Status-Stamped-By-Execution]]", "[[ADR-0017-Claims-About-Working-Software-Are-Derived]]", "[[ISS-0018-Traceability-Stops-At-The-Docs-Boundary]]"]
tests: []
---

# Nothing checks the code against the requirement text

## Problem

A feature reaches `done` when its tasks are resolved, its tests pass and its acceptance boxes are ticked. Every one of those is an assertion made by the agent that did the work. Nobody reads the requirement's own sentences back against the code that is supposed to satisfy them and reports what is still missing.

This is the failure [[ADR-0010-Test-Status-Stamped-By-Execution]] removed from test notes, still live one level up. A test note can no longer claim a verdict it did not earn; a feature note still can.

## Expected

Before close-out, something reads the feature's requirements, plans and tasks, inspects the code as it stands, and emits the work that remains as new `TASK-*` notes. When nothing remains it says so and writes nothing.

## Actual

`tools/skills/close-out/SKILL.md` is a nine-step checklist the same agent walks. Step 1 gates on linked test notes, step 3 advances requirements whose boxes are ticked, step 8 runs `validate-docs.sh`. The validator checks structure — links, statuses, boxes, counters — and never asks whether a tick is true. Step 9 runs independent review, which returns a claims table and a verdict, not a list of unbuilt work, and which [[ADR-0028-A-Review-Gate-Runs-Two-Rounds]] caps at two rounds.

## Evidence

Spec Kit's `templates/commands/converge.md` defines the pass this issue is about. Its constraints are the interesting part:

- Append-only. It writes exactly one thing: a new `## Phase N: Convergence` section at the bottom of `tasks.md`.
- It may not rewrite, renumber, reorder or delete an existing task, including tasks a previous convergence appended.
- It may not touch the spec, the plan, or any application code. Completing the appended tasks is the implement command's job.
- When the code already satisfies everything it must leave the file byte-for-byte unchanged, with no empty header.
- It is explicitly not a diff tool: no git, no branch comparison, no history. It assesses the present state of the code against the artifacts.

The loop is implement, converge, implement, converge, until converge returns clean.

## Next Actions

- [ ] Decide (see `question:` in the frontmatter).
- [ ] If built: settle where the appended tasks live, since project-os has one note per task rather than one list per feature, and an append-only rule has to become "create notes, never edit existing ones".
- [ ] Check the overlap with [[ISS-0018-Traceability-Stops-At-The-Docs-Boundary]] — both are about the graph stopping at the docs boundary, and a convergence pass is a cheaper answer to the same hole than coverage tags in source.
- [ ] Weigh against [[ADR-0016-Ceremony-Proportionate-To-The-Change]]: a pass that runs on every feature regardless of size is exactly the undeclared-cost pattern that ADR names.
- [x] Triaged by Edwin on 2026-09-22 and parked in [[PHASE-999-Parking-Lot|PHASE-999]]. Deferred means still wanted: the `question:` above is the decision re-adoption has to make, not one that is waiting on anyone now.

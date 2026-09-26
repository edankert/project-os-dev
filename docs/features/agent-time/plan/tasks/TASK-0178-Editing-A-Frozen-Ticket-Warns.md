---
type: "[[task]]"
id: TASK-0178
aliases: ["TASK-0178"]
title: "Editing a ticket whose release is out warns"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0097-Nothing-Stops-A-Released-Ticket-Being-Edited]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0097-Nothing-Stops-A-Released-Ticket-Being-Edited]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0035-An-Edit-To-A-Released-Ticket-Warns]]"]
---

# Editing a ticket whose release is out warns

## Definition of Done
- [x] A ticket (task, issue, change note) that was finished at the latest release tag is frozen; an edit to it in the working tree or the index is reported as FROZEN-EDIT, a warning. The release is the newest `released` REL note's `tag:`, else the newest git tag. The warning costs nothing measurable on your-trainer (warm validator 0.96 s before and after).
- [x] A tool-written supersession pointer is not reported, nor a derived reverse list, nor a rename (how the archive moves a note).
- [x] Tested with a fixture repo with a release tag (TST-0035).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0035: four mutations, all caught).

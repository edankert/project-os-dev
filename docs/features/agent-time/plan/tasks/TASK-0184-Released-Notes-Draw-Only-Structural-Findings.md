---
type: "[[task]]"
id: TASK-0184
aliases: ["TASK-0184"]
title: "A note that was finished when the last release went out draws only structural findings"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["Edwin, 2026-09-26, on PHASE-0009's open exit criterion: 'I don't think these should be seen as findings about finished notes, if they were released previously, they should only be findings about notes which potentially changed the functionality of the previouslt released notes'"]
parent: "[[ISS-0094-A-Rule-Judges-Notes-That-Closed-Before-It-Existed]]"
effort: S
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]", "[[TASK-0179]]"]
tests: ["[[TST-0035-An-Edit-To-A-Released-Ticket-Warns]]"]
---

# A note that was finished when the last release went out draws only structural findings

## Definition of Done
- [x] A task, issue, feature or requirement that was finished at the release boundary (the newest released REL note's tag, else the newest git tag) and is still finished draws only structural findings and FROZEN-EDIT; the rest are counted in one line.
- [x] Findings about work finished since the release are unchanged: they are live release work.
- [x] Tested with a fixture repo and a release tag (TST-0035, three new assertions); measured on a your-trainer clone: 189 findings hidden, and none left names a note finished at v2.1.8 apart from PHASE-014's PHASE-CHILDREN, which is about two items open now.

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0035: M5 no released filter, M6 the status at the tag ignored, M7 FROZEN-EDIT hidden too; all caught).

## Notes

Edwin's reading of PHASE-0009's fourth exit criterion: a finding about work done since the last release is not a finding about a finished note. A note released earlier should only be the subject of a finding about a newer note that changes what it shipped, and that finding belongs on the newer note.

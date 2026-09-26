---
type: "[[task]]"
id: TASK-0173
aliases: ["TASK-0173"]
title: "Supersession is written once, in the new note, and a tool stamps the old one"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0096-Superseding-Means-Editing-The-Old-Note]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0096-Superseding-Means-Editing-The-Old-Note]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0031-Supersession-Is-Stamped-On-The-Old-Note]]"]
---

# Supersession is written once, in the new note, and a tool stamps the old one

## Definition of Done
- [x] `sync-snapshot.py` stamps `superseded:` on a note that another names in `supersedes:`, and `amended_by:` for `amends:`. It calls `tools/scripts/derive-pointers.py`, in every repo without an opt-in: it writes only a missing or wrong pointer, and the fleet dry run found one (your-health ADR-0033, superseded by ADR-0034). The field keeps the old note's spelling (`superseded_by:` for designs, tasks and phases), and a `proposed` successor stamps nothing.
- [x] The validator warns when a live note cites a superseded one (CITES-SUPERSEDED, a warning; a parent's own child lists are left out); `snapshot-query.py` shows the pointer. Fleet count when it arrived: 50 warnings in five repos, none in project-os-dev.
- [x] DECISIONS.md "Superseding" says the author writes the new note only, and describes `amends:`. The ADR template gains `amends:`; SCHEMAS.md documents `amends` and `amended_by`.
- [x] Tested on a fixture pair (TST-0031).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0031: seven mutations, all caught).

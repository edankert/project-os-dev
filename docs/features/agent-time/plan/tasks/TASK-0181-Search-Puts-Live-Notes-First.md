---
type: "[[task]]"
id: TASK-0181
aliases: ["TASK-0181"]
title: "Search labels each hit with its status and puts live notes first"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0101-A-Search-Returns-Finished-Notes-Mixed-In]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0101-A-Search-Returns-Finished-Notes-Mixed-In]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0038-Search-Puts-Live-Notes-First]]"]
---

# Search labels each hit with its status and puts live notes first

## Definition of Done
- [x] `snapshot-query.py --search <text>` runs rg over `docs/`, labels each hit with id and status, lists live notes first and folds finished ones into a count unless `--all`. Without rg it scans in Python and skips `docs/archive/` as `.ignore` does.
- [x] `snapshot-query.py --links-to <ID>` lists the notes that link to an item, from the note index (TASK-0169).
- [x] The session-start orientation names both; tested (TST-0038).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0038: four mutations, all caught).

## Measured on your-trainer, 2026-09-26

`--search Strava` listed 169 live notes and folded 322 finished ones into a count, in 0.28 s; `--links-to TST-0480` in 0.29 s. The default search shows no finished note, against 64% of a plain `rg -l`.

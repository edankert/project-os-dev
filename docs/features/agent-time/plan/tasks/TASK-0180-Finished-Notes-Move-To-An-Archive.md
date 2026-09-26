---
type: "[[task]]"
id: TASK-0180
aliases: ["TASK-0180"]
title: "Finished notes whose release is out move to docs/archive/"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0091-Finished-Notes-Have-No-Archive]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0091-Finished-Notes-Have-No-Archive]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0037-Released-Finished-Tickets-Move-To-The-Archive]]"]
---

# Finished notes whose release is out move to docs/archive/

## Definition of Done
- [x] `tools/scripts/archive-notes.py` moves finished tasks, finished issues, merged change notes and retired checks whose release is out to `docs/archive/` under the same sub-path; dry run by default; never deletes.
- [x] Archived notes leave the snapshot; links into the archive still resolve; the validator raises nothing but structural findings about them.
- [x] A repo `.ignore` excludes `docs/archive/` from rg and agent search.
- [x] The close-out skill moves the lasting facts, what shipped and why, into the feature note or an ADR before a feature's tickets are archived.
- [x] Tested on a fixture repo (TST-0037), and a dry run reported on your-trainer (below).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0037: five mutations, all caught).

## Measured on a clone of your-trainer, 2026-09-26

`archive-notes.py --apply` moved 1,063 notes finished at v2.1.8: 687 tasks, 308 issues, 54 change notes and 14 retired checks. The dry run took 0.4 s. After a sync, `validate-docs.sh` passed, the walk procedures included, and no finding named an archived note except structural ones (20 were hidden and counted). project-os-cockpit's dry run: 631 notes at v1.0.0. The other repos have no release yet, so nothing moves.

Search results for eight everyday terms on that clone, with the archive out of search (`.ignore`): "Strava" went from 490 notes, 64% finished, to 310 notes, 44% finished; "backup" from 272 notes (52% finished) to 200 (36%). The notes still finished are features, requirements and tickets closed after v2.1.8, which stay in place. TASK-0181's `--search` folds those into a count.

Nothing was written to your-trainer or the cockpit: each repo archives when its owner runs `--apply`.

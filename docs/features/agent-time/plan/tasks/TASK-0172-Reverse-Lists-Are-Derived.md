---
type: "[[task]]"
id: TASK-0172
aliases: ["TASK-0172"]
title: "A relationship is written once, on the child, and every reverse list is generated"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0095-One-Relationship-Is-Written-In-Six-Places]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0095-One-Relationship-Is-Written-In-Six-Places]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0030-A-Relationship-Written-On-The-Child-Reaches-Every-List]]"]
---

# A relationship is written once, on the child, and every reverse list is generated

## Definition of Done
- [x] `sync-snapshot.py` generates a feature's and an issue's `tasks:`, a phase's lists, and the snapshot's membership from each child's `parent:` and `phase:`, keeping each list's written style. It does so through `tools/scripts/derive-lists.py`, when the repo sets `retention.derive_lists: true`; until then the sync reports how many lists would change.
- [x] A migration mode moves a fact that exists only in a parent's list onto the child first, and reports conflicts. It runs as the first step of every derivation, so a fact written only in a list is never lost; `derive-lists.py` without `--apply` is the dry run.
- [x] Adding a task writes it in one place; a test asserts the six places follow from it (TST-0030).
- [x] Run on every fleet repo in a dry run, with the changes it would make reported (table below).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0030: six mutations, all caught).

## One decision made while building it

An entry leaves a list only when the child names a different parent of the list owner's own kind: the task moved to another feature, or the issue to another phase. The first design dropped every entry whose child named some other parent. The dry run on your-trainer showed that would empty ten issues' `tasks:` lists in SNAPSHOT.yaml: there an issue's `tasks:` holds the task that fixes it, and that task's `parent:` is a feature. Both facts are true, so a child naming a parent of another kind stays listed.

## Fleet dry run, 2026-09-26

`derive-lists.py` on every repo, writing nothing. Columns: note lists that would change; facts moved from a list onto a child whose field was empty; SNAPSHOT.yaml lists that would change; snapshot entries added for live tasks; conflicts, where a list names a child whose own field names another parent of the same kind (the child wins).

| Repo | Note lists | Moved | Snapshot lists | Entries | Conflicts |
|---|---|---|---|---|---|
| articles | 4 | 0 | 0 | 0 | 0 |
| edankert.com | 0 | 0 | 0 | 0 | 0 |
| obsidian-supernote-sync | 0 | 0 | 0 | 0 | 0 |
| project-os-bench | 1 | 0 | 0 | 0 | 1 |
| project-os-cockpit | 52 | 7 | 25 | 5 | 8 |
| project-os-deck | 4 | 0 | 4 | 0 | 0 |
| project-os-dev | 16 | 1 | 4 | 0 | 8 |
| project-os | 0 | 0 | 0 | 0 | 0 |
| your-applications.com | 7 | 30 | 0 | 0 | 0 |
| your-health | 40 | 0 | 30 | 10 | 10 |
| your-sudoku | 9 | 122 | 0 | 0 | 0 |
| your-trainer | 43 | 10 | 3 | 5 | 2 |
| yourtrainer-mcp | 2 | 57 | 0 | 0 | 0 |

Every conflict is a phase list naming an item whose own `phase:` has since moved, or a snapshot copy of such a list. project-os-dev opts in with this phase. Each other repo opts in on its own commit, after its owner reads its dry run.

Measured on a your-trainer clone with the lists derived: a warm `sync-snapshot.py` takes 0.68 s, up from 0.44 s.

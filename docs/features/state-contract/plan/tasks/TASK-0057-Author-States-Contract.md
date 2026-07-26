---
type: "[[task]]"
id: TASK-0057
aliases: ["TASK-0057"]
title: "Author STATES.md — the single normative state contract (values, gates, and who writes each value)"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0014-Single-State-Contract]]"
effort: M
due: ""
depends: []
blocks: [TASK-0058]
related: [REQ-0018, ADR-0008]
tests: []
---

# Author the state contract

## Definition of Done

- [ ] One file states, per note type: allowed status values, the gates on each terminal transition, and **who or what writes the value** (agent, generator, test runner).
- [ ] Deferral is specified once, including the invariant and what is authored versus derived after [[REQ-0020-Deferral-Bookkeeping-Derived|REQ-0020]].
- [ ] Requirement advancement is specified once, matching ADR-0007 as amended — including that requirements are **not** test-gated.
- [ ] Every rule carries a pointer to the ADR that decided it, so the next amendment has one place to land.
- [ ] The file is readable as a table first, prose second; it is consulted mid-task, not studied.

## Steps

- [ ] Decide the naming question (see Notes) before writing.
- [ ] Draft the per-type table; fill the "who writes" column from FEAT-0015 and FEAT-0016.
- [ ] Fold in the deferral and requirement-advancement sections verbatim from their current best copy — this task moves text, it does not rewrite rules.
- [ ] Cross-check every claim against `validate-docs.py`; any divergence is a bug in one of the two, to be filed rather than smoothed over.

## Notes

**The "who writes the value" column is the point of the file, not decoration.** [[REQ-0019-Snapshot-Generated|REQ-0019]], [[REQ-0021-Transitions-Advance-On-Evidence|REQ-0021]] and [[REQ-0022-Test-Status-Stamped|REQ-0022]] are each precisely a change to that column. Without it those requirements have nowhere to be stated as a contract and would have to live as procedure in skills — which is what produced the four-copy problem.

**Naming.** Replace `STATUSES.md` outright, or absorb it and keep the filename? A rename breaks inbound links in nine downstream repos and in every generated adapter; keeping the name is cheaper but undersells the scope. Decide first — the answer changes every link written in TASK-0058.

**Sequencing.** Best written **after** FEAT-0013, FEAT-0015 and FEAT-0016 land, so the contract is authored once against final content rather than four times against moving content.

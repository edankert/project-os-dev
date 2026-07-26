---
type: "[[task]]"
id: TASK-0064
aliases: ["TASK-0064"]
title: "Evidence-driven transitions: focus implies doing, close-out stamps done, forward-only and never gate-exempt"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0015-Derived-State]]"
effort: M
due: ""
depends: [TASK-0060]
blocks: []
related: [REQ-0021, REQ-0006, ADR-0009]
tests: []
---

# Evidence-driven transitions

## Definition of Done

- [ ] A task named by `focus.task` advances to `doing` mechanically.
- [ ] Close-out stamps `done` on the task it closes, as part of the same operation.
- [ ] Advancement is **forward-only** — it never moves an item backwards and never lifts an item out of `deferred`.
- [ ] Every gate that applies to a typed transition applies identically to an automatic one; an automatic transition a gate would refuse **fails loudly** rather than proceeding.
- [ ] Fixture covers `VERIFY` and `DEFER-SCOPE` under automatic advancement.
- [ ] Per-repo opt-out recorded in `SNAPSHOT.yaml`, not assumed.
- [ ] The timing question (see Notes) is decided and recorded.

## Steps

- [ ] Decide when `focus` stamps (see Notes).
- [ ] Implement advancement with the forward-only and gate-respecting constraints as the first code written, not as later hardening.
- [ ] Build the gate fixtures.
- [ ] Add the opt-out key; document it in `SNAPSHOT.md`.

## Notes

**This is the highest blast-radius task in FEAT-0015** and is sequenced last for that reason: it writes to *notes*, not just to the generated index, and it writes terminal statuses. Automation that can manufacture `done` at scale is exactly the failure [[ADR-0005-Deferral-As-Descoping|ADR-0005]] named ("never flip a parked task to done") and [[ADR-0006-Requirement-Advancement-On-Evidence|ADR-0006]] named again ("ticking to fit"). Two of the criteria above are therefore restrictions rather than features.

**Timing.** Stamping `doing` the instant `focus.task` is set dirties the working tree on every context switch, and a session that browses three tasks would mark all three `doing`. Options: stamp at commit time only; stamp forward but never retract; or make it opt-in per repo. Commit-time stamping is the least intrusive and is the recommended default.

**Why this belongs in a derived-state feature at all.** 53% of tasks only ever carry one status and 39% are born `done`; ~5% pass through `doing`. Those statuses are already being derived — retrospectively, by an LLM, from memory. This replaces a recollection with an observation.

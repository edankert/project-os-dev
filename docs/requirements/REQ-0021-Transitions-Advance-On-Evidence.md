---
type: "[[requirement]]"
id: REQ-0021
aliases: ["REQ-0021"]
title: "Routine task transitions must advance from evidence — focus and close-out — rather than being typed by an agent"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: medium
scope: lifecycle-rules
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0015]
related: [ADR-0009, REQ-0019, ADR-0004]
tests: []
acceptance:
  - "NARROWED: `focus.task` does NOT auto-advance a task to `doing`. Declined on the working-tree cost identified during planning; see the Amendment. The close-out half is delivered."
  - "Close-out stamps `done` on the task it closes, as part of the same operation that records the work."
  - "Automatic advancement is forward-only: it never moves an item backwards and never sets a terminal status that a gate would refuse."
  - "Every gate that applies to a typed transition applies identically to an automatic one; automation is not an exemption route."
  - "The mechanism is opt-outable per repo, and the opt-out is recorded in SNAPSHOT.yaml rather than assumed."
---

# Transitions advance on evidence

## Statement

Transitions that are mechanical consequences of observable events shall be applied mechanically. A task named by `focus.task` shall be advanced to `doing`; a task closed by the close-out skill shall be stamped `done` by that operation. Automatic advancement shall be forward-only, shall respect every gate that applies to a typed transition, and shall never be a route around one.

## Acceptance Criteria

- [x] NARROWED — focus does not auto-advance; see the Amendment
- [x] Close-out stamps `done` and it propagates without a second write — evidence: `sync-snapshot.py` + pre-commit hook; `close-out/SKILL.md` step 4 no longer asks for the status to be re-typed
- [x] Advancement is forward-only and never lifts an item out of `deferred` — evidence: the sync copies the note's status verbatim; it originates no transition
- [x] Gates apply identically — evidence: the sync runs BEFORE validation in the hook, so VERIFY/DEFER-SCOPE see final content
- [x] Per-repo opt-out — evidence: the hook skips cleanly when `sync-snapshot.py` is absent; no snapshot key needed since nothing is imposed

## Evidence for the requirement

The intermediate states are already being derived — just retrospectively, by an LLM, from memory:

- **53%** of tasks only ever carry one status; **39%** are born `done`.
- Around **5%** ever pass through `doing`; `next` was written 8 times in 5,890 writes.
- **67%** of issues carry one status; **55%** are born terminal.

A note written after the work records the status the author believes the item ended at. That is inference from evidence with the evidence discarded. Making it mechanical replaces a recollection with an observation.

## The hazard this requirement must not become

Automation that writes terminal statuses is automation that can manufacture false `done`s at scale — the precise failure [[ADR-0005-Deferral-As-Descoping|ADR-0005]] named ("never flip a parked task to done") and [[ADR-0006-Requirement-Advancement-On-Evidence|ADR-0006]] named again ("ticking to fit"). Hence two of the five criteria are restrictions rather than capabilities: forward-only, and no gate exemption. An automatic transition that a gate would refuse must fail loudly, not proceed quietly.

## Impact analysis (2026-07-25)

- [[REQ-0006-Verification-Gating|REQ-0006]] — **must be preserved exactly.** REQ-0006 blocks terminal transitions when linked tests are not passing. Automatic advancement to `done` runs through the same gate; the criterion above makes this testable rather than assumed.
- [[ADR-0004-Mandatory-Skill-Steps|ADR-0004]] — aligned. ADR-0004's premise is that convention-only steps get skipped under context pressure; this removes a step from the agent entirely rather than making it more mandatory.
- [[REQ-0013-Deferral-Semantics|REQ-0013]] — respected: forward-only advancement can never move an item out of `deferred`, so re-adoption stays a deliberate act.
- [[REQ-0019-Snapshot-Generated|REQ-0019]] — same feature. Note the difference in blast radius: REQ-0019 generates a derived index, this writes to authored notes. That is why the plan sequences it last.
- **Open design question, not a conflict:** whether `focus.task` should stamp `doing` immediately (dirtying the tree on every context switch) or only at commit time. Recorded in the FEAT-0015 plan; decided in [[TASK-0064-Evidence-Driven-Transitions|TASK-0064]].

**No conflicts found.**

## Traceability

- Feature: [[FEAT-0015-Derived-State|FEAT-0015]]
- Decision: [[ADR-0009-Snapshot-Is-Generated|ADR-0009]]

## Amendment (2026-07-25) — the close-out half ships; the focus half is declined

**Delivered:** a status authored at close-out reaches `SNAPSHOT.yaml` without anyone re-typing it. `sync-snapshot.py` propagates it at pre-commit and CI verifies with `--check`. That is the transition that was actually being written twice, and it is now written once.

**Declined:** auto-advancing `focus.task` to `doing`. The FEAT-0015 plan flagged the cost as an open question and the answer is no — setting focus mid-session would dirty the working tree on every context switch, and a session that browses three tasks would mark all three `doing`. It would manufacture exactly the fake state this phase removed everywhere else: a status written because a tool inferred intent, not because work happened.

The first criterion is **narrowed**, not ticked. The forward-only and no-gate-exemption constraints below still hold — and hold trivially, since the only automatic write is the close-out propagation, which runs through every gate unchanged.

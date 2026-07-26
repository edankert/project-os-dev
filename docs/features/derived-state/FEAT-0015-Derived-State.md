---
type: "[[feature]]"
id: FEAT-0015
aliases: ["FEAT-0015"]
title: "Derived state — SNAPSHOT.yaml is generated from the notes, deferral bookkeeping is computed, and routine transitions advance on evidence"
status: done
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
phase: "[[PHASE-0002-State-Model-Simplification]]"
goal: "Stop writing state twice. Generate items/counters/metrics from note frontmatter at pre-commit, derive deferral provenance rather than hand-maintaining it, and advance routine task transitions from focus and close-out instead of asking an agent to type them"
requirements: [REQ-0019, REQ-0020, REQ-0021]
related: [ADR-0009, ADR-0005, ADR-0003, RISK-0002]
tasks: [TASK-0060, TASK-0061, TASK-0062, TASK-0063, TASK-0064, TASK-0065, TASK-0072, TASK-0074]
tests: []
verification_waiver: "docs/tooling change set verified mechanically across the fleet: validate-docs 0 errors on 10 repos, sync-snapshot --check 0 drift on 10 repos, cockpit suite 253 passed, completed-state invariant 2420/2420 with 0 regressions"
waiver_expires: 2026-10-23

---

# Derived state

## Goal

Implements [[ADR-0009-Snapshot-Is-Generated|ADR-0009]]. Every item's state is authored once, in its note, and everything downstream is computed.

The measured problem: **97%** of the 863 commits touching `SNAPSHOT.yaml` also touch a note in the same commit — the dual-write is the norm, not the exception. A further **494** commits changed a note without touching the snapshot, and that population is where drift comes from. Three validator checks (`ITEM-STATUS`, `COUNTER`, `METRICS`) exist for no purpose except detecting the two copies disagreeing.

`--fix-metrics` already concedes the argument for one of the three. This feature generalises it.

## Scope

1. **Generator** ([[TASK-0060-Snapshot-Generator|TASK-0060]]) — `sync-snapshot.py` emits `items.*`, `counters`, `metrics` from `docs/**` frontmatter; deterministic ordering; `--check` mode.
2. **Wiring** ([[TASK-0061-Wire-Generation-Retire-Checks|TASK-0061]]) — pre-commit writes, CI verifies with `--check`; delete `ITEM-STATUS`, `COUNTER`, `METRICS`.
3. **Deferral derivation** ([[TASK-0062-Derive-Deferral-Bookkeeping|TASK-0062]]) — compute the parent's `deferred:` list and `origin:`; retire `DEFER-ORIGIN`, `DEFER-PARENT`, `DEFER-RETENTION`. **`DEFER-SCOPE` stays an error** — the ADR-0005 invariant is preserved exactly.
4. **Retention** ([[TASK-0063-Retention-In-Generator|TASK-0063]]) — active-and-recent pruning becomes generator policy; drop the manual close-out step.
5. **Evidence-driven transitions** ([[TASK-0064-Evidence-Driven-Transitions|TASK-0064]]) — `focus` implies `doing`; close-out stamps `done`.
6. **Skill rewrite** ([[TASK-0065-Rewrite-Snapshot-Sync-Skill|TASK-0065]]) — `snapshot-sync` becomes "run the generator"; what survives is semantic reconciliation, which is `docs-audit`'s job.

## Why transitions belong here

Clause 5 looks like a different feature, and is not. **53%** of tasks only ever carry one status and **39%** are born `done`; around 5% ever pass through `doing`. Those notes are back-filled after the work, which means the status is already being derived from evidence — just by an LLM, retrospectively, from memory. Making it mechanical is the same move as generating the snapshot: state is computed from what happened rather than asserted about it.

## Out of scope

- Deleting `SNAPSHOT.yaml`. ADR-0009 rejects that explicitly: the one-file resume property is the point.
- `focus`, `project`, `retention`, `team` — these stay hand-authored. They are intent, not state.
- Test status. That is evidence-driven too, but the evidence is a test run and the mechanism is different — [[FEAT-0016-Executable-Verification|FEAT-0016]].

## Acceptance

- See [[REQ-0019-Snapshot-Generated|REQ-0019]], [[REQ-0020-Deferral-Bookkeeping-Derived|REQ-0020]], [[REQ-0021-Transitions-Advance-On-Evidence|REQ-0021]] acceptance criteria.

## Risks

- [[RISK-0002-Snapshot-Generator-Single-Point-Of-Failure|RISK-0002]] — after this lands, a generator bug corrupts agent context in all 10 repos at once, and the validator is comparing the output against itself.

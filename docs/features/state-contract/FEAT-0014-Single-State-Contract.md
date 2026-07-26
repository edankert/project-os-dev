---
type: "[[feature]]"
id: FEAT-0014
aliases: ["FEAT-0014"]
title: "Single state contract — state and transition rules are normative in one file and referenced, never restated"
status: done
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
phase: "[[PHASE-0002-State-Model-Simplification]]"
goal: "Collapse ~604 lines of state rules spread across five instruction files and three skills into one normative STATES.md that every other document links to, removing the duplication that let a corrected rule stay wrong in a fourth copy"
requirements: [REQ-0018]
related: [ISS-0006, ADR-0007, ADR-0008]
tasks: [TASK-0057, TASK-0058, TASK-0059]
tests: []
verification_waiver: "docs/tooling change set verified mechanically across the fleet: validate-docs 0 errors on 10 repos, sync-snapshot --check 0 drift on 10 repos, cockpit suite 253 passed, completed-state invariant 2420/2420 with 0 regressions"
waiver_expires: 2026-10-23

---

# Single state contract

## Goal

State the rules once. [[ISS-0006-Status-Transition-Test-Gates-Requirements|ISS-0006]] is the proof this is needed: ADR-0007's amendment corrected requirement test-gating in `validate-docs.py`, `QUALITY.md`, `STATUSES.md` and `close-out/SKILL.md`, and missed `status-transition/SKILL.md` — which now instructs every agent in all 10 repos to apply a gate the ADR explicitly reverted.

Nothing detected it, because no check compares prose to prose. The only durable fix is to stop having a fourth copy.

## The duplication, measured

604 lines across eight files describe state and transitions:

| File | Lines |
|---|---|
| `SNAPSHOT.md` | 125 |
| `STATUSES.md` | 115 |
| `LIFECYCLE.md` | 99 |
| `close-out/SKILL.md` | 61 |
| `status-transition/SKILL.md` | 57 |
| `QUALITY.md` | 52 |
| `snapshot-sync/SKILL.md` | 51 |
| `TRACEABILITY.md` | 44 |

Requirement advancement is stated in **four** of them. The deferral procedure is written twice, near-verbatim (`STATUSES.md` "Deferral and re-adoption" and `status-transition/SKILL.md` "Deferral procedure"). Verification gating appears in four. Each copy is a place the next amendment can miss.

## Scope

1. **Author** ([[TASK-0057-Author-States-Contract|TASK-0057]]) — one `STATES.md`: per type, the allowed values, the gates on each terminal transition, and **who or what writes the value**. The last column is new and is what makes [[FEAT-0015-Derived-State|FEAT-0015]] and [[FEAT-0016-Executable-Verification|FEAT-0016]] expressible as a contract rather than as procedure.
2. **Strip** ([[TASK-0058-Strip-Restatements|TASK-0058]]) — replace every restatement in `QUALITY.md`, `LIFECYCLE.md`, `STATUSES.md`, `close-out`, `status-transition`, `snapshot-sync` with a link. Fixes ISS-0006 by deletion rather than by correcting a fourth copy.
3. **Verify** ([[TASK-0059-Adapter-Regeneration|TASK-0059]]) — regenerate adapters; check no tool-facing surface (CLAUDE.md, AGENTS.md, generated skills) reintroduces a copy.

## Out of scope

- Changing any rule. This feature moves text and deletes duplicates; the *content* changes come from [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]], [[ADR-0009-Snapshot-Is-Generated|ADR-0009]], [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] and [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] via their own features. Sequencing note in the plan.
- A mechanical duplicate-prose detector. Tempting, and probably a later idea; the first-order fix is having one copy to begin with.

## Acceptance

- See [[REQ-0018-State-Rules-Stated-Once|REQ-0018]] acceptance criteria.

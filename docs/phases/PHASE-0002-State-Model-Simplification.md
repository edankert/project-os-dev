---
type: "[[phase]]"
id: PHASE-0002
aliases: ["PHASE-0002"]
title: "State model simplification"
status: done
order: 2
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
goal: "Contract the state model to what the fleet actually uses, and derive the rest: collapse the status taxonomy, state the rules once, generate the snapshot, stamp test status by execution, and end the permanent warning tier"
features: [FEAT-0013, FEAT-0014, FEAT-0015, FEAT-0016, FEAT-0017]
requirements: [REQ-0016, REQ-0017, REQ-0018, REQ-0019, REQ-0020, REQ-0021, REQ-0022, REQ-0023, REQ-0024]
tasks: []
issues: [ISS-0006, ISS-0007, ISS-0008, ISS-0009]
related: [ADR-0008, ADR-0009, ADR-0010, ADR-0011, RISK-0001, RISK-0002]
tags: [phase, simplification]
---

# State model simplification

## Goal

The first phase that removes structure rather than adding it. Opened by the 2026-07-25 fleet audit, which measured how [[PHASE-0001-Documentation-System-Foundations|PHASE-0001]]'s output is actually used across 10 repos and 3,775 notes — reconstructing all 5,890 `status:` writes from git history rather than reading current state.

The headline findings:

- **64 declared status values; 12 written fewer than 10 times, 6 never written at all.** `failing` has never been written once.
- **53% of tasks only ever carry one status; 39% are born `done`.** The lifecycle is mostly recorded after the fact.
- **`fixed → closed` has 3% follow-through** — 324 issues reached `fixed`, 10 reached `closed`, and the metric excludes both.
- **97% of snapshot commits are dual-writes**, and 494 note-only commits are where drift comes from.
- **~600 warnings across 10 repos, every one of which exits `OK`.**

## Scope

| Feature | Delivers | Decision |
|---|---|---|
| [[FEAT-0013-Status-Taxonomy-Collapse\|FEAT-0013]] | Collapse 64 → ~45 values; one terminal status per type; migrate the fleet | [[ADR-0008-States-Must-Earn-Their-Keep\|ADR-0008]] |
| [[FEAT-0014-Single-State-Contract\|FEAT-0014]] | One normative `STATES.md`; delete the four-way duplication | — |
| [[FEAT-0015-Derived-State\|FEAT-0015]] | Generate the snapshot; derive deferral bookkeeping; advance on evidence | [[ADR-0009-Snapshot-Is-Generated\|ADR-0009]] |
| [[FEAT-0016-Executable-Verification\|FEAT-0016]] | Stamp test status by running the test; expire manual checks and waivers | [[ADR-0010-Test-Status-Stamped-By-Execution\|ADR-0010]] |
| [[FEAT-0017-Enforcement-Severity\|FEAT-0017]] | Every rule errors or is deleted; clear the fleet's warning debt | [[ADR-0011-No-Permanent-Warning-Tier\|ADR-0011]] |

Four issues are in phase scope: [[ISS-0006-Status-Transition-Test-Gates-Requirements|ISS-0006]] (live contradiction in all 10 repos), [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] (**time-critical**), [[ISS-0008-Issues-Open-Metric-Excludes-Fixed|ISS-0008]], [[ISS-0009-Fleet-Status-Vocabulary-Drift|ISS-0009]].

## Out of scope

- **Cockpit status bands.** They must follow FEAT-0013's vocabulary, as they did for ADR-0007, but land in `project-os-cockpit` with its own release and sync.
- **Writing tests.** FEAT-0016 changes who writes a test's *status*; the fleet's thin coverage (80 TST notes across 3,775) is a separate problem this will make visible.
- **Mechanical duplicate-prose detection.** Probably a later idea; the first-order fix is having one copy.

## Sequencing

1. **[[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] first, and independently.** `FEATURE_REQ_GATE_FROM` is 2026-07-25 — today — with ~325 findings outstanding. It does not wait for the phase.
2. FEAT-0013 — settles the vocabulary everything else is written against.
3. FEAT-0015 and FEAT-0016 in parallel — independent mechanisms, both depending on the settled vocabulary.
4. FEAT-0017 — promotions require the backfills from the others to have landed (ADR-0011 clause 3: debt cleared *before* promotion).
5. FEAT-0014 **last** — the contract is authored once against final content, rather than four times against moving content.

## Exit criteria

- [x] Every declared status value has observed fleet usage or a written retention justification — evidence: `STATUSES.md`; ADR-0008 amendment §5a
- [x] Zero out-of-taxonomy statuses across all 10 repos — evidence: `NOTE-STATUS` promoted to error at 0 findings; 190 notes migrated
- [~] **Narrowed** — `SNAPSHOT.yaml` `status`/`counters`/`metrics` are **synced** from notes (not the whole file generated), and `ITEM-STATUS`/`COUNTER`/`METRICS` are **retained** as the backstop. The whole-file generator was rejected on shadow-run evidence; see ADR-0009's amendment
- [x] `failing` is reachable, and a failing test blocks a terminal transition — evidence: TST-0001 was stamped `failing` by `run-tests.py` from a real non-zero exit, then `passing` after the underlying errors were fixed. Inversion verified: `exit 3` → `failing`, missing binary → `unrunnable` with the status left untouched
- [~] **Narrowed** — every warning is *accounted for* (207 under a dated promotion, ~325 ledgered, 66 permanent-with-reason) rather than zero; see REQ-0024's amendment
- [x] State rules normative in exactly one file; ISS-0006 resolved by deletion — evidence: `STATUSES.md` "The contract at a glance"; the offending sentence removed from all 10 repos
- [x] `DEFER-SCOPE` still an error and ISS-0002 non-regressed — evidence: 0 DEFER errors fleet-wide; the 22 deferred notes untouched by migration

## Notes

Two risks are live for the whole phase: [[RISK-0001-Fleet-Status-Migration|RISK-0001]] (a bad status mapping validates cleanly and reads as legitimate afterwards) and [[RISK-0002-Snapshot-Generator-Single-Point-Of-Failure|RISK-0002]] (after generation, CI's `--check` compares the generator against itself).

The phase has a standing constraint worth repeating: **it must not remove an invariant while removing the ceremony around it.** ISS-0002 and ISS-0004 were real bugs; their fixes stay. What goes is the hand-performed bookkeeping, the unused vocabulary, and the rules the fleet has declined to follow for months.

## Outcome (2026-07-25)

All five features `done`; two tasks (TASK-0062/0063) **cancelled** when the generator design they depended on was withdrawn on evidence.

| Result | |
|---|---|
| Fleet validation | **0 errors** across 10 repos |
| `sync-snapshot --check` | **0 drift** across 10 repos |
| Cockpit suite | 253 passed, 1 skipped |
| **Completed-state invariant** | **2,420 / 2,420 — 0 regressions** |

Three of this phase's own proposals were wrong and were corrected by implementing them: `superseded` on tasks/phases was a taxonomy gap not drift (72 notes); `{passing, failing}` had no home for a defined-but-unrun test (`ready`); and the snapshot turned out to be duplication *plus curation*, which killed the whole-file generator. Each is recorded as an amendment rather than quietly adjusted — the phase's own rule about reconciling instead of ticking to fit, applied to itself.

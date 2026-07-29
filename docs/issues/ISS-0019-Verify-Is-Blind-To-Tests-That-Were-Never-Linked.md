---
type: "[[issue]]"
id: ISS-0019
aliases: ["ISS-0019"]
title: "VERIFY iterates only over tests that exist, so an item reaching terminal with zero linked tests and no waiver passes silently — 52 registered items in this repo did exactly that, against QUALITY.md's stated rule"
status: open
severity: high
owner: user:edwin
created: 2026-07-29
updated: 2026-07-29
component: tooling
source: ["intake 2026-07-29: articles repo, quality-without-reading thesis, finding 7"]
phase: "[[PHASE-999-Parking-Lot]]"
related: [ADR-0017, ADR-0010, REQ-0006, ISS-0021]
tests: []
---

# VERIFY is blind to tests that were never linked

## Problem

`QUALITY.md` states the rule without ambiguity:

> If a terminal status must be set without passing tests (docs-only chore, config-only change), record an explicit `verification_waiver: <reason>` in the note frontmatter. The waiver is a logged artifact (the validator reports it as a warning); **silent skips are a build failure.**

Silent skips are not a build failure. They are silent.

`validate-docs.py:1397-1415` is the no-waiver branch of the verification invariant:

```python
else:
    for tst in sorted(linked_tests):
        ...  # not found -> VERIFY; not passing -> VERIFY; passing but stale -> VERIFY
```

Every finding the gate can produce is inside that loop body. When `linked_tests` is empty the body never executes, the branch completes, and nothing is reported. The gate checks the tests an item *has*; it cannot see the tests an item *lacks*.

The asymmetry is the defect. Closing an item **with** a waiver is visible — `VERIFY-WAIVED` warns, and since [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]] the waiver must carry `waiver_expires:` or `WAIVER` errors. Closing an item with **nothing at all** is cheaper *and* quieter than closing it honestly under a waiver. The incentive points the wrong way.

## Repro

Any repo carrying the validator:

1. Create a task note, `status: done`, no `tests:` key, no `verification_waiver:`.
2. Register it in `SNAPSHOT.yaml` under a feature.
3. Run `bash tools/scripts/validate-docs.sh`.

## Expected

`VERIFY` reports the item as terminal without verification and without a recorded waiver — the "silent skip" QUALITY.md calls a build failure.

## Actual

Clean.

## Measured in this repo, 2026-07-29

Counting only snapshot-registered items at their type's terminal status, with no `tests:` in either the snapshot entry or the note frontmatter, and no `verification_waiver:` in either:

| collection | terminal items with neither test nor waiver |
|---|---:|
| tasks (`done`) | 40 |
| issues (`fixed`) | 7 |
| features (`done`) | 5 |
| **total** | **52** |

Sample: `TASK-0078`, `TASK-0079`, `TASK-0077`, `TASK-0075`, `TASK-0023`…`TASK-0031`.

This is a **floor**, not a count. Retention prunes done tasks and closed issues out of the snapshot (`retention.keep_done_tasks_in_snapshot: false`), so historical items are not in the population at all, and the validator's item walk starts from the snapshot.

The number also explains why nobody noticed: 52 clean items look exactly like 52 verified items. There is no surface anywhere in the system on which the two differ.

## Root cause

The check was written to validate links, and inherited its shape from the collections around it — `LINK` integrity, the deferral checks, the feature task walk are all "for each reference, is it sound?" loops. That shape cannot express a cardinality rule, and the verification invariant is a cardinality rule: *at least one*, or an explicit waiver.

`REQ-0006` ("Verification gating must block status transitions when linked tests are not passing") encodes the same blind spot in its own wording. *"When linked tests are not passing"* is conditional on tests being linked, so the requirement is literally satisfied by the current behaviour. The requirement and the implementation agree with each other and both disagree with `QUALITY.md`.

## Relationship to ADR-0017

This is a clause-3 instance under [[ADR-0017-Claims-About-Working-Software-Are-Derived|ADR-0017]]: *never written by the party seeking the transition.* An item closing with no test and no waiver is a verification claim written by omission — the agent seeking `done` asserts sufficiency by declining to say anything, and nothing can contradict it. Whereas the waiver path makes the same assertion nameable, countable and expiring.

It is also the mechanical instance of the intake's finding 7, "absence is invisible." The conceptual version is about untested regions of code, which project-os cannot see (recorded as a non-goal in ADR-0017). This version is about untested *items*, which it can see perfectly well and does not look at.

## Fix sketch

An error when a terminal item has no linked tests and no waiver — i.e. hoist the emptiness case out of the loop. Two things to settle first, because the naive fix would fail this repo's own build with 52 errors on the next commit:

- **Requirements are correctly exempt** and must stay so ([[ADR-0007]], enforced at `validate-docs.py:1374`, with a nine-line comment explaining why re-adding test-gating for requirements would reintroduce retired `verified` through the back door). The fix touches tasks, issues and features only.
- **The 52 need a disposition before the check is armed.** `tools/GRANDFATHERED.yaml` exists for exactly this and `ADR-0011` permits a dated cutover no more than 90 days out. `ISS-0007` is the cautionary precedent — a cutover that armed over ~325 unresolved findings — so the backfill comes first and the arming date follows it.

Whether the honest disposition for most of the 52 is a waiver or a test is the real question, and it is a judgement about this project, not a validator change. A tooling repo whose tasks are documentation edits may legitimately be mostly waivers; if so, `ISS-0021`'s budget concern is where that lands.

## Blast radius

Every repo carrying the validator. The check has never fired on this case in any of them, so the fleet-wide population is unknown and is the first thing the fix needs to measure — `validate-fleet.sh` with the emptiness case armed as a warning gives the number before anything is promoted.

## Next Actions

- [ ] Confirm the reading by inversion: add a fixture item, terminal, no tests, no waiver; assert the current validator is silent.
- [ ] Measure the fleet-wide population with the check emitting as a warning.
- [ ] Decide the disposition for the existing 52 here (waiver vs test), and whether `REQ-0006`'s wording needs amending or superseding — it currently sanctions the bug.
- [ ] Arm as an error behind a dated cutover per ADR-0011, after the backfill, not before (ISS-0007).
- [ ] Author a `TST-*` covering both branches — empty and non-empty — since the empty branch is the one that was never covered.

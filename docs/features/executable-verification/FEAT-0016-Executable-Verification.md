---
type: "[[feature]]"
id: FEAT-0016
aliases: ["FEAT-0016"]
title: "Executable verification — test status is stamped by running the test, manual checks expire, waivers get an end date"
status: done
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
phase: "[[PHASE-0002-State-Model-Simplification]]"
goal: "Make the verification gate load-bearing: a TST-* note with a command has its status written by executing that command, manual tests carry a freshness date and go stale, and verification_waiver stops being open-ended"
requirements: [REQ-0022, REQ-0023]
related: [ADR-0010, ADR-0004, REQ-0006]
tasks: [TASK-0066, TASK-0067, TASK-0068]
tests: []
---

# Executable verification

## Goal

Implements [[ADR-0010-Test-Status-Stamped-By-Execution|ADR-0010]].

`QUALITY.md` builds its close-out rules on one gate: no terminal status while a linked `TST-*` is not `passing`. It is the most-referenced rule in the system, and across 10 repos and 5,890 status writes it has **never observed a failure** — `failing` has been written zero times. 78% of test notes are born `passing`; 99% never change status again. Meanwhile 48 notes carry a `verification_waiver`, so the documented escape hatch has been used infinitely more often than the gate has fired.

The cause is structural, not cultural: a test note's status is written by the agent that wants the transition, at the moment it wants it. Nothing writes to that note again — least of all a CI run that goes red three weeks later.

## Scope

1. **Schema** ([[TASK-0066-Test-Command-Schema|TASK-0066]]) — `command:`, `last_run:`, `last_verified:` on the test template and `SCHEMAS.md`; `test-authoring` gains the step; `waiver_expires:` added.
2. **Runner** ([[TASK-0067-Test-Runner|TASK-0067]]) — `run-tests.py` executes each `command:` and stamps `passing`/`failing` + `last_run:` + exit code. Hand-editing status on a note that has a `command:` becomes a validator error.
3. **Expiry** ([[TASK-0068-Staleness-And-Waiver-Expiry|TASK-0068]]) — manual tests go stale past a configured window and stop satisfying `VERIFY`; expired waivers are an error.

## What this does not add

**No `stale` status.** Staleness is a validator *finding*, not a state — adding a value would regrow the taxonomy [[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]] is cutting, and would let an agent set it by hand, which is the exact failure being removed. `failing` is retained by ADR-0008 for this feature's sake: it is unreachable today, not unwanted.

## Out of scope

- Writing tests. This feature changes who writes a test's *status*; the fleet's thin test coverage (80 TST notes across 3,775) is a separate problem that this will make visible.
- Replacing CI. The runner stamps note status from a command; it is not a test framework and does not own the suite.

## Expected first-run effect

The first honest run across the fleet will produce failing and stale results. Those tests are failing and stale **today** — silently. Surfacing them is the deliverable, not a regression introduced by it, and the rollout should say so in advance so the first red build is not misread.

## Acceptance

- See [[REQ-0022-Test-Status-Stamped|REQ-0022]] and [[REQ-0023-Manual-Verification-Expires|REQ-0023]] acceptance criteria.

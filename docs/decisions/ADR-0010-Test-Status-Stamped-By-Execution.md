---
type: "[[adr]]"
id: ADR-0010
aliases: ["ADR-0010"]
title: "Test status is stamped by execution, not asserted by an author"
status: accepted
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: ["review:2026-07-25-fleet-state-audit"]
decision: "A `TST-*` note that carries a `command:` has its `status` written only by executing that command; hand-editing the status of an executable test is a validator error. Manual tests keep an author-written status but must carry `last_verified:` and go stale after a project-configured window. `verification_waiver` gains an expiry date"
context: "In 5,890 status writes across 10 repos, `failing` has never been written once. 78% of TST-* notes are born `passing` and 99% never change status again. Meanwhile 48 notes carry a `verification_waiver` — the escape hatch is used more often than the gate has ever fired, which is to say infinitely more often. The verification gate is the centrepiece of QUALITY.md and it is entirely self-certified"
alternatives:
  - "Trust authors and audit periodically — rejected: that is the current design, and it has produced zero recorded failures in 5,890 writes across ten repos and several years. The absence of failure is not evidence of passing tests; it is evidence that nobody returns to a note when CI goes red"
  - "Delete TST-* notes and rely on CI alone — rejected: CI knows a suite failed, not which requirement or task the failing check was supposed to gate. The traceability from REQ/TASK to a specific verification is the only thing the note adds, and it is the thing worth keeping"
  - "Require every test to be automated — rejected: TESTING.md's tiers include genuine manual acceptance checks (device behaviour, visual review, third-party flows). Forcing them into a runner produces fake automation and the same self-certification one layer down"
  - "Infer test status from the last CI run of the whole suite — rejected: it collapses per-test granularity to per-run, so a note gating one requirement would flip on an unrelated failure elsewhere in the suite"
consequences:
  - "`failing` becomes a reachable state for the first time; ADR-0008 retains it in the collapsed taxonomy specifically for this"
  - "The verification gate in QUALITY.md becomes load-bearing: VERIFY can block a terminal transition on evidence rather than on an assertion by the agent seeking the transition"
  - "TST-* notes gain `command:` and `last_run:`; SCHEMAS.md and the test template change; test-authoring gains a step"
  - "Staleness is enforced as a validator finding rather than a new status, keeping the collapsed taxonomy from regrowing (ADR-0008)"
  - "`verification_waiver` gains a required expiry date — a permanent waiver is indistinguishable from deleting the rule, and 48 of them currently have no end"
  - "Repos with no runnable verification will start reporting stale manual tests. That is the true state being made visible, not a new problem"
  - "A test whose command cannot run in the validator's environment (device, network, credentials) must be declared manual; misdeclaring it produces a permanently failing note, which is the correct pressure"
supersedes: ""
superseded: ""
related: [ADR-0004, ADR-0007, REQ-0006, FEAT-0016]
---

# Test status is stamped by execution

## Context

`QUALITY.md` builds its close-out rules on one gate: an item may not reach a terminal status while a linked `TST-*` is not `passing`. `validate-docs.py` implements it as the `VERIFY` check. It is the most-referenced rule in the system.

It has never once observed a failure.

Across 10 repos and 5,890 status writes reconstructed from git history:

- **`failing` was written zero times.** Not rarely — never.
- **78%** of `TST-*` notes are created already at `passing`.
- **99%** of test notes only ever hold one status for their entire lifetime.
- **48** notes carry a `verification_waiver`, the documented escape hatch.

The mechanism is not mysterious. A test note's status is written by an LLM at the moment it writes the note, asserting the outcome it expects. Nothing writes to that note again — least of all a CI run that goes red three weeks later. ADR-0007 diagnosed the same shape one level up and retired `verified` for it: *"set on delivery or on nothing far more often than on proof."* The same sentence is true of `passing`, and for the same reason.

The consequence is that the gate audits only those who already comply, exactly as ADR-0007 observed of the requirement-level gate: no link means an empty loop means a silent pass, and a self-written `passing` means the check confirms what the author just asserted.

## Decision

### 1. Executable tests are stamped, not asserted

A `TST-*` note may declare a `command:`. When it does:

- `status` is written **only** by `tools/scripts/run-tests.py`, which executes the command and records `passing`/`failing` plus `last_run:` (timestamp) and the exit code.
- A commit that changes `status` on a note with a `command:` without a corresponding `last_run:` change is a validator error.

### 2. Manual tests are dated, and expire

A test with no `command:` keeps its author-written status and must carry `last_verified:`. Beyond a project-configured window (default 90 days) the validator reports it as stale, and a stale test does not satisfy the `VERIFY` gate.

Staleness is a **finding, not a status**. Adding a `stale` value would regrow the taxonomy ADR-0008 is cutting, and would let an agent set it by hand — the failure this ADR exists to remove.

### 3. Waivers expire

`verification_waiver` becomes `verification_waiver: <reason>` plus `waiver_expires: <date>`. QUALITY.md already calls a waiver "a logged artifact"; a log entry with no end date is a rule deletion written in the passive voice. The 48 existing waivers are dated during migration.

## Why this and not more enforcement

The tempting alternative is to keep the model and demand discipline: require evidence in the note, require review, require a waiver. All three already exist. Evidence pointers are required by ADR-0006, review by QUALITY.md, waivers by the same file — and the measured result is 0 failures, 206 missing reviews, and 48 open-ended waivers.

The pattern across ADR-0007, ADR-0008 and this decision is the same: when a rule is uniformly unfollowed across every repo for months, the instrument is wrong. Here the instrument is asking the party seeking the transition to certify that the transition is allowed. Replacing assertion with execution is the smallest change that removes the conflict of interest.

## Consequences

See frontmatter. The load-bearing one: the first honest run of the fleet after this lands will surface failing and stale tests that are failing and stale *today*, silently. That is the point, and it should be expected rather than treated as a regression introduced by the change.

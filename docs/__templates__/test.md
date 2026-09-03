---
type: "[[test]]"
id: TST-0000
title: ""
status: ready
owner: unassigned
created: 2026-01-27
updated: 2026-01-27
source: []
scope: feature
level: system       # unit | integration | system | e2e | acceptance
entrypoint: ""
command: ""          # runnable check; when set, `status` is written by the runner, never by hand (ADR-0010)
last_verified: ""    # manual tests only (no `command:`) — date the procedure was last performed; goes stale
covers: []           # THE verification link (ADR-0032): [[FEAT-...]] / [[ISS-...]] / [[REQ-...]]. One direction, one encoding.
issues: []           # context only — what this test VERIFIES goes in covers:
tasks: []
artifacts: []
adequacy: ""
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
# level: acceptance only; delete on an executable test. Fields explained in SCHEMAS.md, test.md ("Acceptance fields").
area: ""             # the human grouping, one walk's worth of related checks; the verdict lives in the release ledger, not here (ADR-0037)
---

# <Test>

## Purpose
<What does this test verify?>

> **Status is evidence, not intent** (`tools/instructions/STATUSES.md` `[[test]]`). A test with a `command:` records no verdict: it rests at `active`, CI runs it on every push, and `python3 tools/scripts/run-tests.py` reproduces the run locally without writing anything (ADR-0025). A test without one is manual: it carries a hand-written `passing` or `failing`, `ready` means defined and not yet run, and `last_verified:` must stay current or the verification gate stops accepting it.

## Procedure
- <step-by-step>

## Expected results
- <observable outcomes>

## Evidence (fill after running)
- <paths/log excerpts/screenshots/etc>

## Adequacy (who verifies this test?)
- <For automated tests guarding a fix: evidence the test fails when the fix is reverted/broken (mutation result, revert-run, or reasoning). A test that cannot fail does not guard.>

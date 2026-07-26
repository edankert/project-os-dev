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
kind: manual
level: system
entrypoint: ""
command: ""          # runnable check; when set, `status` is written by the runner, never by hand (ADR-0010)
last_verified: ""    # manual tests only (no `command:`) — date the procedure was last performed; goes stale
requirements: []
features: []
issues: []
tasks: []
artifacts: []
evidence: []
last_run: ""
adequacy: ""
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: []
---

# <Test>

## Purpose
<What does this test verify?>

> **Status is evidence, not intent.** `ready` means defined but not yet executed — that is the state a new test note is created in. A test with a `command:` has its `status` written by `tools/scripts/run-tests.py` from the exit code; hand-editing it is a validator error. A test without one is manual: keep `last_verified:` current, because a stale manual test stops satisfying the verification gate.

## Procedure
- <step-by-step>

## Expected results
- <observable outcomes>

## Evidence (fill after running)
- <paths/log excerpts/screenshots/etc>

## Adequacy (who verifies this test?)
- <For automated tests guarding a fix: evidence the test fails when the fix is reverted/broken (mutation result, revert-run, or reasoning). A test that cannot fail does not guard.>

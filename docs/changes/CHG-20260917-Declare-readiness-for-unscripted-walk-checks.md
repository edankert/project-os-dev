---
type: "[[change]]"
id: CHG-20260917-Declare-readiness-for-unscripted-walk-checks
title: "Declare readiness for unscripted walk checks"
status: merged
owner: user:edwin
created: 2026-09-17
updated: 2026-09-17
source: ["Your Trainer FEAT-0122 A5/A8: an owed unscripted check can be unwalkable on one platform"]
commit: ""
pr: ""
impacts: []
issues: []
features: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]"]
---

# Declare readiness for unscripted walk checks

## Summary
An unscripted acceptance check can declare a preparation or decision reason for one platform. The shared walk generator validates that declaration, carries it into the check row, and prints it on the generated sheet. A malformed declaration shows a decision warning instead of an apparently ready card. None of these labels changes the set of checks owed by the platform.

## Impact

- No screen changed in this repository: the shared generator supplies readiness data for unscripted release checks.

## Documentation Coverage (All Types Considered)
Set each item to one of: `updated`, `new`, `not-applicable`, `deferred`.

- features: updated
- requirements: not-applicable
- tasks: updated
- issues: not-applicable
- tests: updated
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable
- changes: new
- snapshot: updated

## Follow-ups
- [x] Validate a platform readiness map on acceptance checks. Print the matching reason on fallback rows, and hold malformed declarations behind a visible decision warning.
- [x] Test valid, invalid and platform-isolated declarations. Twelve focused generator tests and the shared sheet test pass; the generator is synced to Your Trainer and both cockpit copies.

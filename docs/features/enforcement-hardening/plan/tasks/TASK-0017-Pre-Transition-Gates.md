---
type: "[[task]]"
id: TASK-0017
title: "Add pre-transition gates to status-transition skill"
status: done
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0005-Enforcement-Hardening]]"
effort: M
due: ""
depends: []
blocks: []
related: [REQ-0006]
tests: []
---

# Add pre-transition gates to status-transition skill

## Definition of Done
- [x] Status-transition skill includes verification gate (check tests before done/closed/verified)
- [x] Status-transition skill includes phase alignment gate (check task phase vs focus.phase before doing)
- [x] Status-transition skill includes claim check gate (check claimed_by before doing)
- [x] All gates are pre-transition — checked before the status change is applied

## Note
The claim check gate will be removed when FEAT-0004 (Snapshot Simplification) is implemented.

---
type: "[[change]]"
id: CHG-20260916-Name-the-screen-on-each-walk-action
title: "Name the screen on each walk action"
status: merged
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["Your Trainer FEAT-0122 B5: name the screen beside each current action; standalone Chrome render of the Android walk, 2026-09-16"]
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

# Name the screen on each walk action

## Summary
The shared walk generator shows a screen's readable title beside each action when the procedure names its `SUR-*` id. A Chrome render of Your Trainer's Android walk exposed `SUR-0033` as the heading for Quick Ride cockpit. Unknown ids remain visible so a missing surface note does not hide the source.

## Impact

- No screen changed in this repository: the shared sheet and payload generator resolve a known surface id to its title. The cockpit's change note records the rendered walk screen.

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
- [x] Resolve a known `SUR-*` id to its title and preserve the id for the link. An unknown id stays visible.
- [x] Verify the generated sheet and cockpit payload, then sync the generator into both consumers. The upstream sheet has 157 passing assertions, the preparation fixture has eight passing tests, and the cockpit agreement fixture has six passing tests.

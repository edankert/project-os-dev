---
type: "[[change]]"
id: CHG-20260916-Declare-release-walk-prerequisites-and-selective-setup
title: "Declare release walk prerequisites and selective setup"
status: merged
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["Your Trainer FEAT-0122, 2026-09-16: implement the guided release walk"]
commit: ""
pr: ""
impacts: []
issues: []
features: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TASK-0125-Retain-Declared-Preparation-And-Relevant-Setup]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]"]
---

# Declare release walk prerequisites and selective setup

## Summary
The release walk will keep authored preparation actions and show only the setup needed by the observations still owed. The generator and validator will share one explicit contract, so a cleared check cannot remove the actions needed to reach a later check.

## Impact

- No screen changed: this repository supplies the walk generator and procedure contract; the page is owned by project-os-cockpit.

## Documentation Coverage (All Types Considered)
Set each item to one of: `updated`, `new`, `not-applicable`, `deferred`.

- features: new
- requirements: new
- tasks: new
- issues: updated
- tests: updated
- workflows: updated
- decisions: new
- risks: not-applicable
- changes: new
- snapshot: updated

## Follow-ups
- [ ] Define the authored prerequisite and selective setup syntax in the template and rules.
- [ ] Implement matching generator and validator behavior.
- [ ] Correct survey hierarchy when a child screen changes without its parent.
- [ ] Prove the contract with fixtures and sync both consumers.

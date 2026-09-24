---
type: "[[change]]"
id: CHG-20260924-Work-In-Progress-Has-A-Snapshot-Entry
title: "The validator warns when a focus item or an in-flight task has no snapshot entry"
status: merged
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot]]"]
commit: ""
pr: ""
impacts: ["tools/scripts/validate-docs.py", "tools/scripts/test-snapshot-membership.sh"]
issues: ["[[ISS-0084-An-In-Flight-Task-Can-Be-Missing-From-The-Snapshot]]"]
features: []
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[TASK-0161]]", "[[TST-0022]]"]
---

# The validator warns when a focus item or an in-flight task has no snapshot entry

## Summary

`validate-docs.sh` now reports two new findings. FOCUS-MEMBERSHIP is a focus item with a note but no entry in `SNAPSHOT.yaml`. TASK-MEMBERSHIP is a `backlog` or `doing` task that an in-flight feature, phase or issue lists, but that has no `items.tasks` entry of its own. Both are warnings until 2026-12-23 and errors after.

## Impact

- No screen changed: a validator check.

When the fleet next syncs, five repos will see new warnings: your-health 8, project-os-cockpit 7, your-trainer 5, your-applications.com 1 and yourtrainer-mcp 1. Each is fixed by adding the missing snapshot entry.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: not-applicable
- tasks: new (TASK-0161)
- issues: new and fixed (ISS-0084)
- tests: new (TST-0022)
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable (no new dependency, variable or path)
- changes: new (this note)
- snapshot: updated

## Follow-ups

- [ ] Each of the five repos adds its missing entries before 2026-12-23.

---
type: "[[task]]"
id: TASK-0011
aliases: ["TASK-0011"]
title: "Remove claimed_by/claim_started from item schema and instructions"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0004-Snapshot-Simplification]]"
fixes: []
effort: S
due: ""
depends: []
blocks: [TASK-0009, TASK-0012]
related: []
tests: []
---

# Remove claimed_by/claim_started from item schema and instructions

## Definition of Done
- [x] SNAPSHOT.md no longer documents claimed_by or claim_started fields
- [x] Status-transition skill no longer includes claim-check gate
- [x] Snapshot-sync skill no longer includes stale-claim detection
- [x] HANDOFF.md no longer references claimed_by

## Steps
- [x] Remove claimed_by/claim_started from SNAPSHOT.md item fields
- [x] Update status-transition/SKILL.md (remove claim check from pre-transition gates)
- [x] Update snapshot-sync/SKILL.md (remove stale claim detection step)
- [x] Update HANDOFF.md (remove claim-related checklist items)
- [x] Search for remaining references across all files

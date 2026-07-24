---
type: skill
id: SKILL-STATUS-TRANSITION
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, statuses]
---

# Skill: Status transition

## When to use
- Any time you move an item between lifecycle states (task, issue, feature, risk, workflow).

## Inputs
- Item ID and target status.

## Outputs
- Note + snapshot updated consistently.

## Checklist
1. Confirm the transition is allowed (see `../../instructions/STATUSES.md`).
2. **Pre-transition gates:**
   - Verification gate: before transitioning a task to `done`, issue to `closed`, requirement to `verified`, feature to `done`, or phase to `done`, verify linked `TST-*` notes and required child work are complete.
   - Phase alignment gate: before transitioning a task to `doing`, check the task `phase` (or inherited parent feature phase) against `focus.phase` in `../../../SNAPSHOT.yaml`. If the task is ahead of the active phase, stop and request explicit user confirmation.
3. Update `../../../SNAPSHOT.yaml`:
   - set the item status
   - update `focus` if this becomes the active item
4. Update the corresponding note frontmatter `status` and `updated`.
5. If the transition implies completion:
   - consider whether a `CHG-*` note is required
   - update related items (e.g. issue to `fixed`, feature progression)

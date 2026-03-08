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
2. **Pre-transition gates (check before applying the transition):**
   - **Verification gate** — if transitioning a task to `done`, issue to `closed`, requirement to `verified`, or feature to `done`:
     - List all linked `TST-*` IDs.
     - Verify each test is `status: passing`.
     - If any linked test is not `passing`: **STOP. Do not apply the transition.** Report which tests are blocking.
     - If no tests are linked and the item involves a functional code change: flag to the user that verification may be missing.
   - **Phase alignment gate** — if transitioning a task to `doing`:
     - Check the task's `phase` property (or inherited from parent feature).
     - Check `focus.phase` in `../../../SNAPSHOT.yaml`.
     - If the task's phase is ahead of the active phase: **STOP. Flag to the user** that this task belongs to a future phase. The user may override, but the override must be explicit.
3. Update `../../../SNAPSHOT.yaml`:
   - set the item status
   - update `focus` if this becomes the active item
4. Update the corresponding note frontmatter `status` and `updated`.
5. If the transition implies completion:
   - consider whether a `CHG-*` note is required
   - update related items (e.g. issue to `fixed`, feature progression)

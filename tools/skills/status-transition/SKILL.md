---
type: skill
id: SKILL-STATUS-TRANSITION
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-04
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
1. Confirm the transition is allowed. **`../../instructions/STATUSES.md` is normative** — allowed values, the gate on each terminal transition, and who writes the value. Do not rely on a restatement anywhere else; there are none by design (ISS-0006).
2. **Pre-transition gates:**
   - Terminal gates: the gate on each terminal status is stated once in `../../instructions/STATUSES.md`, "The contract at a glance"; check it before the transition.
   - Phase alignment gate: before transitioning a task to `doing`, check the task `phase` (or inherited parent feature phase) against `focus.phase` in `../../../SNAPSHOT.yaml`. If the task is ahead of the active phase, whether it runs now is the user's decision (`../../instructions/LIFECYCLE.md`, "When to pause for the user").
   - Deferral gate: transitioning to `deferred` is a **descoping operation**, not a plain status flip — run the deferral procedure below, all steps in the same turn.
3. The snapshot follows the note: `tools/scripts/sync-snapshot.py` propagates the status at pre-commit (`../../instructions/LIFECYCLE.md`, "Mandatory Automated Documentation"). Set `focus` by hand if this becomes the active item.
4. Update the corresponding note frontmatter `status` and `updated`.
5. If the transition implies completion:
   - consider whether a `CHG-*` note is required
   - update related items (e.g. issue to `fixed`, feature progression)

## Requirement advancement (`approved` → `implemented`)

Requirements are advanced by the work that delivers them, not on their own schedule:

1. `draft` → `approved`: the criteria are agreed and features may now implement against them (`../feature-scaffold/SKILL.md`, step 7 "Requirement approval gate").
2. `approved` → `implemented`: terminal, set at feature close-out (`../../instructions/STATUSES.md` `[[requirement]]`; procedure in `../close-out/SKILL.md`, step 3 "Requirement advancement").

## Deferral procedure (transition to `deferred`)

`deferred` never satisfies completeness (`../../instructions/STATUSES.md`, "Deferral and re-adoption"). All steps in one turn:

1. **Descope from the parent**: remove the item's ID from the parent's scope list (feature `tasks:`) and add it to the parent's `deferred:` list — in both the parent note and `../../../SNAPSHOT.yaml`.
2. **Record provenance**: on the deferred item, set `origin:` to the former parent link and clear `parent:`.
3. **Assign a forward home**: set `phase:` to a real future phase when one exists; otherwise use the parking lot — create `../../../docs/phases/PHASE-999-Parking-Lot.md` once if absent (status `planned`, all-9s sentinel IDs are counter-exempt) and point `phase:` at it.
4. **Keep it active**: the item stays in the snapshot; retention never prunes `deferred` (`../../instructions/STATUSES.md`, "Deferral and re-adoption").

## Re-adoption (transition out of `deferred`)

1. Assign a new (or the original) `parent:` and add the ID back to that parent's scope list (note + snapshot).
2. Set the non-parked status for the type (`../../instructions/STATUSES.md`, "Deferral and re-adoption") and update `phase:` to the real phase of the new work.
3. Keep `origin:` as history of where the item was first scoped.

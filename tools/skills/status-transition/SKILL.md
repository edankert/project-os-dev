---
type: skill
id: SKILL-STATUS-TRANSITION
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-07-21
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
   - Verification gate: before transitioning a task to `done`, issue to `closed`, requirement to `verified`, feature to `done`, or phase to `done`, verify linked `TST-*` notes are passing and every child in the scope list is scope-resolved (`done` or `cancelled` — never `deferred`; see `../../instructions/QUALITY.md`).
   - Phase alignment gate: before transitioning a task to `doing`, check the task `phase` (or inherited parent feature phase) against `focus.phase` in `../../../SNAPSHOT.yaml`. If the task is ahead of the active phase, stop and request explicit user confirmation.
   - Deferral gate: transitioning to `deferred` is a **descoping operation**, not a plain status flip — run the deferral procedure below, all steps in the same turn.
3. Update `../../../SNAPSHOT.yaml`:
   - set the item status
   - update `focus` if this becomes the active item
4. Update the corresponding note frontmatter `status` and `updated`.
5. If the transition implies completion:
   - consider whether a `CHG-*` note is required
   - update related items (e.g. issue to `fixed`, feature progression)

## Requirement advancement (`approved` → `implemented`)

Requirements are advanced by the work that delivers them, not on their own schedule:

1. `draft` → `approved`: the criteria are agreed and features may now implement against them (`../feature-scaffold/SKILL.md`, "Requirement approval gate").
2. `approved` → `implemented`: set at feature close-out once **all** features in the requirement's `implements:` list are `done`, with each acceptance criterion ticked against evidence and any departed-from criterion reconciled — full procedure in `../close-out/SKILL.md`, "Requirement advancement".
3. `implemented` → `verified`: requires passing `[[test]]` notes per `../../instructions/QUALITY.md`. Never skip from `approved` straight to `verified`.

## Deferral procedure (transition to `deferred`)

`deferred` means "out of the current parent's scope, still wanted later" — it never satisfies completeness, and the validator rejects deferred items left in a scope list or parked without provenance and a home (see `../../instructions/STATUSES.md`, "Deferral and re-adoption"). All steps in one turn:

1. **Descope from the parent**: remove the item's ID from the parent's scope list (feature `tasks:`) and add it to the parent's `deferred:` list — in both the parent note and `../../../SNAPSHOT.yaml`.
2. **Record provenance**: on the deferred item, set `origin:` to the former parent link and clear `parent:`.
3. **Assign a forward home**: set `phase:` to a real future phase when one exists; otherwise use the parking lot — create `../../../docs/phases/PHASE-999-Parking-Lot.md` once if absent (status `planned`, all-9s sentinel IDs are counter-exempt) and point `phase:` at it.
4. **Keep it active**: the item stays in the snapshot (retention never prunes `deferred`) and counts toward `tasks_deferred`/`issues_deferred` metrics.

## Re-adoption (transition out of `deferred`)

1. Assign a new (or the original) `parent:` and add the ID back to that parent's scope list (note + snapshot).
2. Set the non-parked status (`backlog`/`open`/`draft`/`planned` per type) and update `phase:` to the real phase of the new work.
3. Keep `origin:` as history of where the item was first scoped.

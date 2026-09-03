---
type: skill
id: SKILL-PHASE-PLANNING
status: active
owner: group:maintainers
created: 2026-05-05
updated: 2026-09-04
tags: [skills, phases, planning]
---

# Skill: Phase planning

## When to use
- A project adopts phase-gated development.
- A new milestone needs durable scope, linked work, or exit criteria.
- Existing numeric phase values should be migrated to `PHASE-*` notes.

## Inputs
- Roadmap or milestone description.
- Existing feature, requirement, task, and issue IDs.
- `../../../SNAPSHOT.yaml`.
- `../../../docs/PHASES.md`.

## Outputs
- New or updated `../../../docs/phases/PHASE-####-Short-Name.md` notes.
- `../../../SNAPSHOT.yaml` updated (`counters.PHASE`, `items.phases`, `focus.phase` when active).
- Phase links added to related notes and snapshot items.

## Checklist
1. Decide whether a first-class phase note is needed:
   - Which form `phase:` takes is stated once in `../../../docs/PHASES.md`.
2. Allocate the next `PHASE-####` from `../../../SNAPSHOT.yaml -> counters.PHASE`.
3. Create the phase note from `../../../docs/__templates__/phase.md`.
4. Populate:
   - `order`
   - `goal`
   - scope and out-of-scope sections
   - exit criteria
   - linked `features`, `requirements`, `tasks`, and `issues`
5. Update `../../../SNAPSHOT.yaml`:
   - add `items.phases.<PHASE-####>` with `file`, `title`, `status`, `order`, `goal`, and linked item IDs
   - set `focus.phase` if this is the active milestone
   - `counters.PHASE` and `metrics.counts` are derived by the sync script (`../../instructions/LIFECYCLE.md`, "Mandatory Automated Documentation"); do not hand-write them
6. Update related notes/items:
   - set `phase: "[[PHASE-####]]"` in note frontmatter where applicable
   - set `phase: PHASE-####` in snapshot item entries
   - maintain backlinks from phase note/snapshot to the related items
7. Run `../snapshot-sync/SKILL.md` to verify phase links and metrics.

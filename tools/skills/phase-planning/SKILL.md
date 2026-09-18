---
type: skill
id: SKILL-PHASE-PLANNING
status: active
owner: group:maintainers
created: 2026-05-05
updated: 2026-09-18
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

## When a phase is too small
The document-first rule needs a focus item before code changes, and opening a phase is the cheapest way to get one. Without a limit, every request gets its own phase and `PHASES.md` becomes a log. Measured in project-os-cockpit on 2026-07-30: nine phases opened in one day, against nine in the twelve weeks before, with a median of 4 items against 21 (project-os-dev ISS-0029).

**Open a phase only when both of these hold:**
1. You can state its goal without listing its parts. "The cockpit reports on every repo it can see" passes. "Show the phase ID next to the title" does not; that describes one change.
2. Its exit criteria say something other than "the tasks are done". A phase whose criteria repeat its task list is a task list with a heading.

**Do not open one** for a single request, a single issue, or anything finished in the same session. That work gets an `ISS-*` or a task inside a **standing phase**: one known phase per lasting area of the product (an overview screen, the record itself) that small fixes join.

**A standing phase is `done` while idle and reopened when work arrives.** Leaving it permanently `active` makes it look like a phase someone forgot to close. To add work, set it back to `active`, add the item, and close it again.

**A phase that closes with three items or fewer** should probably have joined an existing phase. Check this before closing it.

**If phases were opened too small already, merge them; do not delete them:**
1. Move the unresolved children to the surviving phase first.
2. Set each absorbed phase to `superseded`, with `superseded_by:`. Its note stays as the record of that stretch of work.
3. Widen the surviving phase's goal and its `features:`/`issues:`, and add `supersedes:`.
4. Update `docs/PHASES.md` and the `phase:` entries in `SNAPSHOT.yaml`; the sync script copies statuses, not `phase`.

## Checklist
1. Decide whether a first-class phase note is needed ("When a phase is too small" above):
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

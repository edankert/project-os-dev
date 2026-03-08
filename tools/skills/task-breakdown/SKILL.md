---
type: skill
id: SKILL-TASK-BREAKDOWN
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, tasks]
---

# Skill: Task breakdown

## When to use
- You have a `FEAT-*` (and optionally `REQ-*`) but tasks are missing or too large.

## Inputs
- Feature note + requirements + any linked issues.

## Outputs
- `../../../SNAPSHOT.yaml` updated (`items.tasks`, feature `tasks` list, `focus` if applicable).
- New/updated task notes under `../../../docs/features/<slug>/plan/tasks/`.

## Checklist
1. Read the feature goal + acceptance and decide the smallest set of deliverable tasks.
2. **Inherit phase from parent feature**:
   - Check the parent feature's `phase` in `../../../SNAPSHOT.yaml` or the feature note frontmatter.
   - Tasks inherit the parent's phase by default; override only if the task belongs to a different milestone.
   - Consult `../../../docs/PHASES.md` if phase context is needed.
3. For each task:
   - allocate a `TASK-####`
   - define `title`, `status`, `phase` (inherited or explicit), `effort`, `parent`, `depends`, `blocks`
4. Update `../../../SNAPSHOT.yaml`:
   - add `items.tasks.<TASK-####>` with `phase` field
   - append the task ID to `items.features.<FEAT-####>.tasks`
5. Create each task note from `../../../docs/__templates__/task.md` with:
   - `phase` set in frontmatter (inherited from parent feature or explicit override)
   - a measurable DoD
6. If tasks expose unknowns, file an `ISS-*` rather than inflating tasks.

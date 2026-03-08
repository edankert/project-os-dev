---
type: skill
id: SKILL-BACKLOG-GROOMING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, backlog]
---

# Skill: Backlog grooming

## When to use
- The project has many `backlog` items and needs a clear `next` queue.
- Tasks are too large or ambiguous.

## Inputs
- Bases dashboards and the underlying notes; use `../../../SNAPSHOT.yaml` for canonical agent state.

## Outputs
- A prioritized `next` set and better-scoped tasks/issues.

## Checklist
1. Review tasks and identify candidates for `next`.
2. Split oversized tasks into smaller tasks with measurable DoD.
3. Convert unknowns into `ISS-*` rather than embedding them in tasks.
4. Update `focus` only when starting execution.
5. Update snapshot `metrics` after grooming.

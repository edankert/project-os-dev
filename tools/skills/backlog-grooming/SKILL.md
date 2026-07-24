---
type: skill
id: SKILL-BACKLOG-GROOMING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-07-21
tags: [skills, backlog]
---

# Skill: Backlog grooming

## When to use
- The project has many `backlog` items and needs a clear `next` queue.
- Tasks are too large or ambiguous.

## Inputs
- Bases views and the underlying notes; use `../../../SNAPSHOT.yaml` for canonical agent state.

## Outputs
- A prioritized `next` set and better-scoped tasks/issues.

## Checklist
1. Review tasks and identify candidates for `next`.
2. **Parked-item review (mandatory):** list every `deferred` item (snapshot + notes). For each, decide explicitly: re-adopt (assign a parent, add to its scope list, status back to `backlog`/`open`/`draft` per `../status-transition/SKILL.md`, "Re-adoption"), cancel (`cancelled`/`wont-fix` if no longer wanted), or keep parked with a one-line rationale in the note. Parked items are never allowed to just age out.
3. Split oversized tasks into smaller tasks with measurable DoD.
4. Convert unknowns into `ISS-*` rather than embedding them in tasks.
5. Update `focus` only when starting execution.
6. Update snapshot `metrics` after grooming (including `tasks_deferred`/`issues_deferred`).
7. Run the cross-document audit (`../docs-audit/SKILL.md`) as part of the grooming cadence — per-edit checks catch single-file drift, but stale cross-note references only surface in a full-graph sweep.

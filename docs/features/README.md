---
type: reference
id: FEATURES-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [features]
---

# `docs/features/`

Feature definitions and planning. This is where “work packages” live.

## What goes here
- One folder per feature (slugged name), containing:
  - `FEAT-####-Short-Name.md` (from `../__templates__/feature.md`)
  - `plan/PLAN.md` (the working plan)
  - `plan/tasks/TASK-####-Short-Action.md` (from `../__templates__/task.md`)
  - `plan/tests/TST-####-Short-Description.md` (feature-scoped tests; from `../__templates__/test.md`)
  
## When to add a new feature folder
- When work spans multiple tasks and needs a shared goal/scope/acceptance section.
- When you need to track progress over time and link issues/requirements/tasks together.

## When to add tasks
- Add a `TASK-*.md` when it’s actionable, has a clear DoD, and can be owned/estimated.
- Keep tasks small; file an `ISS-*` for “unknowns” rather than inflating a task.

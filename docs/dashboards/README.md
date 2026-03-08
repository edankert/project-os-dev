---
type: reference
id: DASHBOARDS-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [dashboards]
---

# `docs/dashboards/`

Navigation and status “views” over the rest of the docs.

## What goes here
- Human entrypoints that render status “views” over the docs.
- Bases are used here as a visualization layer over note frontmatter.

## Dashboards
- Tasks: `Tasks.md`
- Issues: `Issues.md`
- Features: `Features.md`
- Changes: `Changes.md`
- Requirements: `Requirements.md`
- Risks: `Risks.md`
- Tests: `Tests.md`
- Workflows: `Workflows.md`

## When to add/update dashboards
- When a new note type or section is introduced and needs an index/board.
- When workflows change and the “front door” pages should point to new entrypoints.

## Important notes
- Dashboards reflect the current state of the underlying notes.
- If a view appears “out of sync”, update the underlying note frontmatter.

## Active context
- Prefer updating `../../SNAPSHOT.yaml` and the underlying notes rather than maintaining separate “progress” pages.
- Agent source of truth: `../../SNAPSHOT.yaml` (repo root; keep it consistent with the notes).

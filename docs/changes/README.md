---
type: reference
id: CHANGES-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [changes]
---

# `docs/changes/`

Traceable records of **what changed** in the repo and **why** (after work lands).

## What goes here
- `CHG-YYYYMMDD-*.md`: one note per meaningful change, using `../__templates__/change.md`.
- Use the changes dashboard for roll-ups/views: `../dashboards/Changes.md`.

## When to add a change note
- After merging work that affects users/flows (scripts, directory layout, supported systems, environment variables).
- When changing behavior or expectations (e.g., build output location, CI behavior, tool output format).
- When a fix is significant enough that you want a stable link from issues/features to “what shipped”.

## What to include
- Links to related `ISS-*`, `FEAT-*`, `TASK-*`, and any ADRs.
- `commit:` and/or `pr:` identifiers (if available).
- “Impact” bullets that name affected flows and artifact paths.

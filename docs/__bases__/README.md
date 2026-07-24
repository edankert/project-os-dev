---
type: reference
id: BASES-README
status: active
owner: team:docs
created: 2026-01-27
updated: 2026-01-27
tags: [bases]
---

# `docs/__bases__/`

Obsidian Bases definitions (`*.base`) used for the optional navigation and context panes over notes under `docs/`.

## Important
- Bases are a **UI/view layer** only.
- Bases are for human consumption; agents/LLMs must use `../../SNAPSHOT.yaml` as canonical state.
- The LLM must keep note frontmatter consistent with the snapshot so Bases views stay accurate.

## What goes here
- `NAVIGATION.base`: left-pane navigation over features, phases, and issues.
- `CONTEXT.base`: right-pane context for notes that link to the active note.

## Linking
- Open or pin `[[NAVIGATION.base]]` for navigation.
- Open or pin `[[CONTEXT.base]]` for active-note context.

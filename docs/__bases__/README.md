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

Obsidian Bases definitions (`*.base`) used to render **tables** and **cards** views over notes under `docs/`.

## Important
- Bases are a **UI/view layer** only.
- Bases are for human consumption; agents/LLMs must use `../../SNAPSHOT.yaml` as canonical state.
- The LLM must keep note frontmatter consistent with the snapshot so Bases views stay accurate.

## What goes here
- One `*.base` file per dataset (tasks, issues, features, requirements, risks, changes, workflows).
  - Tests: `[[Tests.base]]`

## Linking
- Embed a view section: `![[Tasks.base#Active]]`
- Link to a base file: `[[Tasks.base]]`

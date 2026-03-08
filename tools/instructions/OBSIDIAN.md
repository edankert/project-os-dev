---
type: instruction
id: INSTR-OBSIDIAN
status: active
owner: group:maintainers
created: 2026-01-26
updated: 2026-01-26
tags: [instructions, obsidian]
---

# Obsidian-enabled conventions (optional)

## Linking
- Prefer Obsidian wiki links using the **filename without `.md`** (e.g. `[[TASK-0001-Foo]]`), not full paths.
- This implies filenames should be unique across the docs set; if a filename is not unique, use a path-qualified link.

## Properties
- Property keys should generally be **single names** (single token; avoid spaces). Prefer simple keys over verbose variants.
- Use **links** in properties instead of bare IDs whenever the target is another note in this docs set.
  - Example: feature `tasks:` should contain links to task notes, not raw `TASK-####` strings.

## Naming
- Filenames should include the stable ID plus a short descriptor:
  - Issues: `ISS-0001-Short-Problem.md`
  - Features: `FEAT-0001-Short-Name.md`
  - Tasks: `TASK-0001-Short-Action.md`
  - Tests: `TST-0001-Short-Description.md`
  - Changes: `CHG-YYYYMMDD-Short-Description.md`
  - Risks/Reqs/ADRs/Workflows: same pattern (`ID-Short-Description.md`)

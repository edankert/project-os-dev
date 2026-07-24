---
type: "[[task]]"
id: TASK-0040
aliases: ["TASK-0040"]
title: "Document Obsidian workspace setup for cockpit layout"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0009-Cockpit-Layout]]"
fixes: []
effort: S
due: ""
depends: ["[[TASK-0036-Create-NAV-Base]]", "[[TASK-0037-Create-CONTEXT-Base]]"]
blocks: []
related: []
tests: []
---

# Document Workspace Setup

## Definition of Done
- [ ] OBSIDIAN.md updated with "Cockpit Layout" section
- [ ] Documents how to:
  - Pin NAV.base to the left sidebar
  - Pin CONTEXT.base to the right sidebar
  - Save as an Obsidian workspace for quick switching
- [ ] Explains what each pane shows and how CONTEXT.base uses `this.file`
- [ ] Notes any known limitations (e.g., `this.file` behavior when no note is active)

## Steps
- [ ] Edit `tools/instructions/OBSIDIAN.md` in project-os repo
- [ ] Add step-by-step workspace setup instructions
- [ ] Consider providing an `.obsidian/workspaces.json` template (optional)

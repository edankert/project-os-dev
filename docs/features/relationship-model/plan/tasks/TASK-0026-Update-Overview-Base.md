---
type: "[[task]]"
id: TASK-0026
aliases: ["TASK-0026"]
title: "Update feature-overview.base template"
status: cancelled
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0007-Relationship-Model]]"
fixes: []
effort: S
due: ""
depends: ["[[TASK-0023-Update-Schemas]]"]
blocks: []
related: []
tests: []
---

# Update feature-overview.base Template

> **Cancelled**: Superseded by FEAT-0009 (Cockpit Layout). Per-feature Overview.base files replaced by a single CONTEXT.base using `this.file` in the right sidebar.

## Definition of Done (cancelled)
- [ ] Overview.base filter uses `contains` on the new named fields
- [ ] Filter covers: `implements contains`, `fixes contains`, `affects contains`, `specifies contains`, `validates contains`
- [ ] Placeholder replacement mechanism documented (FEAT-0000-PLACEHOLDER → actual feature filename)
- [ ] Tested: confirm Bases `contains` operator works on list properties

## Steps
- [ ] Edit `docs/__templates__/feature-overview.base` in project-os repo
- [ ] Update filter from `parent ==` to `implements contains` / `affects contains` / etc.
- [ ] Test in Obsidian with sample notes

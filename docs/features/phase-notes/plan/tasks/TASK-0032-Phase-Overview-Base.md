---
type: "[[task]]"
id: TASK-0032
aliases: ["TASK-0032"]
title: "Create phase-overview.base contextual dashboard template"
status: cancelled
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0008-Phase-Notes]]"
fixes: []
effort: S
due: ""
depends: ["[[TASK-0030-Phase-Template]]"]
blocks: []
related: ["[[TASK-0026-Update-Overview-Base]]"]
tests: []
---

# Create Phase Overview Base Template

> **Cancelled**: Superseded by FEAT-0009 (Cockpit Layout). Per-phase overview bases replaced by a single CONTEXT.base using `this.file` in the right sidebar.

## Definition of Done (cancelled)
- [ ] `docs/__templates__/phase-overview.base` created
- [ ] Filters items where `phase contains "[[PHASE-###-PLACEHOLDER]]"`
- [ ] Covers all types: features, tasks, issues, requirements, tests, risks
- [ ] Views: All (grouped by type), Features, Tasks, Issues
- [ ] Placeholder replacement mechanism documented (same pattern as feature-overview.base)

## Steps
- [ ] Create `docs/__templates__/phase-overview.base` in project-os repo
- [ ] Uses `contains` operator on `phase` list/link field
- [ ] Document placeholder replacement in feature-scaffold/phase-scaffold skill

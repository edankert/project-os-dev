---
type: "[[task]]"
id: TASK-0031
aliases: ["TASK-0031"]
title: "Create Phases.base top-level dashboard"
status: done
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
related: []
tests: []
---

# Create Phases.base Dashboard

## Definition of Done
- [ ] `docs/__bases__/Phases.base` created
- [ ] Filter: `type == "[[phase]]"`
- [ ] Properties: display_title, status, order, goal
- [ ] Views:
  - Table: All (sorted by order ASC)
  - Table: Active (filter `status == "active"`)
  - Board: grouped by status

## Steps
- [ ] Create `docs/__bases__/Phases.base` in project-os repo
- [ ] Add `![[Phases.base]]` to `docs/DASHBOARD.md`

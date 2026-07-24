---
type: "[[task]]"
id: TASK-0030
aliases: ["TASK-0030"]
title: "Create phase note template and schema"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0008-Phase-Notes]]"
fixes: []
effort: S
due: ""
depends: []
blocks: ["[[TASK-0031-Phase-Base-Dashboard]]", "[[TASK-0032-Phase-Overview-Base]]", "[[TASK-0033-Migrate-Phase-Field]]"]
related: []
tests: []
---

# Create Phase Template and Schema

## Definition of Done
- [ ] `docs/__templates__/phase.md` created with frontmatter:
  - `type: "[[phase]]"`
  - `id: PHASE-000`
  - `title: ""`
  - `status: draft` (allowed: draft, active, completed)
  - `order: 0` (integer, controls sort order)
  - `goal: ""` (what this phase delivers)
  - Standard common fields (owner, created, updated, related)
- [ ] SCHEMAS.md updated with `phase.md` section documenting all fields
- [ ] Phase naming convention: `PHASE-###-Short-Name.md`
- [ ] Phase notes stored under `docs/phases/`
- [ ] Phase template body includes embedded `![[Overview.base]]`

## Steps
- [ ] Create `docs/__templates__/phase.md` in project-os repo
- [ ] Add `phase.md` section to `docs/__templates__/SCHEMAS.md`
- [ ] Add `PHASE` counter to template SNAPSHOT.yaml

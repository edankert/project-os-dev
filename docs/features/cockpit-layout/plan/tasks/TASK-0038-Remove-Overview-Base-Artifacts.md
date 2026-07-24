---
type: "[[task]]"
id: TASK-0038
aliases: ["TASK-0038"]
title: "Remove feature-overview.base template and per-feature Overview.base generation"
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
depends: ["[[TASK-0037-Create-CONTEXT-Base]]"]
blocks: []
related: []
tests: []
---

# Remove Overview Base Artifacts

## Definition of Done
- [ ] `docs/__templates__/feature-overview.base` deleted from project-os repo
- [ ] `![[Overview.base]]` embed removed from `docs/__templates__/feature.md`
- [ ] Feature-scaffold skill (`tools/skills/feature-scaffold/SKILL.md`) no longer generates Overview.base per feature
- [ ] Feature-scaffold skill outputs section no longer lists Overview.base
- [ ] TASK-0026 and TASK-0032 notes updated with `status: cancelled` (superseded by cockpit layout)

## Steps
- [ ] Delete `docs/__templates__/feature-overview.base`
- [ ] Edit `docs/__templates__/feature.md` — remove Overview.base embed
- [ ] Edit `tools/skills/feature-scaffold/SKILL.md` — remove Overview.base references
- [ ] Update TASK-0026 and TASK-0032 status to cancelled
- [ ] Sync to downstream repos

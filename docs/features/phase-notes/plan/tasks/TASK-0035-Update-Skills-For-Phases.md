---
type: "[[task]]"
id: TASK-0035
aliases: ["TASK-0035"]
title: "Update skills to create and reference phase notes"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0008-Phase-Notes]]"
fixes: []
effort: M
due: ""
depends: ["[[TASK-0033-Migrate-Phase-Field]]"]
blocks: []
related: []
tests: []
---

# Update Skills for Phase Notes

## Definition of Done
- [ ] feature-scaffold: assigns `phase` as link to phase note, consults phase notes instead of PHASES.md
- [ ] task-breakdown: inherits `phase` link from parent feature
- [ ] status-transition: phase alignment gate references phase note status
- [ ] project-init: optionally creates initial phase notes under `docs/phases/`
- [ ] New skill or skill step: create phase notes (could be part of project-init or a standalone phase-scaffold)
- [ ] Remove references to `docs/PHASES.md` as the phase registry

## Steps
- [ ] Edit `tools/skills/feature-scaffold/SKILL.md`
- [ ] Edit `tools/skills/task-breakdown/SKILL.md`
- [ ] Edit `tools/skills/status-transition/SKILL.md`
- [ ] Edit `tools/skills/project-init/SKILL.md`
- [ ] Consider adding `tools/skills/phase-scaffold/SKILL.md`

---
type: "[[task]]"
id: TASK-0033
aliases: ["TASK-0033"]
title: "Change phase field from integer to link across all templates"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0008-Phase-Notes]]"
fixes: []
effort: M
due: ""
depends: ["[[TASK-0030-Phase-Template]]"]
blocks: ["[[TASK-0034-Update-Lifecycle-Instructions]]"]
related: []
tests: []
---

# Migrate Phase Field to Link

## Definition of Done
- [ ] `phase` field in all templates changed from `phase:` (integer) to `phase: []` (list of links)
- [ ] Templates affected: feature.md, task.md, issue.md, requirement.md, test.md, risk.md
- [ ] SCHEMAS.md common fields section updated: `phase` is now `(optional, list of links)` instead of `(optional, integer 1-N)`
- [ ] All .base dashboards that group/sort by phase updated to work with link values
- [ ] `docs/PHASES.md` registry file marked as deprecated or replaced

## Steps
- [ ] Update each template's frontmatter in `docs/__templates__/`
- [ ] Update SCHEMAS.md common fields section
- [ ] Update .base files that reference `phase` property
- [ ] Add migration note for downstream repos

## Notes
- This is a breaking change for downstream repos with existing phase integers
- Downstream migration: create phase notes, then find-replace `phase: 1` → `phase: ["[[PHASE-001-...]]"]`

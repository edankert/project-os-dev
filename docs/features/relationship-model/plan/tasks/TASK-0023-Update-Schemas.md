---
type: "[[task]]"
id: TASK-0023
aliases: ["TASK-0023"]
title: "Update SCHEMAS.md with new relationship fields"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0007-Relationship-Model]]"
fixes: []
effort: S
due: ""
depends: []
blocks: ["[[TASK-0024-Update-Templates]]"]
related: []
tests: []
---

# Update SCHEMAS.md

## Definition of Done
- [ ] Task: `parent` replaced by `implements` (list) and `fixes` (list)
- [ ] Issue: `parent` replaced by `affects` (list)
- [ ] Requirement: `implements` renamed to `specifies` (list, direction corrected)
- [ ] Test: `features`/`issues`/`tasks` consolidated into `validates` (list)
- [ ] Feature: `requirements`, `tasks`, `tests` lists removed; `goal` and `release` kept
- [ ] All new fields documented as (optional, list of links) with clear semantics
- [ ] Old field names noted as deprecated

## Steps
- [ ] Edit `docs/__templates__/SCHEMAS.md` in project-os repo
- [ ] Update task.md section
- [ ] Update issue.md section
- [ ] Update requirement.md section
- [ ] Update test.md section
- [ ] Update feature.md section

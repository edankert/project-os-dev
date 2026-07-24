---
type: "[[task]]"
id: TASK-0025
aliases: ["TASK-0025"]
title: "Update TRACEABILITY.md link rules"
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
depends: ["[[TASK-0023-Update-Schemas]]"]
blocks: []
related: []
tests: []
---

# Update TRACEABILITY.md

## Definition of Done
- [ ] Task link rule: must have at least one of `implements` or `fixes`
- [ ] Issue link rule: should have `affects` when related to a feature
- [ ] Requirement link rule: must have `specifies` linking to feature(s)
- [ ] Test link rule: must have `validates` linking to what it verifies
- [ ] Feature link rule: no longer requires `tasks`/`requirements`/`tests` lists (children link up)
- [ ] Snapshot alignment section reflects new field names

## Steps
- [ ] Edit `tools/instructions/TRACEABILITY.md` in project-os repo

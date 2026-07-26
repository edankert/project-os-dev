---
type: "[[task]]"
id: TASK-0027
aliases: ["TASK-0027"]
title: "Update top-level .base dashboards"
status: done
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
depends: ["[[TASK-0024-Update-Templates]]"]
blocks: []
related: []
tests: []
---

# Update Top-Level Bases Dashboards

## Definition of Done
- [ ] Tasks.base: replace `parent` column with `implements` and `fixes`
- [ ] Issues.base: add `affects` column
- [ ] Requirements.base: replace any `implements` references with `specifies`
- [ ] Tests.base: add `validates` column
- [ ] Features.base: no `tasks`/`requirements`/`tests` columns needed

## Steps
- [ ] Edit each `.base` file in `docs/__bases__/` in project-os repo

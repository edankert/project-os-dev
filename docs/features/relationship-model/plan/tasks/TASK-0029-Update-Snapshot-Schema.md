---
type: "[[task]]"
id: TASK-0029
aliases: ["TASK-0029"]
title: "Update SNAPSHOT.md schema and migrate existing entries"
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
depends: ["[[TASK-0025-Update-Traceability]]"]
blocks: []
related: []
tests: []
---

# Update SNAPSHOT.md Schema

## Definition of Done
- [ ] SNAPSHOT.md documents new field names for task items (`implements`, `fixes` instead of `parent`)
- [ ] SNAPSHOT.md documents `specifies` for requirement items (replaces `implements`)
- [ ] SNAPSHOT.md documents `validates` for test items
- [ ] SNAPSHOT.md documents that feature items no longer carry `tasks`/`requirements`/`tests` lists
- [ ] Existing entries in project-os-dev SNAPSHOT.yaml migrated (requirements: `implements` → `specifies`)
- [ ] Template SNAPSHOT.yaml in project-os updated

## Steps
- [ ] Edit `tools/instructions/SNAPSHOT.md` in project-os repo
- [ ] Edit `SNAPSHOT.yaml` in project-os-dev repo (rename requirement `implements` to `specifies`)
- [ ] Edit template `SNAPSHOT.yaml` in project-os repo

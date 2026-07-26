---
type: "[[task]]"
id: TASK-0024
aliases: ["TASK-0024"]
title: "Update note templates with new relationship fields"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0007-Relationship-Model]]"
effort: S
due: ""
depends: ["[[TASK-0023-Update-Schemas]]"]
blocks: []
related: []
tests: []
---

# Update Note Templates

## Definition of Done
- [ ] `task.md`: `parent` replaced by `implements: []` and `fixes: []`
- [ ] `issue.md`: `parent` replaced by `affects: []`
- [ ] `requirement.md`: `implements` renamed to `specifies: []`
- [ ] `test.md`: `features`/`issues`/`tasks` replaced by `validates: []`
- [ ] `feature.md`: `requirements`, `tasks`, `tests` lists removed
- [ ] All templates have correct default values (empty lists)

## Steps
- [ ] Edit each template file in `docs/__templates__/` in project-os repo
- [ ] Verify frontmatter YAML is valid

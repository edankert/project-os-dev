---
type: "[[task]]"
id: TASK-0028
aliases: ["TASK-0028"]
title: "Update skills that create or link notes"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0007-Relationship-Model]]"
fixes: []
effort: M
due: ""
depends: ["[[TASK-0024-Update-Templates]]"]
blocks: []
related: []
tests: []
---

# Update Skills

## Definition of Done
- [ ] feature-scaffold: generates tasks with `implements` instead of `parent`, generates Overview.base with new filters, no longer populates `tasks`/`requirements`/`tests` on feature note
- [ ] issue-intake: creates issues with `affects` instead of `parent`
- [ ] task-breakdown: creates tasks with `implements`/`fixes` instead of `parent`
- [ ] test-authoring: creates tests with `validates` instead of `features`/`issues`/`tasks`
- [ ] close-out: checks new field names during close-out verification
- [ ] snapshot-sync: recognizes new field names

## Steps
- [ ] Edit each SKILL.md in `tools/skills/` in project-os repo
- [ ] Verify checklist steps reference correct field names

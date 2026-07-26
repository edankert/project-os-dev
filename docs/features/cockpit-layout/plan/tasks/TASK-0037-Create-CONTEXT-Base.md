---
type: "[[task]]"
id: TASK-0037
aliases: ["TASK-0037"]
title: "Create CONTEXT.base for right sidebar dynamic context"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0009-Cockpit-Layout]]"
fixes: []
effort: M
due: ""
depends: []
blocks: []
related: []
tests: []
---

# Create CONTEXT.base

## Definition of Done
- [ ] `docs/CONTEXT.base` created in project-os template repo
- [ ] Filter uses `this.file` to match against relationship fields:
  - `implements contains this.file`
  - `fixes contains this.file`
  - `affects contains this.file`
  - `specifies contains this.file`
  - `validates contains this.file`
  - `phase contains this.file`
- [ ] Views:
  - All: table showing display_title, type, status — sorted by type then status
  - Tasks: filtered to `type == "[[task]]"`, showing display_title, status, due
  - Requirements: filtered to `type == "[[requirement]]"`, showing display_title, status, priority
  - Issues: filtered to `type == "[[issue]]"`, showing display_title, status, severity
  - Tests: filtered to `type == "[[test]]"`, showing display_title, status, last_run
- [ ] Right sidebar updates dynamically when switching notes in center editor
- [ ] Verified: `this.file` resolves to the active editor pane when base is pinned in sidebar

## Steps
- [ ] Create `docs/CONTEXT.base` in project-os repo
- [ ] Test `this.file` behavior when base is pinned in right sidebar
- [ ] Verify dynamic update on note switch
- [ ] Sync to downstream repos

## Notes
- Critical validation: confirm `this.file` in a pinned sidebar base references the active editor note, not the base file itself. If not, investigate alternative approaches.

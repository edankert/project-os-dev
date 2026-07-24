---
type: "[[task]]"
id: TASK-0036
aliases: ["TASK-0036"]
title: "Create NAV.base for left sidebar navigation"
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
depends: []
blocks: []
related: []
tests: []
---

# Create NAV.base

## Definition of Done
- [ ] `docs/NAV.base` created in project-os template repo
- [ ] Filter: features, phases, and issues (excludes templates, trash)
- [ ] Views:
  - Features: table showing display_title, status, phase — filtered to `type == "[[feature]]"`, sorted by phase ASC
  - Phases: table showing display_title, status, order — filtered to `type == "[[phase]]"`, sorted by order ASC
  - Issues: table showing display_title, severity, status — filtered to active issues, sorted by severity DESC
- [ ] Clicking a row opens the note in the center editor

## Steps
- [ ] Create `docs/NAV.base` in project-os repo
- [ ] Verify tabbed views work in Obsidian
- [ ] Sync to downstream repos

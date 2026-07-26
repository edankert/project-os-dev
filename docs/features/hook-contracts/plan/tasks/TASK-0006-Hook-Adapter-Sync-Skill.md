---
type: "[[task]]"
id: TASK-0006
aliases: ["TASK-0006"]
title: "Create adapter-sync skill for regenerating tool-specific files"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0002-Hook-Contracts]]"
fixes: []
effort: S
due: ""
depends: [TASK-0002, TASK-0004]
blocks: []
related: ["[[FEAT-0001-Tool-Adapters]]"]
tests: []
---

# Create adapter-sync skill for regenerating tool-specific files

## Definition of Done
- [x] `tools/skills/adapter-sync/SKILL.md` exists
- [x] Skill describes when and how to regenerate tool-specific files from adapters
- [x] Covers: CLAUDE.md regeneration, hooks.json updates, .cursor/rules/ regeneration
- [x] Referenced from skills README

## Steps
- [x] Write SKILL.md with checklist for each adapter type
- [x] Add to skills README index

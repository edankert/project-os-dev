---
type: "[[task]]"
id: TASK-0002
aliases: ["TASK-0002"]
title: "Create Claude Code adapter with CLAUDE.md import strategy"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0001-Tool-Adapters]]"
fixes: []
effort: M
due: ""
depends: [TASK-0001]
blocks: [TASK-0005]
related: []
tests: []
---

# Create Claude Code adapter with CLAUDE.md import strategy

## Definition of Done
- [x] `tools/adapters/claude-code/ADAPTER.md` documents the Claude Code adapter
- [x] A reference CLAUDE.md is provided showing how to @import project-os instruction files
- [x] The adapter documents which instruction files to import and in what order
- [x] CONTEXT.md import is noted as optional (for users who also want the generic fallback)

## Steps
- [x] Document Claude Code's @import syntax and how it maps to tools/instructions/
- [x] Create a reference CLAUDE.md with @import lines for all project-os instruction files
- [x] Document any Claude Code-specific considerations (200-line CLAUDE.md limit, .claude/rules/ for overflow)

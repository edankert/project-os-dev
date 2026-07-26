---
type: "[[feature]]"
id: FEAT-0001
aliases: ["FEAT-0001"]
title: "Tool-specific adapter layer"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
goal: "Replace monolithic CONTEXT.md with tool-specific adapters that deliver project-os rules via each tool's native instruction format"
release: ""
related: ["[[ADR-0001-Tool-Adapter-Architecture]]"]
---

# Tool-specific adapter layer

## Goal
Replace the monolithic CONTEXT.md delivery mechanism with a tool-specific adapter layer. Rules remain in `tools/instructions/` (single source of truth) and are delivered to each LLM tool via its native instruction format.

## Scope
**In scope:**
- Adapter directory structure (`tools/adapters/<tool>/`)
- Claude Code adapter (CLAUDE.md with @import)
- Codex adapter stub (AGENTS.md)
- Cursor adapter stub (.cursor/rules/*.mdc)
- Generic fallback (CONTEXT.md)
- Adapter-sync skill for regenerating tool-specific files

**Out of scope:**
- Adapters for tools not yet assessed (Cline, Windsurf, Kiro)
- Automated detection of which tool is being used

## Acceptance
- Rules authored once in `tools/instructions/`, delivered to any tool via adapter
- Changing a rule does not require manual updates to tool-specific files
- Claude Code adapter uses `@import` references
- Generic fallback works for unsupported tools

## Links
- Requirements: [[REQ-0001-Tool-Agnostic-Rules]], [[REQ-0002-Native-Instruction-Format]]
- Tasks: [[TASK-0001-Adapter-Directory-Structure]], [[TASK-0002-Claude-Code-Adapter]], [[TASK-0003-Codex-Cursor-Adapters]]
- Decision: [[ADR-0001-Tool-Adapter-Architecture]]

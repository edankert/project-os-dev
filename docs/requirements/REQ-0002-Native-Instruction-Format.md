---
type: "[[requirement]]"
id: REQ-0002
title: "Adapters must deliver rules in each tool's native instruction format"
status: approved
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
priority: high
scope: "adapters"
acceptance:
  - "Claude Code adapter produces CLAUDE.md with @import references to tools/instructions/ files"
  - "Codex adapter produces AGENTS.md with equivalent content"
  - "Cursor adapter produces .cursor/rules/*.mdc files with appropriate glob scoping"
  - "A generic fallback uses CONTEXT.md directly for unsupported tools"
implements: ["[[FEAT-0001-Tool-Adapters]]"]
verifies: []
related: ["[[REQ-0001-Tool-Agnostic-Rules]]"]
tests: []
---

# Adapters must deliver rules in each tool's native instruction format

## Statement
Each tool adapter MUST produce instruction files in the target tool's native format, using that tool's mechanisms for loading and scoping.

## Acceptance Criteria
- Claude Code adapter produces `CLAUDE.md` with `@import` references to `tools/instructions/` files
- Codex adapter produces `AGENTS.md` with equivalent content
- Cursor adapter produces `.cursor/rules/*.mdc` files with appropriate glob scoping
- A generic fallback uses `CONTEXT.md` directly for unsupported tools

## Traceability
- Implements: [[FEAT-0001-Tool-Adapters]]
- Decided by: [[ADR-0001-Tool-Adapter-Architecture]]

---
type: adapter
tool: generic
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-03-08
---

# Generic Adapter (CONTEXT.md Fallback)

## Overview

The generic adapter uses `CONTEXT.md` as a single entry point that works with any LLM tool. It provides the project-os contract, edit policy, invariants, and the operating rule in one file. Tools that support file reading can follow paths to instruction and skill files from CONTEXT.md.

## Native instruction format

- **File**: `CONTEXT.md` (repo root)
- **Syntax**: Standard Markdown
- **Import**: None — the file is self-contained with references to other files via relative paths

## When to use

Use the generic adapter when:
- The LLM tool does not have a native instruction format
- You want a single-file entry point for any tool
- The tool supports reading referenced files on demand

## Relationship to tool-specific adapters

`CONTEXT.md` is always present in a project-os repo. Tool-specific adapters (Claude Code, Codex, Cursor) are optional additions that deliver the same rules via native formats. If a tool-specific adapter exists, prefer it over the generic fallback.

## Hook support

None — the generic adapter relies on instruction-based rules only. For enforcement, use a tool-specific adapter that supports hooks.

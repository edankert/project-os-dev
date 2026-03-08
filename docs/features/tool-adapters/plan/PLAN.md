# Plan: Tool-specific adapter layer

## Sequence
1. TASK-0001: Create the adapter directory structure and ADAPTER.md template
2. TASK-0002: Create the Claude Code adapter (highest priority — primary tool)
3. TASK-0003: Create Codex and Cursor adapter stubs (lower priority — templates for future use)

## Approach
- CONTEXT.md is retained as the generic fallback but is no longer the primary delivery mechanism for tools with adapters
- Claude Code adapter uses `@import` syntax to reference `tools/instructions/` files from the project's CLAUDE.md
- Codex and Cursor adapters are stubs with documentation on how to complete them when those tools are actively used

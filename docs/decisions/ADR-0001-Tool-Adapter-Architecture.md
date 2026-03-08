---
type: "[[adr]]"
id: ADR-0001
title: "Use tool-specific adapters instead of a monolithic CONTEXT.md"
status: accepted
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
decision: "Deliver project-os rules via tool-specific adapters rather than a single CONTEXT.md"
context: "Every LLM tool has its own instruction format (CLAUDE.md, AGENTS.md, .cursorrules). CONTEXT.md duplicates this and creates a maintenance burden."
alternatives:
  - "Keep CONTEXT.md as the sole delivery mechanism (status quo)"
  - "Abandon CONTEXT.md entirely and maintain separate tool-specific files manually"
  - "Use CONTEXT.md as the canonical source and generate tool-specific files via adapters"
consequences:
  - "Rules are authored once in tools/instructions/ and delivered to any tool via its native format"
  - "New adapter required for each supported tool"
  - "CONTEXT.md remains as the tool-agnostic fallback for unsupported tools"
  - "Teams using mixed tools (Claude Code + Cursor) all read the same rules"
supersedes: ""
superseded: ""
related: ["[[FEAT-0001-Tool-Adapters]]", "[[REQ-0001-Tool-Agnostic-Rules]]", "[[REQ-0002-Native-Instruction-Format]]"]
---

# Use tool-specific adapters instead of a monolithic CONTEXT.md

## Context
Every LLM coding tool has converged on a "markdown file in the repo" pattern for persistent instructions: Claude Code uses `CLAUDE.md`, OpenAI Codex uses `AGENTS.md`, Cursor uses `.cursor/rules/*.mdc`, Cline uses `.clinerules`. project-os currently uses `CONTEXT.md` as its operating contract, which is effectively a duplicate of whatever tool-specific file the user already maintains. This creates redundancy and risks the two files drifting apart.

## Decision
Adopt an adapter architecture:
- `tools/instructions/` remains the **canonical source** for all project-os rules
- `tools/adapters/<tool>/ADAPTER.md` describes how to map rules into each tool's native format
- For Claude Code: the project's `CLAUDE.md` uses `@import` references to pull in project-os instruction files
- For Codex: `AGENTS.md` includes equivalent references
- For Cursor: `.cursor/rules/*.mdc` files are generated with appropriate glob scoping
- `CONTEXT.md` remains as the generic fallback for tools without a specific adapter

## Alternatives
- **Status quo**: Keep CONTEXT.md as the sole delivery mechanism. Rejected because it duplicates the tool-specific file and requires users to read two files.
- **Manual tool-specific files**: Maintain separate CLAUDE.md, AGENTS.md, etc. manually. Rejected because rule changes require N manual updates.

## Consequences
- Single source of truth for rules (tools/instructions/)
- Teams using mixed tools get consistent rules automatically
- New tools require a new adapter (low effort)
- CONTEXT.md is retained but deprioritised for tools with adapters

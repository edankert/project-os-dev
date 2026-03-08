---
type: "[[task]]"
id: TASK-0001
title: "Create adapter directory structure and ADAPTER.md template"
status: done
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0001-Tool-Adapters]]"
effort: S
due: ""
depends: []
blocks: [TASK-0002, TASK-0003]
related: []
tests: []
---

# Create adapter directory structure and ADAPTER.md template

## Definition of Done
- [x] `tools/adapters/` directory exists with subdirectories for claude-code, codex, cursor, generic
- [x] ADAPTER.md template defines the expected structure of an adapter
- [x] README in tools/adapters/ explains the adapter concept

## Steps
- [x] Create directory structure
- [x] Write ADAPTER.md template with fields: tool name, instruction file format, import mechanism, hook support
- [x] Write README.md for tools/adapters/

---
type: "[[feature]]"
id: FEAT-0002
title: "Hook contract definitions and tool-specific implementations"
status: done
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
goal: "Define enforceable hook contracts in project-os and provide tool-specific implementations that turn prescriptive skills into deterministic gates"
requirements: ["[[REQ-0003-Hook-Contracts]]", "[[REQ-0004-Tool-Specific-Hook-Implementations]]"]
tasks: ["[[TASK-0004-Hook-Contracts-Spec]]", "[[TASK-0005-Claude-Code-Hooks]]", "[[TASK-0006-Hook-Adapter-Sync-Skill]]"]
release: ""
related: ["[[ADR-0002-Hook-Contract-Pattern]]", "[[FEAT-0001-Tool-Adapters]]"]
tests: []
---

# Hook contract definitions and tool-specific implementations

## Goal
Bridge the gap between prescriptive skills (checklists agents should follow) and deterministic enforcement (hooks that block non-compliant actions). Define what should be enforced in a tool-agnostic spec, then implement enforcement for each supported tool.

## Scope
**In scope:**
- HOOKS.md with tool-agnostic hook contract definitions
- Claude Code hooks.json and shell scripts implementing each contract
- Contracts for: verification gating, risk scan triggers, phase alignment, snapshot freshness, document-first rule
- Adapter-sync skill update to include hook regeneration

**Out of scope:**
- Hook implementations for Codex, Cursor, Kiro (stubs only until those tools support hooks)
- Custom hook authoring by consuming projects (future feature)

## Acceptance
- HOOKS.md defines each enforcement point with trigger, check, and failure behaviour
- Claude Code adapter includes working hooks.json and scripts
- Skills remain as fallback for tools without hook support

## Links
- Requirements: [[REQ-0003-Hook-Contracts]], [[REQ-0004-Tool-Specific-Hook-Implementations]]
- Tasks: [[TASK-0004-Hook-Contracts-Spec]], [[TASK-0005-Claude-Code-Hooks]], [[TASK-0006-Hook-Adapter-Sync-Skill]]
- Decision: [[ADR-0002-Hook-Contract-Pattern]]

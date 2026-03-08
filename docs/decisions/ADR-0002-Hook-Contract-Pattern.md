---
type: "[[adr]]"
id: ADR-0002
title: "Define hook contracts as tool-agnostic specs with tool-specific implementations"
status: accepted
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
decision: "Separate hook contract definitions (what to enforce) from implementations (how to enforce) using an adapter pattern"
context: "project-os skills are prescriptive checklists with no enforcement. Claude Code hooks can deterministically enforce rules but are tool-specific."
alternatives:
  - "Keep enforcement purely prescriptive (skills only)"
  - "Write Claude Code hooks directly without abstraction"
  - "Define tool-agnostic contracts with tool-specific implementations"
consequences:
  - "HOOKS.md becomes the reference for what should be enforced"
  - "Each adapter provides runnable hook implementations"
  - "Skills remain as the fallback for tools without hook support"
  - "Adding enforcement for a new tool means implementing hook scripts, not redesigning contracts"
supersedes: ""
superseded: ""
related: ["[[FEAT-0002-Hook-Contracts]]", "[[REQ-0003-Hook-Contracts]]", "[[REQ-0004-Tool-Specific-Hook-Implementations]]"]
---

# Define hook contracts as tool-agnostic specs with tool-specific implementations

## Context
project-os skills define what agents should do (checklists), but cannot enforce compliance. An agent can ignore a checklist step and proceed. Claude Code provides deterministic hooks (`PreToolUse`, `PostToolUse`, `SessionStart`, etc.) that can block actions, but these are Claude Code-specific. Other tools (Codex, Cursor, Kiro) have or will have their own hook mechanisms.

The gap: project-os needs enforcement, but enforcement mechanisms are tool-specific.

## Decision
Separate the contract from the implementation:
- `tools/instructions/HOOKS.md` defines **hook contracts** — tool-agnostic specifications of what should be enforced, when, and what happens on failure
- Each `tools/adapters/<tool>/` directory contains the runnable implementation (e.g., `hooks.json` and shell scripts for Claude Code)
- Skills remain as the prescriptive layer for tools without hook support
- Hook contracts reference the project-os rule they enforce (traceability)

## Alternatives
- **Prescriptive only**: Rely entirely on LLM compliance with skill checklists. Rejected because LLMs can and do skip steps.
- **Claude Code hooks directly**: Write hooks.json without abstraction. Rejected because it locks enforcement to one tool and mixes the "what" with the "how."

## Consequences
- Enforcement becomes portable across tools (as tools add hook support)
- Clear separation of concerns: contracts define policy, adapters implement mechanism
- Skills and hooks complement each other — skills guide, hooks enforce
- Initial implementation effort focused on Claude Code (highest-value adapter)

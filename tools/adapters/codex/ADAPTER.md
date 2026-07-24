---
type: adapter
tool: codex
status: active
owner: group:maintainers
created: 2026-03-08
updated: 2026-05-05
---

# Codex adapter

## Overview

Codex reads project instructions from `AGENTS.md` in the repository root. It can also read referenced files on demand, but `AGENTS.md` should remain self-contained enough to define the startup contract, docs-first gate, canonical state file, and close-out expectations.

## Native instruction files

- `AGENTS.md`: mandatory startup contract and docs-first gate.
- `LLM_BRIEF.md`: compact project identity, important paths, and common commands.
- `CONTEXT.md`: tool-agnostic project-os contract.
- `SNAPSHOT.yaml`: canonical machine-readable work state.

## Codex hook equivalents

Codex does not require a checked-in native hook configuration for this template. Use these repository scripts as Codex-compatible enforcement points:

| Contract | Entrypoint | Purpose |
|---|---|---|
| Startup preflight | `bash tools/agents/bootstrap.sh` | Verify required files, snapshot focus, branch, and basic tooling. |
| Docs-first intake | `bash tools/agents/start-change.sh "<short title>"` | Scaffold a change note when downstream projects require docs-first change records. |
| Docs-first validation | `bash tools/agents/check-docs-first.sh` | Check that code changes have documentation coverage and snapshot updates. |

See `tools/instructions/HOOKS.md` for the Codex hook-equivalent contracts.

## Synchronizing the adapter

Run `tools/skills/adapter-sync/SKILL.md` when shared lifecycle, status, quality, snapshot, or skill rules change. The sync should update Codex-facing guidance without introducing tool-specific files for unsupported agents.

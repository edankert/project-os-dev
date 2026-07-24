---
type: "[[requirement]]"
id: REQ-0001
aliases: ["REQ-0001"]
title: "project-os rules must be maintainable in one place and deliverable to any LLM tool"
status: implemented
phase: []
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-07-21
source: []
priority: high
scope: "adapters"
acceptance:
  - "Rules are authored once in tools/instructions/"
  - "Each supported tool has an adapter that maps rules to its native format"
  - "Changing a rule in tools/instructions/ does not require manual updates to tool-specific files"
implements: ["[[FEAT-0001-Tool-Adapters]]"]
verifies: []
related: ["[[REQ-0002-Native-Instruction-Format]]"]
tests: []
---

# project-os rules must be maintainable in one place and deliverable to any LLM tool

## Statement
project-os rules (lifecycle, traceability, quality, statuses, etc.) MUST be authored and maintained in a single canonical location (`tools/instructions/`) and MUST be deliverable to any supported LLM tool without duplication or manual synchronisation.

## Acceptance Criteria

- [x] Rules are authored once in `tools/instructions/` — evidence: 16 canonical instruction files there; `tools/adapters/README.md` "The rules themselves stay tool-agnostic in `../instructions/` and `../skills/`; adapters only deliver them."
- [x] Each supported tool has an adapter — evidence: `tools/adapters/{claude-code,codex,cursor,generic}/ADAPTER.md`.
- [x] Changing a rule in `tools/instructions/` requires no manual tool-file edits — evidence: `tools/scripts/generate-adapters.py` regenerates `.cursor/rules/*.mdc`, `.claude/skills/*/SKILL.md` and `.claude/agents/`; staleness is gated by `--check` at `tools/scripts/hooks/pre-commit` and `.github/workflows/validate-docs.yml`. Caveat (scope note, not a failure): *adding a new* instruction file still needs a manual entry in `CLAUDE.md` and in the generator's `CURSOR_RULES` map — the criterion covers changing a rule, not extending the rule set.

## Traceability
- Implements: [[FEAT-0001-Tool-Adapters]]
- Decided by: [[ADR-0001-Tool-Adapter-Architecture]]

---
type: "[[requirement]]"
id: REQ-0001
title: "project-os rules must be maintainable in one place and deliverable to any LLM tool"
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
- Rules are authored once in `tools/instructions/`
- Each supported tool has an adapter that maps rules to its native format
- Changing a rule in `tools/instructions/` does not require manual updates to tool-specific files

## Traceability
- Implements: [[FEAT-0001-Tool-Adapters]]
- Decided by: [[ADR-0001-Tool-Adapter-Architecture]]

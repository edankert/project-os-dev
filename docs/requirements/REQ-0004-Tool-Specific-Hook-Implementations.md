---
type: "[[requirement]]"
id: REQ-0004
title: "Hook contracts must have runnable implementations for supported tools"
status: approved
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
priority: medium
scope: "hooks"
acceptance:
  - "Claude Code adapter includes hooks.json and executable scripts for each contract"
  - "Scripts exit non-zero to block or return warnings via stdout"
  - "Hook implementations are documented with expected inputs and outputs"
implements: ["[[FEAT-0002-Hook-Contracts]]"]
verifies: []
related: ["[[REQ-0003-Hook-Contracts]]"]
tests: []
---

# Hook contracts must have runnable implementations for supported tools

## Statement
Each hook contract defined in `HOOKS.md` SHOULD have a runnable implementation in supported tool adapters, starting with Claude Code.

## Acceptance Criteria
- Claude Code adapter includes `hooks.json` and executable scripts for each contract
- Scripts exit non-zero to block or return warnings via stdout
- Hook implementations are documented with expected inputs and outputs

## Traceability
- Implements: [[FEAT-0002-Hook-Contracts]]
- Decided by: [[ADR-0002-Hook-Contract-Pattern]]

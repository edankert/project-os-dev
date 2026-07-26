---
type: "[[requirement]]"
id: REQ-0004
aliases: ["REQ-0004"]
title: "Hook contracts must have runnable implementations for supported tools"
status: implemented
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-07-21
source: []
priority: medium
scope: "hooks"
acceptance:
  - "Claude Code adapter includes hooks.json and executable scripts for each contract"
  - "Scripts signal block decisions on stdout in the tool native protocol (Claude Code: JSON permissionDecision deny / decision block with exit 0) and print advisory warnings otherwise; non-zero exit is reserved for hook errors"
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

- [x] Claude Code adapter includes `hooks.json` and executable scripts per contract — evidence: `tools/adapters/claude-code/hooks.json` (4 events) and 7 executable scripts in `hooks/`; `.claude/settings.json` matches. HC-007 runs inside `close-out-check.sh` rather than as its own script.
- [x] Scripts signal block/warn decisions on stdout in the tool's native protocol — evidence: `document-first-gate.sh:68-69` emits `"permissionDecision": "deny"`; `close-out-check.sh:35,51,61` emit `"decision": "block"`; advisory hooks (`phase-alignment.sh`, `risk-scan-trigger.sh`, `snapshot-freshness.sh`) print warnings and exit 0.
- [x] Hook implementations documented with expected inputs and outputs — evidence: header block in every script naming contract ID, event, matcher, input and exit semantics (e.g. `verification-gate.py:1-16`); adapter table at `tools/adapters/claude-code/ADAPTER.md:129-142`.

## Amendments (2026-07-21)

**Criterion 2** originally read "Scripts exit non-zero to block or return warnings via stdout". This is factually wrong for the delivered system and would be wrong to implement: in Claude Code a non-zero hook exit signals a *hook error*, not a block. Blocking is expressed by exiting 0 with structured JSON on stdout (`permissionDecision: deny` / `decision: block`), as documented in every script header. The criterion was rewritten to the actual protocol; no hook script exits non-zero anywhere in the repo.

## Traceability
- Implements: [[FEAT-0002-Hook-Contracts]]
- Decided by: [[ADR-0002-Hook-Contract-Pattern]]

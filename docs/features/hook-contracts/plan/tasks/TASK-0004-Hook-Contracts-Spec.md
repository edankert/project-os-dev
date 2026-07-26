---
type: "[[task]]"
id: TASK-0004
aliases: ["TASK-0004"]
title: "Define HOOKS.md with tool-agnostic hook contracts"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0002-Hook-Contracts]]"
fixes: []
effort: M
due: ""
depends: []
blocks: [TASK-0005]
related: []
tests: []
---

# Define HOOKS.md with tool-agnostic hook contracts

## Definition of Done
- [x] `tools/instructions/HOOKS.md` exists with all hook contracts
- [x] Each contract has: ID, trigger description, check logic, failure behaviour, reference to enforced rule
- [x] Contracts defined for: verification gating, risk scan triggers, phase alignment, snapshot freshness, document-first rule
- [x] HOOKS.md is referenced from tools/instructions/README.md

## Steps
- [x] Define HC-001 (Verification Gate)
- [x] Define HC-002 (Risk Scan Trigger)
- [x] Define HC-003 (Phase Alignment)
- [x] Define HC-004 (Snapshot Freshness)
- [x] Define HC-005 (Document-First)
- [x] Add HOOKS.md to the instructions README index

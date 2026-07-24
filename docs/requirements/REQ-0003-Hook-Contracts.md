---
type: "[[requirement]]"
id: REQ-0003
aliases: ["REQ-0003"]
title: "Enforcement points must be defined as tool-agnostic contracts"
status: implemented
phase: []
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-07-21
source: []
priority: high
scope: "hooks"
acceptance:
  - "A HOOKS.md file defines each enforcement point with trigger, check, and failure behaviour"
  - "Contracts are independent of any specific tool's hook mechanism"
  - "Each contract references the project-os rule it enforces (traceability)"
implements: ["[[FEAT-0002-Hook-Contracts]]"]
verifies: []
related: ["[[REQ-0004-Tool-Specific-Hook-Implementations]]"]
tests: []
---

# Enforcement points must be defined as tool-agnostic contracts

## Statement
project-os MUST define its enforcement points as tool-agnostic contracts in a single specification file (`HOOKS.md`), independent of any specific tool's hook mechanism.

## Acceptance Criteria

- [x] `HOOKS.md` defines each enforcement point with trigger, check, and failure behaviour — evidence: `tools/instructions/HOOKS.md`, contracts HC-001..HC-007 each with `Trigger:` / `Check logic:` / `On failure:`.
- [x] Contracts are independent of any specific tool's hook mechanism — evidence: tool bindings are quarantined on explicit `Implementations:` lines in `HOOKS.md` (HC-001, HC-002, HC-004, HC-005, HC-006); `../adapters/<tool>/ADAPTER.md` carries the tool-specific mapping.
- [x] Each contract references the project-os rule it enforces — evidence: a per-contract `Rule:` line on all seven contracts in `HOOKS.md`, e.g. HC-003 → `QUALITY.md` "Verification gating (tests)".

## Amendments (2026-07-21)

Criterion 3 was **not** satisfied at verification time — only 2 of 7 contracts referenced a rule, and none carried a traceability field. Rather than amend the criterion, the gap was closed: a `Rule:` line was added to every contract (HC-001..HC-007) and the file header now states that each contract names the rule it enforces. The criterion is ticked because the work was done, not because it was narrowed.

## Traceability
- Implements: [[FEAT-0002-Hook-Contracts]]
- Decided by: [[ADR-0002-Hook-Contract-Pattern]]

---
type: "[[requirement]]"
id: REQ-0003
title: "Enforcement points must be defined as tool-agnostic contracts"
status: approved
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
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
- A `HOOKS.md` file defines each enforcement point with trigger, check, and failure behaviour
- Contracts are independent of any specific tool's hook mechanism
- Each contract references the project-os rule it enforces (traceability)

## Traceability
- Implements: [[FEAT-0002-Hook-Contracts]]
- Decided by: [[ADR-0002-Hook-Contract-Pattern]]

---
type: "[[feature]]"
id: FEAT-0004
aliases: ["FEAT-0004"]
title: "Remove orchestration fields from SNAPSHOT.yaml"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
goal: "Simplify SNAPSHOT.yaml by removing session/claimed_by fields and positioning it as project context only"
release: ""
related: ["[[ADR-0003-Delegate-Orchestration]]", "[[FEAT-0003-Team-Model]]"]
---

# Remove orchestration fields from SNAPSHOT.yaml

## Goal
Simplify SNAPSHOT.yaml by removing agent coordination fields (`session`, `claimed_by`, `claim_started`) and updating all instructions that reference them. SNAPSHOT.yaml becomes purely a project context file.

## Scope
**In scope:**
- Remove `session` object from SNAPSHOT.yaml template and SNAPSHOT.md
- Remove `claimed_by`/`claim_started` from item schema
- Rewrite HANDOFF.md for orchestration-agnostic recovery
- Update snapshot-sync skill (remove stale-claim detection)
- Update status-transition skill (remove claim-check gate)

**Out of scope:**
- Adding the team model (FEAT-0003 handles that)

## Acceptance
- SNAPSHOT.yaml template has no session, claimed_by, or heartbeat fields
- All instructions and skills referencing these fields are updated
- Recovery/handoff works using project state (statuses, note content) only

## Links
- Requirements: [[REQ-0005-Orchestration-Delegation]]
- Tasks: [[TASK-0010-Remove-Session-Fields]], [[TASK-0011-Remove-Claimed-By]], [[TASK-0012-Update-Handoff-Recovery]]
- Decision: [[ADR-0003-Delegate-Orchestration]]

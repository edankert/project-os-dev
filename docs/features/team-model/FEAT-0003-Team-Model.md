---
type: "[[feature]]"
id: FEAT-0003
title: "Team model replacing agent orchestration"
status: done
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
goal: "Replace session/claimed_by orchestration in SNAPSHOT.yaml with a team model that delegates coordination to native tool orchestration"
requirements: ["[[REQ-0005-Orchestration-Delegation]]"]
tasks: ["[[TASK-0007-Team-Schema]]", "[[TASK-0008-Update-SNAPSHOT-Template]]", "[[TASK-0009-Update-Lifecycle-Preflight]]"]
release: ""
related: ["[[ADR-0003-Delegate-Orchestration]]", "[[FEAT-0004-Snapshot-Simplification]]"]
tests: []
---

# Team model replacing agent orchestration

## Goal
Add a lightweight `team` model to SNAPSHOT.yaml that identifies who is on the team and what tool/adapter each member uses, without attempting real-time coordination. Coordination is delegated to native tool orchestration (Claude Code Agent Teams, Codex parallel, etc.).

## Scope
**In scope:**
- Team schema definition (members, tool, adapter path)
- SNAPSHOT.yaml template update
- LIFECYCLE.md preflight update (remove claim-checking, add orchestration-agnostic steps)

**Out of scope:**
- Real-time agent coordination
- Cross-tool orchestration protocols
- Agent identity management

## Acceptance
- SNAPSHOT.yaml template includes a `team` section
- Team members list their ID, tool, and adapter path
- Preflight rules do not include claim-checking steps
- Documentation acknowledges that coordination is the native tool's responsibility

## Links
- Requirements: [[REQ-0005-Orchestration-Delegation]]
- Tasks: [[TASK-0007-Team-Schema]], [[TASK-0008-Update-SNAPSHOT-Template]], [[TASK-0009-Update-Lifecycle-Preflight]]
- Decision: [[ADR-0003-Delegate-Orchestration]]

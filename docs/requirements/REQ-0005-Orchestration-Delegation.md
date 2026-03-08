---
type: "[[requirement]]"
id: REQ-0005
title: "project-os must delegate agent coordination to native tool orchestration"
status: approved
phase:
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
priority: high
scope: "orchestration"
acceptance:
  - "SNAPSHOT.yaml does not contain session, claimed_by, or heartbeat fields"
  - "SNAPSHOT.yaml contains a team model identifying members and their tool adapters"
  - "Preflight rules do not include claim-checking steps"
  - "Recovery/handoff instructions work without agent-specific session metadata"
implements: ["[[FEAT-0003-Team-Model]]", "[[FEAT-0004-Snapshot-Simplification]]"]
verifies: []
related: []
tests: []
---

# project-os must delegate agent coordination to native tool orchestration

## Statement
project-os MUST NOT implement agent coordination (claiming, heartbeats, session tracking). It MUST delegate this to native tool orchestration (Claude Code Agent Teams, Codex parallel tasks, etc.) and focus on project-level context.

## Acceptance Criteria
- SNAPSHOT.yaml does not contain `session`, `claimed_by`, or `heartbeat` fields
- SNAPSHOT.yaml contains a `team` model identifying members and their tool adapters
- Preflight rules do not include claim-checking steps
- Recovery/handoff instructions work without agent-specific session metadata

## Traceability
- Implements: [[FEAT-0003-Team-Model]], [[FEAT-0004-Snapshot-Simplification]]
- Decided by: [[ADR-0003-Delegate-Orchestration]]

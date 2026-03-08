---
type: "[[adr]]"
id: ADR-0003
title: "Delegate agent coordination to native tool orchestration"
status: accepted
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
decision: "Remove session/claimed_by orchestration from SNAPSHOT.yaml and let native tools handle multi-agent coordination"
context: "SNAPSHOT.yaml's session/claimed_by fields are a primitive coordination mechanism. Claude Code Agent Teams and Codex parallel tasks provide real orchestration. project-os should not compete with native tools."
alternatives:
  - "Keep session/claimed_by fields for tool-agnostic coordination"
  - "Remove orchestration entirely and provide no multi-agent support"
  - "Replace orchestration with a team model and delegate coordination to native tools"
consequences:
  - "SNAPSHOT.yaml becomes simpler (project context only, no agent state)"
  - "Multi-agent coordination handled by the tool that's better at it"
  - "Team model identifies members and their adapters without tracking real-time state"
  - "Recovery/handoff protocol simplified — relies on SNAPSHOT.yaml project state, not session metadata"
  - "project-os loses the ability to coordinate agents across different tools (no cross-tool orchestration)"
supersedes: ""
superseded: ""
related: ["[[FEAT-0003-Team-Model]]", "[[FEAT-0004-Snapshot-Simplification]]", "[[REQ-0005-Orchestration-Delegation]]"]
---

# Delegate agent coordination to native tool orchestration

## Context
SNAPSHOT.yaml currently includes `session` (agent_id, last_heartbeat, current_step) and item-level `claimed_by`/`claim_started` fields. These are a file-based attempt at distributed coordination — checking heartbeats, detecting stale claims, preventing concurrent work on the same item.

This approach has fundamental limitations:
- No locking mechanism (two agents can claim simultaneously)
- No real-time awareness (file-based heartbeats are inherently stale)
- Competing with purpose-built orchestration in Claude Code Agent Teams, Codex parallel tasks, and Cursor subagents

Meanwhile, native tool orchestration is maturing rapidly (6-12 month horizon for mature solutions from major vendors).

## Decision
- Remove `session` object and `claimed_by`/`claim_started` from SNAPSHOT.yaml
- Add a `team` model that identifies members and their tool adapters (who is on the team and what tool they use)
- Let native tools handle "who works on what right now" and "are they still alive"
- project-os handles "what does the project look like" and "what happened" (its actual strength)

## Alternatives
- **Keep orchestration fields**: Maintain session/claimed_by for tool-agnostic coordination. Rejected because the mechanism is too primitive to be reliable and competes with better solutions.
- **Remove all multi-agent awareness**: Drop team model entirely. Rejected because knowing who is on the team and what adapter they use is still valuable for the adapter system.

## Consequences
- SNAPSHOT.yaml is simpler and focused on project state
- No cross-tool agent orchestration (a new Codex agent can't detect that a Claude Code agent is working on the same task via SNAPSHOT.yaml alone — but native tools within the same ecosystem can)
- Recovery relies on project state (SNAPSHOT.yaml statuses, note content) rather than session metadata
- Team model is lightweight and informational, not a coordination mechanism

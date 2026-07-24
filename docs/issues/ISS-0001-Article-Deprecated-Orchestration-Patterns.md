---
type: "[[issue]]"
id: ISS-0001
aliases: ["ISS-0001"]
title: "Use Cases article references deprecated orchestration patterns"
status: closed
severity: medium
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
component: documentation
source: []
related: [FEAT-0003, FEAT-0004]
tasks: []
---

# Use Cases article references deprecated orchestration patterns

## Description

The "project-os: Use Cases and Scenarios" article (`Notes/03 Projects/Project OS/project-os Use Cases and Scenarios.md`) references `claimed_by`, `claim_started`, `session`, `agent_id`, `last_heartbeat`, and `current_step` fields in Use Cases 2 (Multi-Agent Collaboration) and 14 (Recovery from Interrupted Sessions).

These fields will be removed from the project-os template when FEAT-0003 (Team Model) and FEAT-0004 (Snapshot Simplification) are implemented.

## Impact

- Use Case 2 is entirely based on claimed_by/session coordination — will need a complete rewrite to describe the team model and native tool orchestration
- Use Case 14 recovery checklist references session metadata — will need rewriting to use SNAPSHOT.yaml statuses, git status, and recent changes instead

## Action Required

After FEAT-0003 and FEAT-0004 are implemented:
1. Rewrite Use Case 2 to describe team model + native orchestration delegation
2. Rewrite Use Case 14 to describe orchestration-agnostic recovery
3. Update the "Context Is All You Need" article if it references these patterns

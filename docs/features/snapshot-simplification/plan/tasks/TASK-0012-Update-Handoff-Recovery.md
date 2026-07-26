---
type: "[[task]]"
id: TASK-0012
aliases: ["TASK-0012"]
title: "Rewrite HANDOFF.md for orchestration-agnostic recovery"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0004-Snapshot-Simplification]]"
fixes: []
effort: M
due: ""
depends: [TASK-0010, TASK-0011]
blocks: []
related: []
tests: []
---

# Rewrite HANDOFF.md for orchestration-agnostic recovery

## Definition of Done
- [x] HANDOFF.md recovery checklist works without session metadata
- [x] Recovery relies on: SNAPSHOT.yaml statuses, note content, git status, recent changes
- [x] Handoff checklist focuses on project state (statuses, focus, relationships) not agent state
- [x] No references to session, claimed_by, or heartbeat

## Steps
- [x] Rewrite "Before stopping work" checklist (focus on project state updates)
- [x] Rewrite "Recovery checklist" (use snapshot-sync, git status, recent changes — no session inspection)
- [x] Add note: "Agent coordination is handled by your tool's native orchestration (Agent Teams, Codex parallel, etc.)"
- [x] Review cross-references to HANDOFF.md and update

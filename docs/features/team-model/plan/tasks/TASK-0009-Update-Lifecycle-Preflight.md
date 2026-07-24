---
type: "[[task]]"
id: TASK-0009
aliases: ["TASK-0009"]
title: "Update LIFECYCLE.md preflight to remove claim-checking, add orchestration-agnostic steps"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0003-Team-Model]]"
fixes: []
effort: M
due: ""
depends: [TASK-0010, TASK-0011]
blocks: []
related: ["[[FEAT-0004-Snapshot-Simplification]]"]
tests: []
---

# Update LIFECYCLE.md preflight to remove claim-checking, add orchestration-agnostic steps

## Definition of Done
- [x] LIFECYCLE.md preflight no longer includes claim-checking steps
- [x] Preflight includes: "If your orchestration layer assigns a specific task, verify it exists in SNAPSHOT.yaml"
- [x] No references to session, claimed_by, or heartbeat in preflight

## Steps
- [x] Remove claim-check step (step 2 in current preflight)
- [x] Add orchestration-agnostic step for tool-assigned tasks
- [x] Renumber remaining steps
- [x] Review all cross-references to LIFECYCLE.md preflight

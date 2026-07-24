---
type: "[[task]]"
id: TASK-0010
aliases: ["TASK-0010"]
title: "Remove session object from SNAPSHOT.yaml template and SNAPSHOT.md"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0004-Snapshot-Simplification]]"
fixes: []
effort: S
due: ""
depends: []
blocks: [TASK-0009, TASK-0012]
related: []
tests: []
---

# Remove session object from SNAPSHOT.yaml template and SNAPSHOT.md

## Definition of Done
- [x] SNAPSHOT.yaml template has no `session` object (not even commented out)
- [x] SNAPSHOT.md no longer documents session fields (agent_id, started, last_heartbeat, current_step)
- [x] SNAPSHOT.md no longer lists session as an optional top-level key

## Steps
- [x] Remove session from SNAPSHOT.yaml template
- [x] Remove session documentation from SNAPSHOT.md
- [x] Search for references to session fields across all instruction files and update

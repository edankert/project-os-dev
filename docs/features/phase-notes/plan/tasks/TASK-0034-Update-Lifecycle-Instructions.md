---
type: "[[task]]"
id: TASK-0034
aliases: ["TASK-0034"]
title: "Update LIFECYCLE.md, SNAPSHOT.md, and phase alignment rules"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
parent: "[[FEAT-0008-Phase-Notes]]"
fixes: []
effort: S
due: ""
depends: ["[[TASK-0033-Migrate-Phase-Field]]"]
blocks: []
related: []
tests: []
---

# Update Lifecycle and Snapshot Instructions

## Definition of Done
- [ ] LIFECYCLE.md "Phase alignment" section references phase notes instead of integer comparison
- [ ] `focus.phase` in SNAPSHOT.yaml changes from integer to phase note ID (e.g., `PHASE-001`)
- [ ] SNAPSHOT.md documents phase items section (`items.phases`)
- [ ] Phase alignment hook (HC-004) logic updated for link-based comparison
- [ ] Template SNAPSHOT.yaml includes `phases: {}` in items and `PHASE: 0` in counters

## Steps
- [ ] Edit `tools/instructions/LIFECYCLE.md` phase alignment section
- [ ] Edit `tools/instructions/SNAPSHOT.md` items documentation
- [ ] Edit template `SNAPSHOT.yaml`
- [ ] Edit `tools/adapters/claude-code/hooks/phase-alignment.sh` if needed

---
type: "[[task]]"
id: TASK-0043
aliases: ["TASK-0043"]
title: "Cockpit verification health: implement FEAT-0018 in project-os-cockpit"
status: doing
phase: []
platform:
owner: user:edwin
created: 2026-07-17
updated: 2026-07-17
source: []
parent: "[[FEAT-0010-Template-Completeness-Program]]"
fixes: []
effort: L
due: ""
depends: []
blocks: []
related: []
external: "../project-os-cockpit/docs/features/verification-health/FEAT-0018-Verification-Health-Surface.md"
tests: []
---

# Cockpit verification health

Implementation is tracked in project-os-cockpit under FEAT-0018 (TASK-0111 validation endpoint, TASK-0112 health badge + drift panel, TASK-0113 waiver/review/adequacy badges); this task tracks the program-level delegation and verification.

## Definition of Done

- [ ] TASK-0111: `GET /api/cockpit/validation` runs the repo's `tools/scripts/validate-docs.py`, cached, debounced re-run on watcher events, fanned out over SSE.
- [ ] TASK-0112: top-bar health badge (green/red+count/grey) with a drift panel deep-linking each violation to the offending note.
- [ ] TASK-0113: waiver/review-verdict/adequacy frontmatter promoted to badges in metadata strip and list rows.
- [ ] Fleet-health (desktop shell) and MCP-server follow-ups scaffolded as backlog features in project-os-cockpit.
- [ ] Cockpit repo left uncommitted (PHASE-007 batch pending there); FEAT-0018/task statuses updated in its own SNAPSHOT and notes.

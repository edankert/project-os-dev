---
type: "[[task]]"
id: TASK-0014
aliases: ["TASK-0014"]
title: "Make verification gating first step in close-out"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
source: []
parent: "[[FEAT-0005-Enforcement-Hardening]]"
fixes: []
effort: S
due: ""
depends: []
blocks: []
related: [REQ-0006]
tests: []
---

# Make verification gating first step in close-out

## Definition of Done
- [x] Close-out skill (`tools/skills/close-out/SKILL.md`) checks linked test statuses as step 1
- [x] Verification is a mandatory gate — agent must STOP if tests are not passing
- [x] Gate runs before any status updates

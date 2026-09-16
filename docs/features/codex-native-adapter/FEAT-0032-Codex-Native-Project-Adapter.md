---
type: "[[feature]]"
id: FEAT-0032
title: "Codex native project adapter"
status: review
phase: "[[PHASE-0006]]"
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
source: ["[[PHASE-0006-Codex-Native-Adapter]]"]
goal: "A Codex session in a project-os repo can discover the same playbooks and receive lifecycle checks comparable to Claude Code."
requirements: [REQ-0030]
tasks: [TASK-0124]
release: ""
acceptance_exception: "This template has no user-facing screen; the executable adapter fixture and generator check are its acceptance evidence."
related: [RISK-0003]
---

# Codex native project adapter

## Goal
Codex users get discoverable skills, named planning and review agents, and lifecycle hook checks from the project-os template.

## Scope
Generate native files from canonical playbooks, install hooks safely, test hook decisions, and document the remaining differences from Claude Code.

## Acceptance
- Codex skills and agents are regenerated from canonical sources and detected by `--check` when stale.
- Hook installation preserves existing user configuration unless explicitly forced.
- Hooks handle Codex tool payloads and state their coverage and trust limits.
- A fixture suite verifies the document-first and verification decisions and advisory lifecycle behavior.

## Links
- Requirement: [[REQ-0030-Codex-Receives-Native-Project-OS-Integration]]
- Task: [[TASK-0124-Implement-And-Verify-Codex-Native-Adapter]]

## Implementation status 2026-09-16
The upstream template now generates 26 Codex skill wrappers and two Codex agent profiles, installs a repository hook file when absent, and runs HC-001..HC-008 event handling through a Codex payload adapter. The 12 fixture checks and generated-file drift check pass. Review and a live trusted session remain before this feature advances to `done`; cockpit telemetry remains in project-os-cockpit ISS-0312 and PHASE-040.

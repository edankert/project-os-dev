---
type: "[[phase]]"
id: PHASE-0006
title: "Codex native project adapter"
status: active
order: 6
owner: user:edwin
created: 2026-09-16
updated: 2026-09-16
goal: "Give Codex native project-os skills, agents, and lifecycle hooks generated from the same canonical playbooks as Claude Code."
features: [FEAT-0032]
requirements: [REQ-0030]
tasks: [TASK-0124]
issues: []
related: [RISK-0003]
tags: [codex, adapters]
---

# Codex native project adapter

## Goal
A project-os repository exposes its canonical skills, preflight and review agents, and lifecycle checks through Codex's native formats.

## Scope
- Generate repository skills and agents from the canonical project-os playbooks.
- Install Codex hooks for lifecycle checks, retaining CI and git hooks as the backstop.
- Document activation, trust requirements, and contract coverage.

## Out of Scope
- Cockpit telemetry and hook ingestion in project-os-cockpit PHASE-040.
- A fleet-wide rollout to every downstream repository.

## Exit Criteria
- [ ] Independent review approves FEAT-0032 and REQ-0030, and the upstream change is committed with CI green.
- [x] The generated artifacts and hook runner pass a fixture test and the adapter generator drift check.
- [x] The Codex adapter is documented with any coverage limits.
- [x] The project-os template and this tracking repository validate cleanly.

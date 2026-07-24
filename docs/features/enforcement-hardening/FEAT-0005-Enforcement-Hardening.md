---
type: "[[feature]]"
id: FEAT-0005
aliases: ["FEAT-0005"]
title: "Enforcement hardening — mandatory skills, verification gating, impact analysis"
status: done
owner: user:edwin
created: 2026-03-08
updated: 2026-03-08
phase: []
goal: "Harden project-os skill enforcement by making risk scans, verification gating, and impact analysis mandatory steps rather than conditional ones"
related: [ADR-0004]
---

# Enforcement Hardening

## Goal

Harden project-os skill enforcement by making risk scans, verification gating, and impact analysis mandatory steps rather than conditional ones. This ensures that capabilities described in project-os documentation are actually enforced through the skill checklists.

## Context

An audit of the project-os template revealed that several capabilities described as enforced were actually implemented as optional/conditional steps in skill checklists. This feature captures the work done to close that gap.

## What Changed

1. **Impact analysis skill created** (`tools/skills/impact-analysis/SKILL.md`) — new playbook for traversing the link graph and detecting requirement conflicts
2. **Verification gating hardened** — moved to step 1 in close-out, added as pre-transition gate in status-transition
3. **Risk scans made mandatory** — explicit trigger checklists added to close-out, feature-scaffold, and issue-intake
4. **Impact analysis made mandatory** — added to feature-scaffold and issue-intake as required steps
5. **Pre-transition gates added** — verification, phase alignment, and claim checks in status-transition skill

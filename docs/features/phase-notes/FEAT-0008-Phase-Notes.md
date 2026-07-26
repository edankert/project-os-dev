---
type: "[[feature]]"
id: FEAT-0008
aliases: ["FEAT-0008"]
title: "Phases as first-class note type"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
goal: "Promote phases from a single registry file to individual navigable notes with contextual dashboards"
release: ""
related: ["[[FEAT-0007-Relationship-Model]]"]
---

# Phases as First-Class Note Type

## Goal
Promote phases from a single `docs/PHASES.md` registry file to individual navigable notes (`type: [[phase]]`) so that:
- Phases are clickable links in Obsidian — selecting a phase shows its contextual dashboard
- Each phase note has an embedded Overview.base showing all features, tasks, issues, and requirements in that phase
- A top-level `Phases.base` dashboard shows all phases with their status
- The `phase` field on notes becomes a link (`"[[PHASE-001-Foundation]]"`) instead of an integer

## Scope

**In scope:**
- New `phase.md` template with frontmatter schema
- New `Phases.base` top-level dashboard
- New `phase-overview.base` contextual dashboard template
- Change `phase` field from integer to link across all existing templates
- Update LIFECYCLE.md phase alignment section
- Update SNAPSHOT.md for phase items
- Update skills that reference phases (feature-scaffold, task-breakdown, status-transition)
- Replace `docs/PHASES.md` registry with individual phase notes under `docs/phases/`

**Out of scope:**
- Migrating existing phase integers in downstream repos (handled per-project)

**Dependency:** FEAT-0007 (relationship model) should land first so the `phase` field uses the same `contains`-based filtering pattern.

## Acceptance
- Phase notes are navigable in Obsidian with clickable links
- Selecting a phase note shows all items in that phase via embedded Overview.base
- Phases.base dashboard shows all phases with status (draft/active/completed)
- All templates use link-based `phase` field
- LIFECYCLE.md phase alignment rules reference phase notes instead of integers

## Links
- Requirements: [[REQ-0011-Phase-Notes]]
- Related: [[FEAT-0007-Relationship-Model]]

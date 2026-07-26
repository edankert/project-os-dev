---
type: "[[feature]]"
id: FEAT-0009
aliases: ["FEAT-0009"]
title: "Obsidian cockpit layout with NAV.base and CONTEXT.base"
status: done
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-04-05
source: []
goal: "Three-pane Obsidian layout: left sidebar for navigation, center editor, right sidebar for dynamic context using this.file"
release: ""
related: ["[[FEAT-0007-Relationship-Model]]", "[[FEAT-0008-Phase-Notes]]"]
---

# Obsidian Cockpit Layout

## Goal
Create a three-pane Obsidian layout that provides a project management cockpit:
- **Left sidebar**: NAV.base — browse features, phases, and issues
- **Center**: Editor — the selected note
- **Right sidebar**: CONTEXT.base — dynamically shows tasks, requirements, issues, and tests related to the active note using `this.file`

## Scope

**In scope:**
- `docs/NAV.base` — pinned left sidebar with tabbed views for features, phases, issues
- `docs/CONTEXT.base` — pinned right sidebar using `this.file` to filter related items
- Remove per-feature Overview.base generation (replaced by CONTEXT.base)
- Remove feature-overview.base template
- Remove `![[Overview.base]]` embed from feature template
- Update DASHBOARD.md for the new layout
- Document workspace setup in OBSIDIAN.md

**Out of scope:**
- Custom Obsidian plugins
- Changes to the relationship model itself (handled by FEAT-0007)

**Dependencies:**
- FEAT-0007 must land first — CONTEXT.base filters on `implements`, `affects`, `specifies`, `validates`
- FEAT-0008 for phases to appear in NAV.base

## Design

### NAV.base (Left Sidebar)
Tabbed views:
- **Features**: Active features sorted by phase
- **Phases**: All phases sorted by order
- **Issues**: Open issues sorted by severity

### CONTEXT.base (Right Sidebar)
Filters using `this.file` against all relationship fields:
```
implements contains this.file
OR fixes contains this.file
OR affects contains this.file
OR specifies contains this.file
OR validates contains this.file
OR phase contains this.file
```
Tabbed views: All, Tasks, Requirements, Issues, Tests

Updates automatically when the center editor note changes.

## Acceptance
- NAV.base pinned in left sidebar shows features, phases, issues
- Clicking an item in NAV.base opens it in the center editor
- CONTEXT.base in right sidebar dynamically shows related items for the active note
- Switching notes in the center immediately updates the right sidebar
- No per-feature Overview.base files exist
- Workspace setup is documented

## Links
- Requirements: [[REQ-0012-Cockpit-Layout]]
- Related: [[FEAT-0007-Relationship-Model]], [[FEAT-0008-Phase-Notes]]

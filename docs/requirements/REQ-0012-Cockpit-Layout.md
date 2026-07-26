---
type: "[[requirement]]"
id: REQ-0012
aliases: ["REQ-0012"]
title: "Obsidian must provide a three-pane cockpit layout with navigation, editor, and dynamic context"
status: implemented
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-07-21
source: []
priority: high
scope: "template-wide"
acceptance:
  - "NAVIGATION.base (docs/__bases__/) provides tabbed navigation for features, phases, and issues in the left sidebar"
  - "CONTEXT.base dynamically filters items related to the active editor note using this.file"
  - "CONTEXT.base surfaces related items through the generic link graph (file.hasLink) rather than per-field filters, covering every relationship field including phase"
  - "No per-feature or per-phase Overview.base files are needed"
  - "Workspace setup is documented so downstream repos can replicate the layout"
implements: ["[[FEAT-0009-Cockpit-Layout]]"]
verifies: []
related: []
tests: []
---

# Cockpit Layout

## Statement
Obsidian must provide a three-pane cockpit layout where the left sidebar shows navigable big items (features, phases, issues), the center is the editor, and the right sidebar dynamically shows tasks, requirements, issues, and tests related to the active note using Bases `this.file` filtering.

## Acceptance Criteria

- [x] `NAVIGATION.base` provides tabbed navigation for features, phases and issues in the left sidebar — evidence: `docs/__bases__/NAVIGATION.base` with six views (Features/Phases/Issues, each plus an "Open" variant); left-pane role documented in `docs/__bases__/README.md`.
- [x] `CONTEXT.base` dynamically filters items related to the active note using `this.file` — evidence: `docs/__bases__/CONTEXT.base` `file.hasLink(this.file)`; tabbed views All / Tasks / Requirements / Issues / Tests / All (Open).
- [x] `CONTEXT.base` surfaces related items through the generic link graph rather than per-field filters — evidence: the single `file.hasLink(this.file)` predicate covers every relationship field at once, including `phase`; per-field filters were dropped with the [[REQ-0010-Named-Relationship-Fields|REQ-0010]] revert and are specified by [[REQ-0015-Relationship-Model|REQ-0015]].
- [x] No per-feature or per-phase `Overview.base` files are needed — evidence: the whole docs set contains exactly two `.base` files (`NAVIGATION.base`, `CONTEXT.base`); `feature-overview.base` is absent and the feature template embeds no base.
- [x] Workspace setup is documented so downstream repos can replicate the layout — evidence: `tools/instructions/OBSIDIAN.md` "Workspace setup (three-pane cockpit)" — vault/Bases enablement, left/centre/right pane assignment, saved workspace, and the `tools/cockpit/` browser alternative.

## Amendments (2026-07-21)

Two criteria reconciled, one gap closed by doing the work.

- **`NAV.base` → `NAVIGATION.base`**: the file was renamed during the May 2026 bases consolidation (`CHG-20260508`) and lives in `docs/__bases__/`, not `docs/` root. Criterion updated to the shipped name and path; substance (tabbed feature/phase/issue navigation) is unchanged.
- **Per-field CONTEXT filters**: the criterion named `implements`, `fixes`, `affects`, `specifies`, `validates`, `phase` — five of which never shipped (see [[REQ-0010-Named-Relationship-Fields|REQ-0010]]). The delivered design filters on the link graph itself, which covers all relationship fields including ones added later. Criterion rewritten to the mechanism that shipped.
- **Workspace documentation** was genuinely missing: `OBSIDIAN.md` covered only linking, properties and naming, with no pane or layout guidance anywhere. Closed by writing the "Workspace setup (three-pane cockpit)" section rather than narrowing the criterion.

## Traceability
- Feature: [[FEAT-0009-Cockpit-Layout]]

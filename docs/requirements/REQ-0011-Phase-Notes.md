---
type: "[[requirement]]"
id: REQ-0011
aliases: ["REQ-0011"]
title: "Phases must be navigable first-class notes with contextual dashboards"
status: implemented
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-07-21
source: []
priority: medium
scope: "template-wide"
acceptance:
  - "Each phase is an individual note with type [[phase]] and standard frontmatter"
  - "Phase status is planned / active / done / deferred"
  - "Phase notes are stored under docs/phases/ with naming PHASE-###-Short-Name.md"
  - "The phase field accepts a [[PHASE-####]] link, with bare integers tolerated during migration"
  - "Phases are listed with status and ordered by order in the navigation dashboard (NAVIGATION.base)"
  - "Items belonging to a phase are reachable contextually from the phase note (CONTEXT.base link-graph filter, right pane)"
  - "docs/PHASES.md is retained as the phase registry, with per-phase notes as the navigable detail"
implements: ["[[FEAT-0008-Phase-Notes]]"]
verifies: []
related: []
tests: []
---

# Phase Notes

## Statement
Phases must be promoted to navigable first-class notes so users can click on a phase link to see all work items belonging to that phase, with a contextual dashboard embedded in each phase note.

## Acceptance Criteria

- [x] Each phase is an individual note with `type: [[phase]]` and standard frontmatter — evidence: `docs/__templates__/phase.md`; `docs/phases/README.md`.
- [x] Phase notes live under `docs/phases/` as `PHASE-####-Short-Name.md` — evidence: `docs/phases/README.md`, `SCHEMAS.md` (four-digit ID, per the repo-wide ID width).
- [x] The `phase` field accepts a `[[PHASE-####]]` link, with bare integers tolerated during migration — evidence: `SCHEMAS.md` ("link or integer … prefer `[[PHASE-####]]` links"); `docs/PHASES.md`.
- [x] Phase status is `planned` / `active` / `done` / `deferred` — evidence: `tools/instructions/STATUSES.md`; enforced at `tools/scripts/validate-docs.py` (`"phase": {"planned", "active", "done", "deferred"}`); template default `status: planned`.
- [x] Phases are listed with status and ordered by `order` in the navigation dashboard — evidence: `docs/__bases__/NAVIGATION.base` views "Phases (All)" and "Phases (Open)", sorted on `order`; `order` is a required integer in `SCHEMAS.md`.
- [x] Items belonging to a phase are reachable contextually from the phase note — evidence: `docs/__bases__/CONTEXT.base` (`file.hasLink(this.file)`) renders every note linking the focused phase, in the right pane.
- [x] `docs/PHASES.md` is retained as the phase registry, with per-phase notes as the navigable detail — evidence: `docs/phases/README.md` ("the top-level `../PHASES.md` file **is** the phase registry and overview"); `LIFECYCLE.md` phase-alignment step directs agents to it.

## Amendments (2026-07-21)

Four criteria were reconciled; the core intent (phases as navigable first-class notes with contextual item views) shipped and is ticked above.

- **Phase statuses** were specified as `draft`/`active`/`completed`. The shipped taxonomy is `planned`/`active`/`done`/`deferred` — aligned with the other note types and mechanically enforced. The original values would *fail validation today*; criterion corrected to the real set (added as its own criterion, split out of the frontmatter's first entry).
- **`Phases.base`** was built and then deleted in the May 2026 bases consolidation (`CHG-20260508`). Its role moved into `NAVIGATION.base` ("Phases (All)" / "Phases (Open)"). Criterion rewritten to the surviving surface. Note the consolidation dropped the board view: phase views are tables only.
- **`phase-overview.base` embedded per phase note** never existed. The generic `CONTEXT.base` right-pane filter covers the "all items in this phase" role without a per-phase artifact — which is what made deleting the per-feature/per-phase `.base` files possible. Criterion rewritten to the delivered mechanism.
- **Replacing `docs/PHASES.md`** was reversed: the registry is deliberately retained as the ordered overview, with phase notes as navigable detail. Criterion inverted to describe the two-layer model that shipped.

Also noted, not amended: `test.md` and `risk.md` carry no `phase` field, so the "all note types" phrasing of criterion 3 is aspirational for those two. Left as-is because neither type is phase-scheduled in practice.

## Traceability
- Feature: [[FEAT-0008-Phase-Notes]]

---
type: "[[change]]"
id: CHG-20260721-Deferral-As-Descoping
aliases: ["CHG-20260721-Deferral-As-Descoping"]
title: "Deferral becomes a descoping operation: origin provenance, forward home, validator DEFER checks, parked surfacing"
status: merged
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
commit: ""
pr: ""
reviewed_by: model:claude-opus-4-8
review_date: 2026-07-21
review_verdict: approved
impacts:
  - "project-os: tools/instructions/STATUSES.md, QUALITY.md, SNAPSHOT.md, TRACEABILITY.md"
  - "project-os: docs/__templates__/SCHEMAS.md"
  - "project-os: tools/skills/status-transition, backlog-grooming, close-out"
  - "project-os: tools/scripts/validate-docs.py (VERIFY scope resolution + DEFER-SCOPE/HOME/ORIGIN/PARENT/RETENTION)"
  - "project-os + project-os-cockpit: cockpit.py TASK_STATUS_ORDER (deferred moves to parked band)"
issues: [ISS-0002]
features: [FEAT-0011]
---

# Deferral becomes a descoping operation

## What changed

Fixes [[ISS-0002-Deferred-Items-Satisfy-Parent-Completeness|ISS-0002]] per [[ADR-0005-Deferral-As-Descoping|ADR-0005]], implemented in the project-os template (and the cockpit for surfacing):

- **Semantics** (`STATUSES.md`, `QUALITY.md`): a parent's `tasks:` list is its current scope. `done`/`cancelled` resolve scope; `deferred` never does. Deferring is a descoping procedure — remove from the parent's `tasks:`, record under the parent's `deferred:`, set single-word `origin:` (former parent), clear `parent:`, assign a forward home (`phase:` future phase or `PHASE-999` parking lot). Re-adoption transitions added per type.
- **Fields** (`SCHEMAS.md`, `TRACEABILITY.md`, `SNAPSHOT.md`): `origin` (common optional) and feature `deferred:` list defined; task parent rule gains the deferred exception; retention explicitly never prunes deferred items; `tasks_deferred`/`issues_deferred` metrics defined.
- **Skills**: `status-transition` gains the mandatory deferral/re-adoption procedure; `backlog-grooming` gains a mandatory parked-item review; `close-out` blocks feature `done` over deferred children. Adapters regenerated (4 `.mdc` rules).
- **Enforcement** (`validate-docs.py`): feature-done VERIFY now accepts `done`/`cancelled` (previously `cancelled` wrongly blocked closure, incentivising fake-`done` flips) and DEFER-SCOPE/DEFER-HOME/DEFER-ORIGIN/DEFER-PARENT/DEFER-RETENTION errors make orphaned or still-in-scope deferred items a build failure; `origin`/`deferred` join link-integrity fields.
- **Surfacing** (`cockpit.py`, canonical + vendored): `deferred` sorts in the parked band after `blocked`/`failing`/`reopened` instead of dead last behind `cancelled`/`reverted`.

## Verification

- Synthetic fixture exercised all six new validator error paths (plus the blank-snapshot-status escape case); correctly-descoped and cancelled cases pass clean; validator clean on project-os and project-os-dev.
- `generate-adapters.py --check` clean (32 artifacts).
- Cockpit test suite after the ordering change: 223 passed, 1 skipped.
- Independent review (model:claude-opus-4-8, 2026-07-21): approved; its three low-severity findings were addressed in-turn (waiver wording, PHASE retention coverage, effective-status gating).

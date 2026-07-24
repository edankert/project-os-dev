---
type: "[[task]]"
id: TASK-0048
aliases: ["TASK-0048"]
title: "Validator hardening: scope-resolution rule for feature done, DEFER checks, deferred metrics"
status: done
phase: []
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "tooling change verified mechanically — synthetic fixture exercised all six paths (VERIFY not-scope-resolved, DEFER-SCOPE, DEFER-HOME, DEFER-ORIGIN, DEFER-PARENT, DEFER-RETENTION) with correctly-descoped and cancelled cases passing clean; validator then ran clean on project-os and project-os-dev"
source: []
parent: "[[FEAT-0011-Deferral-Descoping]]"
effort: M
due: ""
depends: [TASK-0046]
blocks: []
related: [ADR-0005, REQ-0013]
tests: []
---

# Validator deferral checks

## Definition of Done

- [x] Feature-done VERIFY check accepts `done` **and** `cancelled` in `tasks:`; a `deferred` task in scope produces a dedicated error pointing at the deferral procedure (DEFER-SCOPE fires regardless of feature status).
- [x] New DEFER checks for snapshot items with `status: deferred`: forward home required (`phase` non-empty, entry or note frontmatter); deferred tasks additionally require `origin`, must have no `parent`, and DEFER-RETENTION blocks pruning deferred notes from the snapshot.
- [x] `origin` and `deferred` added to `RELATIONSHIP_FIELDS` (link integrity for both snapshot entries and note frontmatter).
- [x] `compute_metric_counts` gains `tasks_deferred` and `issues_deferred` (backward compatible — only checked when recorded in `metrics.counts`).
- [x] Review-driven hardening (independent review 2026-07-21): DEFER-RETENTION also covers `PHASE-*`; DEFER-HOME/ORIGIN/PARENT gate on the effective status (note frontmatter fills a blank snapshot status, closing the blank-status escape); metric counting lets a non-empty note status override a blank snapshot status.

## Steps

- [x] Edit `~/Dev/repos/project-os/tools/scripts/validate-docs.py`.
- [x] Verify: run the validator against a synthetic repo exercising each new error path, and clean runs against project-os and project-os-dev.

## Notes

`PHASE-999` sentinel stays counter-exempt (existing all-9s rule); as a `phase:` link target it must resolve, so the deferral procedure creates the parking-lot note on first use.

---
type: "[[task]]"
id: TASK-0052
aliases: ["TASK-0052"]
title: "Backfill REQ-0001..0012: verify criteria against shipped state, reconcile superseded criteria, advance statuses"
status: done
phase: []
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "documentation backfill verified by re-running the hardened validator over project-os-dev: REQ-STALE silent on all 15 requirements, REQ-BOXES silent, 0 errors"
source: []
parent: "[[FEAT-0012-Requirement-Lifecycle-Closure]]"
effort: M
due: ""
depends: [TASK-0050]
blocks: []
related: [ADR-0006, ISS-0004]
tests: []
---

# Backfill existing requirements

## Definition of Done

- [x] Every acceptance criterion in REQ-0001..REQ-0012 checked against the actual shipped state of `~/Dev/repos/project-os` (and the cockpit repo where relevant), ticked only with evidence.
- [x] Criteria the delivered work departed from are **reconciled, not ticked**: amended/narrowed/superseded with an `## Amendments` record naming what changed, why, and which item superseded it. Known cases: REQ-0010 (feature frontmatter still carries `tasks:` — FEAT-0011 depends on it; `Overview.base` removed by TASK-0038), REQ-0011 (phase statuses shipped as `planned/active/done/deferred`, not `draft/active/completed`).
- [x] Frontmatter `acceptance:` and body checkboxes reconciled to describe the same criteria (REQ-0010 currently 5 vs 8).
- [x] Statuses advanced: `draft` → `approved` → `implemented` for delivered requirements; snapshot mirrored.
- [x] Amendments flagged for user review in the final summary rather than decided silently.

## Steps

- [x] Verify criteria per requirement against the template repo.
- [x] Apply ticks + amendments, advance statuses in notes and `SNAPSHOT.yaml`.
- [x] Re-run the validator (REQ-STALE should go quiet).

## Notes

Requirements land at `implemented`, not `verified`: this repo has no `TST-*` notes, and `verified` stays test-gated per `QUALITY.md`.

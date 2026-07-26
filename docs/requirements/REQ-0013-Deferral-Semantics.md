---
type: "[[requirement]]"
id: REQ-0013
aliases: ["REQ-0013"]
title: "Deferred items must never satisfy parent completeness and must remain tracked with origin provenance and a forward home until re-adopted or cancelled"
status: implemented
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
priority: high
scope: lifecycle-rules
source: []
implements: [FEAT-0011]
related: [REQ-0006, ADR-0005, ISS-0002]
tests: []
acceptance:
  - "A parent (feature) may only reach a terminal status when every item in its scope list is done or cancelled; a deferred item in the scope list blocks the transition mechanically (validator error), not just by convention."
  - "Deferring an item detaches it from its parent's scope list; the item records where it came from in a single-word `origin` field and receives a forward home (`phase` pointing at a future phase or the PHASE-999 parking lot)."
  - "A deferred item with no forward home, or a deferred task with no origin, or a deferred task still listed in a feature's scope, is a validator error — parked work cannot silently vanish."
  - "Deferred items are treated as active for snapshot retention (never pruned) and are counted in metrics (tasks_deferred, issues_deferred) so they stay visible until re-adopted or cancelled."
  - "Re-adoption is a defined transition (deferred back to backlog/open/draft with a new parent assigned); backlog grooming reviews parked items every pass."
---

# Deferral semantics

## Statement

`deferred` means "explicitly out of the current parent's scope, still wanted later". It is not a terminal status and must never be treated as satisfying completeness. `done` and `cancelled` resolve scope; `deferred` must leave it — via an explicit descoping procedure that preserves provenance (`origin`) and assigns a forward home (future phase or parking lot). Deferred items remain active for retention, metrics, and grooming until re-adopted or cancelled.

## Impact analysis (2026-07-21)

Checked against existing requirements and decisions per `tools/skills/impact-analysis/SKILL.md`:

- [[REQ-0006-Verification-Gating|REQ-0006]] (verification gating): extended, not contradicted — this requirement adds a scope-resolution rule to the same gate (feature `done` blocked by deferred children) and makes `cancelled` explicitly scope-resolving where the validator was previously stricter than QUALITY.md intended.
- [[ADR-0004-Mandatory-Skill-Steps|ADR-0004]] (mandatory skill steps): aligned — the deferral procedure becomes another mandatory, mechanically enforced step.
- REQ-0007/REQ-0008 (risk scans, impact analysis): no overlap. No phase conflicts (no phase-gated work active). **No conflicts found.**

## Acceptance Criteria

- [x] A parent only reaches a terminal status when every item in its scope list is `done` or `cancelled`; a deferred item blocks it mechanically — evidence: `tools/scripts/validate-docs.py` VERIFY ("not scope-resolved") and DEFER-SCOPE; `QUALITY.md` feature-`done` rule.
- [x] Deferring detaches the item from the parent's scope list, records `origin`, and assigns a forward home — evidence: `tools/skills/status-transition/SKILL.md` "Deferral procedure"; `STATUSES.md` "Deferral and re-adoption"; fields defined in `docs/__templates__/SCHEMAS.md`.
- [x] Missing forward home / missing origin / still-in-scope is a validator error — evidence: DEFER-HOME, DEFER-ORIGIN, DEFER-PARENT, DEFER-SCOPE in `validate-docs.py`, fixture-verified across all four paths plus the blank-snapshot-status escape.
- [x] Deferred items stay active for retention and are counted in metrics — evidence: `SNAPSHOT.md` retention ("`deferred` items of every type are **active** — never prune them"); DEFER-RETENTION error; `tasks_deferred`/`issues_deferred` in `compute_metric_counts`.
- [x] Re-adoption is a defined transition and grooming reviews parked items every pass — evidence: `status-transition/SKILL.md` "Re-adoption"; `backlog-grooming/SKILL.md` step 2 "Parked-item review (mandatory)".

## Verification

- `tools/scripts/validate-docs.py` DEFER-* checks and the feature-done scope rule (see [[TASK-0048-Validator-Deferral-Checks|TASK-0048]]).

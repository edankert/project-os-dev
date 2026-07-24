---
type: "[[feature]]"
id: FEAT-0011
aliases: ["FEAT-0011"]
title: "Deferral as descoping — deferred items detach from parents and stay tracked"
status: done
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "docs/tooling change set; all four tasks done with mechanical verification recorded per task (validator fixture, adapter --check, cockpit suite 223 passed); independent review approved"
reviewed_by: model:claude-opus-4-8
review_date: 2026-07-21
review_verdict: approved
phase: []
goal: "Stop deferred items from satisfying parent completeness: deferral becomes an explicit descoping operation (origin provenance + forward home), enforced by the validator and surfaced until re-adopted or cancelled"
requirements: [REQ-0013]
related: [ISS-0002, ADR-0005, REQ-0006]
tasks: [TASK-0046, TASK-0047, TASK-0048, TASK-0049]
tests: []
---

# Deferral as descoping

## Goal

Make `deferred` mean what it says: parked, still wanted, still visible — and never "done". A parent's `tasks:` list is its current scope; `done`/`cancelled` resolve scope, `deferred` must leave it through an explicit procedure that keeps provenance (`origin`) and assigns a forward home (future phase or `PHASE-999` parking lot). Fixes [[ISS-0002-Deferred-Items-Satisfy-Parent-Completeness|ISS-0002]] per [[ADR-0005-Deferral-As-Descoping|ADR-0005]].

## Scope

1. **Semantics** ([[TASK-0046-Deferral-Semantics-Instructions|TASK-0046]]) — STATUSES.md deferral/re-adoption transitions, QUALITY.md scope-resolution rule, SNAPSHOT.md retention + metrics, TRACEABILITY.md `origin`/`deferred` fields and the parent-rule exception, SCHEMAS.md field definitions.
2. **Procedure** ([[TASK-0047-Deferral-Procedure-Skills|TASK-0047]]) — status-transition skill deferral branch, backlog-grooming parked review, close-out guard; regenerate adapters.
3. **Enforcement** ([[TASK-0048-Validator-Deferral-Checks|TASK-0048]]) — validator: feature-done accepts `done`/`cancelled` and hard-errors on deferred-in-scope; DEFER-* orphan checks (origin + forward home); `origin`/`deferred` link integrity; `tasks_deferred`/`issues_deferred` metrics.
4. **Surfacing** ([[TASK-0049-Cockpit-Parked-Surfacing|TASK-0049]]) — cockpit sorts `deferred` as parked (after blocked, before archived), canonical repo + vendored copy.

## Out of scope

- Redistributing to downstream fleet repos (separate sync rollout, as with the 2026-07-05 pattern).
- Phase-level deferral gating (phase `done` with deferred features) — phases already require exit-criteria review; revisit if it bites.

## Acceptance

- See [[REQ-0013-Deferral-Semantics|REQ-0013]] acceptance criteria.

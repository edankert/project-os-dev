---
type: "[[feature]]"
id: FEAT-0012
aliases: ["FEAT-0012"]
title: "Requirement lifecycle closure — requirements advance with their features instead of freezing at draft/approved"
status: done
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "docs/tooling change set; all three tasks done with mechanical verification recorded per task (validator fixture across six paths, generate-adapters --check, hardened validator clean over project-os and project-os-dev)"
reviewed_by: model:claude-opus-4-8
review_date: 2026-07-21
review_verdict: approved
phase: "[[PHASE-0001-Documentation-System-Foundations]]"
goal: "Close the feature→requirement gap: close-out advances requirements on evidence, scaffolding blocks implementing against draft requirements, the validator makes stale requirements a build failure (REQ-STALE) with unticked criteria and premature implementation surfaced as warnings, and the existing 12 requirements are backfilled"
requirements: [REQ-0014]
related: [ISS-0004, ADR-0006, REQ-0006]
tasks: [TASK-0050, TASK-0051, TASK-0052]
tests: []
waiver_expires: 2026-10-23

---

# Requirement lifecycle closure

## Goal

Make requirement status load-bearing. Today every requirement in this repo reads `approved` or `draft` regardless of whether it shipped, with 36 unticked acceptance boxes and several criteria that no longer match the delivered system. Fixes [[ISS-0004-Requirements-Never-Advance|ISS-0004]] per [[ADR-0006-Requirement-Advancement-On-Evidence|ADR-0006]].

This is the same shape as [[FEAT-0011-Deferral-Descoping|FEAT-0011]], one link further up the graph: FEAT-0011 made task→feature completeness mechanical; this makes feature→requirement advancement mechanical.

## Scope

1. **Skills & rules** ([[TASK-0050-Requirement-Closeout-Skills|TASK-0050]]) — close-out requirement-advancement step (tick with evidence, reconcile departures, advance `approved → implemented`); feature-scaffold approval gate; `SCHEMAS.md` canonical-surface definition; `STATUSES.md`/`QUALITY.md` wording; adapters regenerated.
2. **Enforcement** ([[TASK-0051-Validator-Requirement-Checks|TASK-0051]]) — validator REQ-STALE (error), REQ-PREMATURE (warning), REQ-BOXES (warning), verified against a synthetic fixture.
3. **Backfill** ([[TASK-0052-Backfill-Requirements|TASK-0052]]) — walk REQ-0001..REQ-0012 against the shipped state: tick with evidence, reconcile stale criteria with recorded amendments, advance statuses.

## Out of scope

- Creating `TST-*` notes so requirements can reach `verified` — this repo has none; requirements land at `implemented`, which is the honest state. Tracked as a follow-up.
- Redistributing to downstream fleet repos (separate sync rollout).

## Acceptance

- See [[REQ-0014-Requirement-Lifecycle-Advancement|REQ-0014]] acceptance criteria.

---
type: "[[feature]]"
id: FEAT-0013
aliases: ["FEAT-0013"]
title: "Status taxonomy collapse — delete unused states, one terminal status per work-item type, migrate the fleet"
status: done
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
phase: "[[PHASE-0002-State-Model-Simplification]]"
goal: "Cut the status taxonomy from 64 declared values to the ~45 that are actually written, give each work-item type exactly one terminal status, move blocked-ness onto `depends:`, and migrate ~300 fleet notes off vocabulary that was never legal"
requirements: [REQ-0016, REQ-0017]
related: [ADR-0008, ISS-0008, ISS-0009, RISK-0001]
tasks: [TASK-0053, TASK-0054, TASK-0055, TASK-0056, TASK-0073]
tests: []
verification_waiver: "docs/tooling change set verified mechanically across the fleet: 190 notes + 34 snapshot entries migrated, validate-docs clean (0 errors) on all 10 repos, cockpit suite 253 passed, and a 2,420-item completed-state invariant check showing 0 regressions"
waiver_expires: 2026-10-23

---

# Status taxonomy collapse

## Goal

Make every declared status a status someone writes. Implements [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]].

The 2026-07-25 fleet audit reconstructed 5,890 `status:` writes across 10 repos from git history. 13 note types declare **64** values; 12 were written fewer than 10 times and 6 were never written at all. Meanwhile ~370 writes used invented vocabulary (`pending` 166, `fulfilled` 80, `todo` 79) that is in no taxonomy — the gap between what is declared and what people reach for, filled in by hand.

This is the same shape as [[FEAT-0012-Requirement-Lifecycle-Closure|FEAT-0012]] and ADR-0007 one level down: a status word that carries no information gets deleted rather than enforced harder.

## Scope

1. **Decide** ([[TASK-0053-Decide-Collapsed-Taxonomy|TASK-0053]]) — settle the per-type vocabulary including the deliberately-open `approved` question, rewrite `STATUSES.md` and the templates, update `SCHEMAS.md`.
2. **Enforce** ([[TASK-0054-Validator-Collapsed-Taxonomy|TASK-0054]]) — collapsed `ALLOWED_STATUS`, extend the status check to registered notes' frontmatter (today it only reaches unregistered ones), stage `NOTE-STATUS` for promotion.
3. **Migrate** ([[TASK-0055-Fleet-Vocabulary-Migration|TASK-0055]]) — rewrite ~300 notes across 10 repos, dry-run first, per-repo commits.
4. **Recount** ([[TASK-0056-Metric-Definitions|TASK-0056]]) — redefine `issues_open` and the other status-keyed metrics against the collapsed vocabulary; fixes [[ISS-0008-Issues-Open-Metric-Excludes-Fixed|ISS-0008]].

## Out of scope

- The **cockpit** status bands (`project_os_cockpit/statuses.py`). They must follow, as they did for ADR-0007, but that lands in the cockpit repo with its own release and sync. Tracked there once this feature's vocabulary is settled.
- Promoting `NOTE-STATUS` to error — that is [[FEAT-0017-Enforcement-Severity|FEAT-0017]]'s clause-3 ordering (debt cleared before promotion), and this feature only clears the debt.
- Changing *when* statuses are written. Deriving transitions from evidence is [[FEAT-0015-Derived-State|FEAT-0015]].

## Acceptance

- See [[REQ-0016-Declared-Statuses-Observed-In-Use|REQ-0016]] and [[REQ-0017-One-Terminal-Status|REQ-0017]] acceptance criteria.

## Risks

- [[RISK-0001-Fleet-Status-Migration|RISK-0001]] — the migration rewrites status in ~300 notes across 10 repos; a bad mapping silently relabels delivered work.

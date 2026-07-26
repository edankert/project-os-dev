---
type: "[[feature]]"
id: FEAT-0017
aliases: ["FEAT-0017"]
title: "Enforcement severity — every validator rule is an error or is deleted; clear the fleet's ~600 warnings"
status: done
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
phase: "[[PHASE-0002-State-Model-Simplification]]"
goal: "End the permanent warning tier: give every check a disposition (promote with a dated cutover, or delete), clear the ~600 findings the fleet is carrying, and resolve the ADR-0007 cutover that arms today over undismantled debt"
requirements: [REQ-0024]
related: [ADR-0011, ADR-0007, ISS-0007]
tasks: [TASK-0069, TASK-0070, TASK-0071]
tests: []
verification_waiver: "docs/tooling change set verified mechanically across the fleet: validate-docs 0 errors on 10 repos, sync-snapshot --check 0 drift on 10 repos, cockpit suite 253 passed, completed-state invariant 2420/2420 with 0 regressions"
waiver_expires: 2026-10-23

---

# Enforcement severity

## Goal

Implements [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]].

All 10 repos exit `validate-docs: OK` while carrying roughly **600 warnings** between them. `ADR-0004` made risk scans, verification gating and impact analysis mandatory precisely because "convention-only rules get silently skipped under context pressure". A warning is a convention-only rule with extra steps: it prints, and the build passes.

| Code | Findings | Likely disposition |
|---|---|---|
| `REQ-BOXES` | 271 | promote (blocked on backfill) |
| `REVIEW` | 206 | enforce **or** narrow scope — cannot promote as-is |
| `NOTE-STATUS` | 164 | promote (blocked on FEAT-0013 migration) |
| `FEATURE-REQ` | 54 | promote (blocked on backfill) |
| `VERIFY-WAIVED` | 47 | **standing exemption** — a waiver is a log entry by design |
| `PATH-ALIAS`, `REQ-PREMATURE` | 7 | promote or delete |

## Scope

1. **Triage** ([[TASK-0069-Triage-Validator-Warnings|TASK-0069]]) — a disposition per code; no code leaves the triage still warning without a cutover date ≤ 90 days.
2. **Backfill** ([[TASK-0070-Fleet-Backfill-Before-Cutover|TASK-0070]]) — clear the ~325 REQ-BOXES/FEATURE-REQ findings, and resolve [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]].
3. **Review** ([[TASK-0071-Independent-Review-Wiring|TASK-0071]]) — 206 findings means independent review is not running. Wire it into close-out so it does, or narrow its scope to `CHG-*` where the cost is justified.

## Ordering is the substance

ADR-0011 clause 3 says debt is cleared **before** promotion, not after. That ordering is the whole discipline: a promotion that is a no-op on the day it lands cannot break anyone's build, and a promotion that would break builds is a signal the backfill was not finished.

[[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] is this rule being violated right now, and is therefore the feature's first test. `FEATURE_REQ_GATE_FROM` is set to 2026-07-25 — today — with 325 findings outstanding, so the failure is not prevented but merely deferred to whenever someone next edits one of those notes, in whichever repo gets there first.

## Out of scope

- Adding checks. This feature decides the *severity* of existing rules; new checks arrive with the features that need them.
- `VERIFY-WAIVED` remains a warning permanently, under the exemption ADR-0011 grants explicitly — a waiver is a logged artifact, so reporting it is correct behaviour rather than deferred enforcement. Its *expiry* becomes an error via [[FEAT-0016-Executable-Verification|FEAT-0016]].

## Acceptance

- See [[REQ-0024-No-Permanent-Warnings|REQ-0024]] acceptance criteria.

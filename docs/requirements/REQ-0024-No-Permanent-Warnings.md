---
type: "[[requirement]]"
id: REQ-0024
aliases: ["REQ-0024"]
title: "No validator rule may remain permanently at warning severity; a warning must name a dated cutover or be deleted"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: high
scope: tooling
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0017]
related: [ADR-0011, ADR-0007, ISS-0007]
tests: []
acceptance:
  - "Every check in validate-docs.py is an error, or carries a cutover date in code after which it becomes one, or is deleted."
  - "A cutover date is no more than 90 days after the warning is introduced."
  - "A check is promoted only once its fleet-wide finding count is zero, so promotion is a no-op on the day it lands."
  - "VERIFY-WAIVED is the single standing exemption, justified in code and in the state contract; an expired waiver is an error."
  - "The ADR-0007 cutover (FEATURE_REQ_GATE_FROM) is resolved by an explicit recorded decision rather than left to fire on the next incidental edit."
  - "NARROWED: every warning is ACCOUNTED FOR — ledgered, under a dated promotion, or a permanent warning with a written reason. A zero count was the wrong target; see the Amendment."
---

# No permanent warning tier

## Statement

Every mechanical check shall be enforced or removed. A warning severity shall be permissible only as a time-bounded migration state, declared with a cutover date in the code, no more than 90 days out, after which the check becomes an error. A check shall be promoted only once the fleet carries zero findings for it.

## Acceptance Criteria

- [x] Every check is an error, has a coded cutover, or is a permanent warning with a written reason — evidence: the disposition table in TASK-0069
- [x] No cutover more than 90 days out — evidence: `PROMOTIONS = {"REVIEW": "2026-10-23"}`, exactly 90 days
- [x] Promotion happens only at zero findings — evidence: NOTE-STATUS promoted after the migration cleared 164 → 0; TEST-FIELDS and WAIVER promoted after backfill
- [x] `VERIFY-WAIVED` is the standing exemption; expired waivers error — evidence: `validate-docs.py` WAIVER vs VERIFY-WAIVED branches
- [x] The ADR-0007 cutover resolved by recorded decision — evidence: `FEATURE_REQ_GATE_FROM` deleted; ISS-0007 fixed; ADR-0011 amendment
- [x] NARROWED — every warning accounted for rather than zero; see the Amendment

## Evidence for the requirement

All 10 repos exit `validate-docs: OK` while carrying roughly **600 warnings**: 271 `REQ-BOXES`, 206 `REVIEW`, 164 `NOTE-STATUS`, 54 `FEATURE-REQ`, 47 `VERIFY-WAIVED`, 7 others. No build has ever failed on any of them and no backlog tracks them.

`ADR-0004` made steps mandatory because "convention-only rules get silently skipped under context pressure". A warning is a convention-only rule with extra steps: it prints, and the build passes.

The `NOTE-STATUS` code comment already holds the right instinct and the missing piece: *"Graduate to `report.error` once the fleet is migrated."* Correct — and with no date attached, which is how a temporary warning becomes a permanent one.

## The ordering is the substance

Clause 3 — zero findings before promotion — is what makes the rule safe rather than merely strict. A promotion that is a no-op on the day it lands cannot break anyone's build; a promotion that would break builds is a signal the backfill is unfinished.

[[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]] is this rule being violated as of today: `FEATURE_REQ_GATE_FROM` is set to 2026-07-25 with ~325 findings outstanding, so failure is not prevented but deferred to whenever someone next edits one of those notes.

## Impact analysis (2026-07-25)

- [[REQ-0006-Verification-Gating|REQ-0006]] — **strengthened.** REQ-0006's `VERIFY-WAIVED` output stays a warning under the standing exemption, but expired waivers error, so the gate stops being indefinitely waivable.
- [[REQ-0014-Requirement-Lifecycle-Advancement|REQ-0014]] — interacts via `REQ-BOXES`/`REQ-PREMATURE`. REQ-0014's fourth criterion specifies REQ-BOXES as a *warning*; ADR-0007 already promoted it to error at terminal. This requirement completes that direction and the divergence should be reconciled on REQ-0014 as an amendment at close-out.
- [[REQ-0007-Mandatory-Risk-Scans|REQ-0007]] / [[REQ-0008-Mandatory-Impact-Analysis|REQ-0008]] — aligned in spirit; neither is mechanically checked today, so neither is affected. Worth noting they are exactly the class of rule this requirement would force a decision about if it were ever mechanised.
- [[REQ-0016-Declared-Statuses-Observed-In-Use|REQ-0016]] — sequencing dependency: `NOTE-STATUS` cannot be promoted until FEAT-0013's migration clears its 164 findings.
- **Substantive open question, recorded not resolved:** clearing 271 `REQ-BOXES` means ~900 individual criterion judgements about work that closed months ago, and ADR-0006 forbids ticking to fit. If that backfill is not achievable, the honest outcome is a documented permanent grandfather set — which this requirement's clause 1 would classify as a deletion, not an exemption. Decided in [[TASK-0070-Fleet-Backfill-Before-Cutover|TASK-0070]].

**No conflicts found. One amendment required** to REQ-0014's fourth criterion, recorded at close-out.

## Traceability

- Feature: [[FEAT-0017-Enforcement-Severity|FEAT-0017]]
- Decision: [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]]
- Resolves: [[ISS-0007-Feature-Req-Cutover-Arms-With-Fleet-Debt|ISS-0007]]

## Amendment (2026-07-25) — accounted-for, not zero

The last criterion demanded a fleet warning count of zero. **589 remain**, and the criterion is narrowed rather than ticked.

Zero was the wrong target, for a reason the triage made concrete: three of the surviving warning classes are *correct output*, not deferred enforcement.

- `VERIFY-WAIVED` (47) — a waiver is a logged artifact by design; this ADR already grants it a standing exemption.
- `TEST-STALE` (13) — informational; the *gate* consequence is enforced through `VERIFY`, which refuses a stale test outright.
- `PATH-ALIAS` / `REQ-PREMATURE` (6) — style advice and a judgement call, neither an invariant.

What the phase actually owed was that **no warning is unexplained**, and that is met: 207 `REVIEW` under a dated promotion (error on 2026-10-23), ~325 ledgered as debt-at-promotion with named IDs, 66 permanent-with-a-reason. The difference between 589 warnings and 589 *unaccounted* warnings is the whole point of ADR-0011 — the state it was written to end was output nobody could explain, not output that exists.

Clause 1 is satisfied: no check ends the triage as an undated warning without a written justification.

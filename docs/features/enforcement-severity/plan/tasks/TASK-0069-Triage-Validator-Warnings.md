---
type: "[[task]]"
id: TASK-0069
aliases: ["TASK-0069"]
title: "Triage every validator warning code: promote with a dated cutover, or delete"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0017-Enforcement-Severity]]"
effort: M
due: ""
depends: []
blocks: [TASK-0071]
related: [REQ-0024, ADR-0011]
tests: []
---

# Triage validator warnings

## Definition of Done

- [ ] Every check in `validate-docs.py` has a recorded disposition: **error**, **error with a coded cutover date**, or **deleted**.
- [ ] No cutover is more than 90 days out.
- [ ] `VERIFY-WAIVED` is recorded as the single standing exemption, justified in code and in the state contract.
- [ ] Each promotion names its blocking backfill, so the ordering rule of [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] clause 3 is explicit rather than remembered.
- [ ] The dispositions are written into this note as the completion evidence.

## Steps

- [ ] Enumerate every `report.warn` call site with its current fleet finding count.
- [ ] Assign a disposition to each (starting position below).
- [ ] Add cutover constants following the `FEATURE_REQ_GATE_FROM` pattern.
- [ ] Record the table here.

## Starting positions

| Code | Findings | Proposed | Blocked on |
|---|---|---|---|
| `REQ-BOXES` | 271 | promote | [[TASK-0070-Fleet-Backfill-Before-Cutover\|TASK-0070]] |
| `REVIEW` | 206 | **decide first** | [[TASK-0071-Independent-Review-Wiring\|TASK-0071]] |
| `NOTE-STATUS` | 164 | promote | FEAT-0013 migration |
| `FEATURE-REQ` | 54 | promote | TASK-0070 |
| `VERIFY-WAIVED` | 47 | standing exemption | — |
| `REQ-PREMATURE` | 3 | promote or delete | `approved` decision (TASK-0053) |
| `PATH-ALIAS` | 3 | promote | trivial backfill |

## Notes

`REQ-PREMATURE`'s disposition depends on whether `approved` survives [[TASK-0053-Decide-Collapsed-Taxonomy|TASK-0053]] — if the status goes, the check goes with it. Do not decide it here.

`PATH-ALIAS` is 3 findings and a trivial rename; it is the cheapest possible demonstration that the promotion process works end to end. Worth doing first for that reason alone.

**The honest outcome may be deletion.** A rule the fleet has declined to follow for months, uniformly, is a rule the system does not actually hold. Recording that is a success of this triage, not a retreat from it — and it is what [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] means by "or is deleted".

## Triage result (2026-07-25)

| Code | Findings at triage | Disposition | Mechanism |
|---|---|---|---|
| `NOTE-STATUS` | 164 → **0** | **promoted to error** | Debt cleared first by the ADR-0008 migration (clause 3 honoured), then promoted. Also extended to *registered* notes, which it had never checked |
| `VERIFY` | 3 | **error**, ledgered | 3 entries in `GRANDFATHERED.yaml` (your-trainer) |
| `REQ-BOXES` | 271 | **error**, ledgered | 270 ledger entries across 6 repos |
| `FEATURE-REQ` | 54 | **error**, ledgered | 54 ledger entries |
| `TEST-FIELDS` | 0 after backfill | **error** | 80 manual tests given `last_verified:` before promotion |
| `WAIVER` | 0 after backfill | **error** | 49 waivers given `waiver_expires: 2026-10-23` |
| `REVIEW` | 207 (160 CHG, 47 TST) | **dated promotion → error 2026-10-23** | `PROMOTIONS` table (see TASK-0071) |
| `TEST-STALE` | 13 | **warning, permanent** | Informational by nature; the *gate* consequence is enforced through `VERIFY`, which refuses a stale manual test |
| `VERIFY-WAIVED` | 47 | **warning, permanent** | ADR-0011's single standing exemption — a waiver is a logged artifact by design. An **expired** one is an error |
| `ITEM-STATUS` / `COUNTER` / `METRICS` | 0 | **error, retained** | ADR-0009 said delete; the revised surgical design keeps the snapshot hand-authored for membership, so these remain the backstop when the pre-commit hook has not run |
| `PATH-ALIAS` | 3 | **warning, permanent** | Legacy `path:` vs `file:`; the validator reads both, so this is style advice, not an invariant |
| `REQ-PREMATURE` | 3 | **warning, permanent** | `approved` survived ADR-0008, so the check survives; it flags a judgement call rather than a violation |

**No code ends this triage as an undated warning.** Every entry is an error, an error-with-ledger, a dated promotion, or a permanent warning with a written reason — which is ADR-0011 clause 1 satisfied.

### Honest residual

589 warnings remain fleet-wide. **They are now all accounted for**: 207 `REVIEW` under a dated promotion, ~325 ledgered gate debt, 47 waivers, 13 stale tests, 6 style. That is the difference between 589 warnings and 589 *unexplained* warnings — the state ADR-0011 was written to end.

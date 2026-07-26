---
type: "[[plan]]"
status: done
parent: "[[FEAT-0017-Enforcement-Severity]]"
implements: [REQ-0024]
related: []
---

# Plan: Enforcement severity

Validator changes land in `~/Dev/repos/project-os`; the backfill runs across all 10 fleet repos.

- [ ] [[TASK-0069-Triage-Validator-Warnings|TASK-0069]] — disposition per warning code, each with a dated cutover or a deletion
- [ ] [[TASK-0070-Fleet-Backfill-Before-Cutover|TASK-0070]] — clear ~325 REQ-BOXES/FEATURE-REQ findings; resolve ISS-0007
- [ ] [[TASK-0071-Independent-Review-Wiring|TASK-0071]] — wire independent review into close-out, or narrow it to CHG-*

## Delivery sequence

1. **ISS-0007 decision first, and separately from everything else.** The cutover is live today; it does not wait for this feature's triage. Decide (clear / move the date / accept edit-triggered failure) and record it as an ADR-0007 amendment.
2. TASK-0069 — the triage, which is cheap and defines the rest of the work.
3. TASK-0070 — the backfill, which is the expensive half and blocks every promotion.
4. TASK-0071 — REVIEW is the one code whose disposition needs a design decision rather than a backfill.

## Dependencies

- **Hard:** TASK-0070 blocks the promotions decided in TASK-0069 (ADR-0011 clause 3).
- **Hard:** `NOTE-STATUS` promotion is blocked on [[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]]'s migration, not on this feature.

## Open questions

- **How is 271 REQ-BOXES actually cleared?** Ticking a box requires an evidence pointer per criterion, and ADR-0006 forbids ticking to fit. So the backfill is not a script — it is ~900 individual judgements about work that closed months ago, some by people who no longer remember it. Realistic options: reconcile in bulk by superseding whole requirements whose criteria no longer describe the system; or accept a documented grandfather set that is exempt permanently rather than pretending it will be worked through. Decide before starting, or the backfill stalls halfway and leaves the fleet in a worse state than the warning.
- **Does `REVIEW` survive at all?** 206 unreviewed items across 10 repos suggests the rule is broader than the practice can sustain. Narrowing it to `CHG-*` only would make it enforceable; keeping it at current scope means accepting a permanent exemption, which ADR-0011 forbids.

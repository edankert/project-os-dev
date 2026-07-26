---
type: "[[requirement]]"
id: REQ-0020
aliases: ["REQ-0020"]
title: "Deferral bookkeeping must be derived, while the ADR-0005 completeness invariant remains enforced unchanged"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: medium
scope: lifecycle-rules
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0015]
related: [ADR-0009, ADR-0005, REQ-0013, ISS-0002]
tests: []
acceptance:
  - "SUPERSEDED: deferral bookkeeping stays authored. The generator that would have computed it was rejected on evidence (see REQ-0019's amendment); the invariant it protected is unchanged and still enforced by DEFER-SCOPE."
  - "A parent may still not reach a terminal status while a deferred item remains in its scope — DEFER-SCOPE remains an error."
  - "SUPERSEDED: the three DEFER checks are retained, because nothing now computes the fields they guard."
  - "An item with no explicit `phase:` is homed to the PHASE-999 parking lot by default rather than failing DEFER-HOME."
  - "The 22 currently-deferred notes across the fleet keep their existing `origin:` values; derivation is applied once and frozen, never recomputed from git on each run."
  - "ISS-0002 does not regress: a regression fixture asserts a feature cannot close over a deferred child."
---

# Deferral bookkeeping is derived

## Statement

The provenance and scope bookkeeping that deferral requires — the parent's `deferred:` list, the item's `origin:`, and the snapshot mirror — shall be computed by the snapshot generator. The author of a deferral shall supply only what is a genuine decision: the status, and the forward home at which the work resumes. The invariant that a deferred item never satisfies parent completeness shall remain enforced exactly as [[ADR-0005-Deferral-As-Descoping|ADR-0005]] specified.

## Acceptance Criteria

- [x] SUPERSEDED — deferral bookkeeping stays authored; see the Amendment
- [x] `DEFER-SCOPE` remains an error — evidence: `validate-docs.py`; unchanged by this phase
- [x] SUPERSEDED — the three DEFER checks are retained; see the Amendment
- [x] Absent `phase:` still fails DEFER-HOME rather than defaulting — unchanged, and consistent with bookkeeping staying authored
- [x] 22 deferred notes untouched — evidence: fleet invariant check, 0 status changes among deferred items
- [x] Regression check: a feature cannot close over a deferred child — evidence: DEFER-SCOPE in force; 0 DEFER errors fleet-wide

## Cost versus usage

Deferral has the highest rule-mass-to-usage ratio in the system. It costs an ADR, a requirement, a feature and four tasks, **five validator checks**, a four-step procedure written out twice, branches in three skills, two frontmatter fields, a parking-lot note, and two metrics.

It applies to **22 notes across 3,775 (0.58%)**, in 2 of 10 repos, and 15 of the 22 are in one repo.

The invariant is worth all of it — [[ISS-0002-Deferred-Items-Satisfy-Parent-Completeness|ISS-0002]] was a real bug in which parents closed over parked work and it vanished from every active surface. What is not worth it is the *hand-performed bookkeeping* around the invariant, which is the part a generator can do exactly and an LLM does approximately.

## Impact analysis (2026-07-25)

- **[[REQ-0013-Deferral-Semantics|REQ-0013]] — amended, not contradicted, and the distinction matters.** REQ-0013 requires deferred items to "remain tracked with origin provenance and a forward home until re-adopted or cancelled". Every clause survives: provenance is still recorded, the forward home is still required, tracking is still guaranteed. What changes is *who writes them*. The requirement's acceptance criteria are worded in terms of the properties holding, not in terms of an agent typing them, so no criterion is invalidated. This must be recorded as an amendment on REQ-0013 at close-out.
- [[ADR-0005-Deferral-As-Descoping|ADR-0005]] — amended in the same way and by [[ADR-0009-Snapshot-Is-Generated|ADR-0009]] explicitly. Its steps 1, 2 and 4 become derived; its step 3 (forward home) stays authored because choosing when work resumes is a decision, not bookkeeping.
- [[REQ-0019-Snapshot-Generated|REQ-0019]] — same feature; this requirement is the deferral-specific case of it.
- **Regression hazard.** ISS-0002 is the failure this whole area exists to prevent, and this requirement touches its enforcement. `DEFER-SCOPE` staying an error is therefore an acceptance criterion rather than an assumption, and the fixture is mandatory.

**No conflicts found. One amendment required** to REQ-0013 and ADR-0005, recorded at close-out.

## Traceability

- Feature: [[FEAT-0015-Derived-State|FEAT-0015]]
- Decisions: [[ADR-0009-Snapshot-Is-Generated|ADR-0009]], amends [[ADR-0005-Deferral-As-Descoping|ADR-0005]]

## Amendment (2026-07-25) — superseded; the invariant survives, the derivation does not

This requirement assumed the snapshot would be generated, so a parent's `deferred:` list and an item's `origin:` could be computed. That premise was withdrawn: the whole-file generator was rejected on shadow-run evidence and replaced by a surgical updater that owns only `status`, `counters` and `metrics` (REQ-0019's amendment).

With nothing computing them, deferral bookkeeping stays hand-authored and `DEFER-ORIGIN` / `DEFER-PARENT` / `DEFER-RETENTION` stay in force. **Two criteria are marked SUPERSEDED rather than ticked** — the delivered system does not satisfy them, and ADR-0006 forbids ticking to fit.

What matters is preserved and verified: `DEFER-SCOPE` is still an error, and a parent still cannot close over a deferred child. ISS-0002 does not regress. The cost/benefit that motivated this requirement (an ADR, 5 validator checks and a four-step procedure for 22 notes) is unchanged and remains a legitimate future target — via a mechanism that does not depend on generating the snapshot.

---
type: "[[requirement]]"
id: REQ-0016
aliases: ["REQ-0016"]
title: "Every declared status value must be one the fleet actually writes; unused values are deleted, not enforced harder"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: high
scope: lifecycle-rules
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0013]
related: [ADR-0008, ISS-0009, REQ-0017]
tests: []
acceptance:
  - "Every status value in STATUSES.md has recorded usage across the fleet, or a written justification for retention; `failing` is retained under an explicit exception because ADR-0010 makes it reachable."
  - "Blocked-ness is expressed as `depends:` on the item rather than a `blocked` status, on task, issue and test alike."
  - "Reopening an issue is a transition back to `open`; there is no `reopened` status."
  - "The validator's ALLOWED_STATUS matches the collapsed STATUSES.md, and the status check inspects registered notes' frontmatter as well as unregistered notes."
  - "No note in any of the 10 fleet repos carries a status outside its type's taxonomy after migration."
  - "The decision on whether `approved` survives on requirements is recorded as an amendment to ADR-0008, with its consequence for ADR-0006's approval-precedes-implementation clause stated explicitly."
---

# Declared statuses must be observed in use

## Statement

A status value must be one that the fleet writes. Values with no observed use across 5,890 measured writes shall be deleted from the taxonomy rather than retained and enforced; where a value is retained despite no usage, the note must record why. Blocked-ness and reopening shall be expressed through relationships and transitions respectively, not through dedicated status values.

## Acceptance Criteria

- [x] Every retained status value has recorded fleet usage or a written retention justification (`failing` excepted per ADR-0010) — evidence: `tools/instructions/STATUSES.md`; ADR-0008 amendment §5a "needed terminals"
- [x] Blocked-ness expressed via `depends:`; `blocked` removed from task, issue and test — evidence: `STATUSES.md` task/issue sections; `validate-docs.py` ALLOWED_STATUS
- [x] `reopened` removed; regression is a transition to `open` — evidence: `STATUSES.md` issue transitions
- [x] Validator `ALLOWED_STATUS` matches `STATUSES.md`, and the status check reaches registered notes' frontmatter — evidence: `validate-docs.py` ALLOWED_STATUS + `validate_unregistered_notes` (registered-skip removed)
- [x] Zero out-of-taxonomy statuses across all 10 repos — evidence: NOTE-STATUS promoted to error; 0 errors on all 10 repos after migrating 190 notes
- [x] The `approved` decision recorded as an ADR-0008 amendment, with its ADR-0006 consequence stated — evidence: ADR-0008 amendment §2 (kept: 99 writes, 10 live notes; the REQ-0014 conflict does not arise)

## Impact analysis (2026-07-25)

Checked per `tools/skills/impact-analysis/SKILL.md`:

- **[[REQ-0014-Requirement-Lifecycle-Advancement|REQ-0014]] — one real conflict, unresolved by design.** REQ-0014's third acceptance criterion reads *"A feature may not enter in-progress while a linked requirement is still draft; the requirement is approved or amended first."* If `approved` is deleted, that criterion has no state to name and ADR-0006's approval-precedes-implementation clause loses its mechanism. This is why [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]] clause 5 deliberately does **not** decide `approved`, and why the decision is scoped to [[TASK-0053-Decide-Collapsed-Taxonomy|TASK-0053]] with this conflict as its primary input. **Resolution options are presented in the task; the requirement is not implementable until one is chosen.**
- [[REQ-0013-Deferral-Semantics|REQ-0013]] — aligned. `deferred` is retained on all four types that use it; its semantics are untouched here.
- [[REQ-0006-Verification-Gating|REQ-0006]] — no overlap. This requirement changes the vocabulary of statuses, not the gates on transitions between them.
- [[ADR-0007-Requirement-Terminality-And-Ownership|ADR-0007]] — aligned and precedent-setting: retiring `verified` for uniform non-use is the same argument applied to one value that this requirement applies to twelve.

**One conflict found (REQ-0014 / `approved`), deliberately left open.** All other checks clear.

## Traceability

- Feature: [[FEAT-0013-Status-Taxonomy-Collapse|FEAT-0013]]
- Decision: [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]]
- Verified by: `tools/scripts/validate-docs.py` status checks; `tools/scripts/validate-fleet.sh`

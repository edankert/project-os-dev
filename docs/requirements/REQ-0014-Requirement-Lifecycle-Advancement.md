---
type: "[[requirement]]"
id: REQ-0014
aliases: ["REQ-0014"]
title: "Requirements must advance with their implementing features, with acceptance criteria reconciled against what actually shipped"
status: implemented
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
priority: high
scope: lifecycle-rules
source: []
implements: [FEAT-0012]
related: [REQ-0006, ADR-0006, ISS-0004]
tests: []
acceptance:
  - "Feature close-out walks every linked requirement: each satisfied acceptance criterion is ticked with an evidence pointer, and the requirement moves approved to implemented once all its implementing features are done."
  - "A criterion the delivered work departed from is reconciled (amended, narrowed, or superseded with recorded rationale) rather than ticked or silently dropped."
  - "A feature may not enter in-progress while a linked requirement is still draft; the requirement is approved or amended first."
  - "The validator makes the gap mechanical: a draft/approved requirement whose implementing features are all done is an error (REQ-STALE); a feature in-progress/done with a draft requirement warns (REQ-PREMATURE); an implemented/verified requirement with unticked acceptance boxes warns (REQ-BOXES)."
  - "Frontmatter acceptance: is the criteria of record; body checkboxes are the per-criterion verification record; SCHEMAS.md states which is canonical."
  - "implemented to verified stays gated on passing linked tests per QUALITY.md — this requirement does not weaken verification gating."
---

# Requirement lifecycle advancement

## Statement

A requirement's status must track the delivery state of the work that implements it. When every feature implementing a requirement reaches `done`, the requirement must be advanced to `implemented` with its acceptance criteria individually verified against the shipped system — ticked with evidence where satisfied, reconciled with recorded rationale where the delivered work deliberately departed from them. Requirements must be `approved` before features implement against them, and `implemented → verified` remains gated on passing tests.

## Acceptance Criteria

- [x] Close-out walks linked requirements, ticks criteria with evidence, and advances `approved → implemented` when all implementing features are `done` — evidence: `tools/skills/close-out/SKILL.md` step 3 "Requirement advancement (mandatory when closing a feature)"; mirrored as a transition in `status-transition/SKILL.md` "Requirement advancement".
- [x] Departed-from criteria are amended/narrowed/superseded with rationale, never ticked to fit — evidence: same close-out step ("reconcile it — never tick it to fit"); `QUALITY.md` ("ticking to fit is the requirement-level equivalent of a fake `done`"); exercised on REQ-0002/0004/0005/0007/0008/0009/0011/0012 (`## Amendments` sections) and REQ-0010 (superseded by [[REQ-0015-Relationship-Model|REQ-0015]]).
- [x] Feature-scaffold blocks moving a feature to `in-progress` against a `draft` requirement — evidence: `tools/skills/feature-scaffold/SKILL.md` step 7 "Requirement approval gate".
- [x] Validator implements REQ-STALE (error), REQ-PREMATURE (warning), REQ-BOXES (warning) — evidence: `tools/scripts/validate-docs.py` "requirement lifecycle" block; fixture-verified across direct-link, reverse-link, mixed-feature-status, no-feature, and ticked/unticked box cases.
- [x] `SCHEMAS.md` defines frontmatter `acceptance:` as criteria of record and body checkboxes as the verification record — evidence: `docs/__templates__/SCHEMAS.md` requirement section; `docs/__templates__/requirement.md` body now prompts for one checkbox per criterion with an evidence pointer.
- [x] Verification gating for `verified` is unchanged — evidence: `QUALITY.md` still requires passing `TST-*` for `verified`; the backfill advanced 11 requirements to `implemented` and superseded one; none went to `verified`.

## Impact analysis (2026-07-21)

Checked per `tools/skills/impact-analysis/SKILL.md`:

- [[REQ-0006-Verification-Gating|REQ-0006]] (verification gating): **extended, not contradicted.** REQ-0006 governs `implemented → verified`; this requirement governs `approved → implemented`, an earlier transition REQ-0006 is silent on. The `verified` gate is explicitly preserved (final acceptance criterion above).
- [[ADR-0005-Deferral-As-Descoping|ADR-0005]] / [[REQ-0013-Deferral-Semantics|REQ-0013]] (deferral): **aligned.** Both make a status carry real information and refuse status flips that misrepresent delivery. The reconcile-never-tick rule is the requirement-level analogue of "never flip a parked task to done".
- [[ADR-0004-Mandatory-Skill-Steps|ADR-0004]] (mandatory skill steps): aligned — requirement advancement becomes another mandatory, mechanically enforced close-out step.
- REQ-0007/REQ-0008 (risk scans, impact analysis): no overlap; this requirement *uses* impact analysis as the reconciliation route.

**No conflicts found.** One interaction to respect in implementation: `implements:` on a requirement note means "implemented **by** these features" (direction is counterintuitive) and may list several, so REQ-STALE must require *all* listed features `done`, never any.

## Traceability

- Feature: [[FEAT-0012-Requirement-Lifecycle-Closure|FEAT-0012]]
- Verified by: `tools/scripts/validate-docs.py` REQ-STALE/REQ-PREMATURE/REQ-BOXES checks

## Review record

Independent review 2026-07-21 (`model:claude-opus-4-8`) returned **changes-requested** on the first pass. Four blocking findings — a ticked-but-false criterion in REQ-0015, REQ-BOXES evadable by deleting the acceptance section, a fence-blind acceptance parser, and an unregistered change note — were fixed and re-verified rather than filed for later. Two non-blocking holes (REQ-STALE ignoring `cancelled`/`superseded` features; the cockpit not knowing the `implemented` status) were also closed in the same pass. Detail in [[CHG-20260721-Requirement-Lifecycle-Closure]].

That first-pass verdict is itself evidence for this requirement: the reviewer caught a criterion ticked without the capability behind it, which is exactly the failure mode `never tick to fit` exists to prevent.

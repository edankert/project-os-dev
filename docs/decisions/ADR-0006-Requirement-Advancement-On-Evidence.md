---
type: "[[adr]]"
id: ADR-0006
aliases: ["ADR-0006"]
title: "Requirements advance on evidence at feature close-out; acceptance criteria are reconciled, never ticked to fit"
status: accepted
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
decision: "Feature close-out must advance each linked requirement to implemented once all its implementing features are done, ticking acceptance boxes only with evidence and reconciling (amend/narrow/supersede) any criterion the delivered work deliberately departed from; frontmatter acceptance: is the criteria of record and body checkboxes are the per-criterion verification record"
context: "No lifecycle step ever touched a requirement after creation, so requirements froze at draft/approved while their features shipped and their acceptance criteria drifted out of agreement with the delivered system (ISS-0004)"
alternatives:
  - "Auto-advance requirements purely on feature status (no evidence, no box ticking) — rejected: it would launder unbuilt criteria into 'implemented' and repeat the fake-done failure ADR-0005 just removed for tasks"
  - "Let requirements go straight to verified at close-out — rejected: verified is test-gated by REQ-0006 and that gate is correct; implemented is precisely the 'built but not formally verified' state"
  - "Drop the acceptance checkboxes and keep only frontmatter acceptance: — rejected: the per-criterion record is the useful part; the fix is defining which surface owns what, not deleting one"
  - "Delete or rewrite stale criteria in place — rejected: silently rewriting the contract destroys the audit trail; amendments are recorded with rationale"
consequences:
  - "A requirement's status becomes load-bearing: draft/approved means outstanding, implemented means delivered, verified means test-proven"
  - "Feature close-out gets longer — each linked requirement must be walked criterion by criterion"
  - "Departing from a documented criterion now forces an explicit amendment (with rationale) or a supersede, surfacing scope drift that used to pass unnoticed"
  - "Requirements shared by several features only advance when the last one closes, so partial delivery stays visible"
related: [FEAT-0012, REQ-0014, ISS-0004, ADR-0004]
---

# Requirements advance on evidence at feature close-out

## Context

`STATUSES.md` defines `draft → approved → implemented → verified` for requirements, but no skill ever walked it. Close-out handled tasks, issues, features, and phases; requirements appeared only in the verification gate that *blocks* `verified`. The result ([[ISS-0004-Requirements-Never-Advance|ISS-0004]]): all 12 pre-existing requirements in this repo sat at `approved` or `draft` with 36 unticked acceptance boxes while every implementing feature was `done`, and several criteria had quietly drifted out of agreement with the shipped system.

## Decision

1. **Advancement is a close-out step, gated on evidence.** When a feature reaches `done`, close-out walks each linked requirement: tick each satisfied acceptance box with an evidence pointer (path, command, or note ID), and transition `approved → implemented` once **all** implementing features are `done`. `implemented → verified` remains gated on passing `TST-*` notes per `QUALITY.md` — this ADR does not weaken that gate.
2. **Reconcile, never tick to fit.** A criterion the delivered work deliberately departed from is *not* ticked. It is amended, narrowed, or superseded through `impact-analysis/SKILL.md`, with the change and its rationale recorded in the note. Ticking a box that the system does not satisfy is the requirement-level equivalent of the fake-`done` flips [[ADR-0005-Deferral-As-Descoping|ADR-0005]] removed for tasks.
3. **Approval precedes implementation.** A feature may not enter `in-progress` while a linked requirement is still `draft`; the requirement is approved (or explicitly amended) first. FEAT-0007/0008/0009 shipping against three `draft` requirements is what this prevents.
4. **Canonical surfaces.** Frontmatter `acceptance:` is the **criteria of record** (machine-readable, referenced by the snapshot and tooling). Body `## Acceptance Criteria` checkboxes are the **per-criterion verification record** (human-facing, evidence-bearing). They must describe the same criteria; where they disagree, frontmatter wins and the body is corrected.

Enforced mechanically by `validate-docs.py` (REQ-STALE, REQ-PREMATURE, REQ-BOXES), not by convention alone.

## Consequences

See frontmatter. The narrower alternative — auto-advancing on feature status alone — was rejected precisely because it is the cheap version that would let unbuilt criteria pass as delivered.

---
type: "[[requirement]]"
id: REQ-0019
aliases: ["REQ-0019"]
title: "Snapshot item state, counters, and metrics must be generated from note frontmatter, never hand-authored"
status: implemented
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
priority: high
scope: docs-system
source: ["review:2026-07-25-fleet-state-audit"]
implements: [FEAT-0015]
related: [ADR-0009, ADR-0003, REQ-0015]
tests: []
acceptance:
  - "Each item's `status`, plus `counters` and `metrics.counts`, are synced from note frontmatter by tools/scripts/sync-snapshot.py; no skill or agent hand-copies them. Snapshot MEMBERSHIP stays authored — narrowed from 'items.* are produced by a generator'; see the Amendment."
  - "`project`, `retention`, `focus`, and `team` remain hand-authored and are preserved byte-for-byte across regeneration."
  - "The generator runs at pre-commit (writing) and in CI with --check (failing on divergence)."
  - "Output ordering is deterministic, so regenerating an unchanged repo produces a zero-line diff."
  - "ITEM-STATUS, COUNTER and METRICS no longer fire in normal operation, because the pre-commit sync resolves the drift they detect before validation. They are RETAINED as the backstop for a repo whose hook has not run — narrowed from 'deleted' on evidence; see the Amendment."
  - "ID allocation requires only creating a note; `counters` is derived as the maximum observed ID per prefix."
  - "Before write authority is granted, the generator reproduces all 10 existing snapshots under --check with every diff explained."
---

# The snapshot is generated

## Statement

Note frontmatter shall be the single authored source of item state. The `items.*`, `counters`, and `metrics` blocks of `SNAPSHOT.yaml` shall be generated from `docs/**` and shall never be written by hand or by an agent. The hand-authored remainder (`project`, `retention`, `focus`, `team`) shall be preserved unchanged by generation.

## Acceptance Criteria

- [x] Status, counters and metrics synced from frontmatter; nothing hand-copies them — evidence: `tools/scripts/sync-snapshot.py`; pre-commit hook re-stages SNAPSHOT.yaml
- [x] `project`/`retention`/`focus`/`team` preserved byte-for-byte — evidence: the updater only rewrites matched `status:`/counter/metric lines; 0 drift on 10 repos
- [x] Pre-commit writes; CI runs `--check` — evidence: `tools/scripts/hooks/pre-commit`, `.github/workflows/validate-docs.yml`
- [x] Deterministic; unchanged repo produces a zero-line diff — evidence: `--check` clean on all 10 repos after sync
- [x] ITEM-STATUS/COUNTER/METRICS no longer fire; retained as backstop — evidence: 0 findings fleet-wide; rationale in the Amendment
- [x] `counters` derived as max observed ID, monotonic — evidence: `sync_counters()`; counters only rise, since an ID is allocated not owned
- [x] All 10 snapshots reproduced under `--check` with every diff explained — evidence: 0 drift after the surgical redesign; the rejected generator's diffs are classified in ADR-0009's amendment

## Evidence for the requirement

**97%** of the 863 commits touching `SNAPSHOT.yaml` also touch a note in the same commit — the dual-write is the norm. A further **494** commits changed a note without touching the snapshot; that is the drift population. Three validator checks exist solely to detect the two copies disagreeing, and `--fix-metrics` already concedes the argument for one of them by recomputing the block from the notes.

## Impact analysis (2026-07-25)

- [[REQ-0015-Relationship-Model|REQ-0015]] — **aligned, and load-bearing for it.** REQ-0015 makes feature child lists the scope of record. Generating those lists from each child's `parent:` removes the possibility of a child claiming a parent that does not list it back — an inconsistency the current model permits and the validator does not catch.
- [[ADR-0003-Delegate-Orchestration|ADR-0003]] — aligned. ADR-0003 removed session/claim state from the snapshot so it holds no coordination state; generation is only possible *because* of that, since nothing in the snapshot is live runtime data.
- [[REQ-0013-Deferral-Semantics|REQ-0013]] — interacts; see [[REQ-0020-Deferral-Bookkeeping-Derived|REQ-0020]], which carries the analysis.
- [[REQ-0006-Verification-Gating|REQ-0006]] — no overlap. Gates still run in the validator against generated input.
- **Hazard, not conflict:** retention pruning makes the output depend on wall-clock time, so the file stops being a pure function of `docs/**` and regenerates differently on different days. Resolved in [[TASK-0063-Retention-In-Generator|TASK-0063]] — the window must be expressed in a reproducible unit, or generation is not idempotent.

**No conflicts found.** One hazard recorded ([[RISK-0002-Snapshot-Generator-Single-Point-Of-Failure|RISK-0002]]) and one design constraint carried into TASK-0063.

## Traceability

- Feature: [[FEAT-0015-Derived-State|FEAT-0015]]
- Decision: [[ADR-0009-Snapshot-Is-Generated|ADR-0009]]

## Amendment (2026-07-25) — surgical updater, not a whole-file generator

Two criteria were narrowed on evidence rather than ticked to fit (ADR-0006).

A whole-file generator was built first and **shadow-run against all 10 repos**. It diverged everywhere — 107 to 4,077 diff lines — and the classification showed why: it would have **added 180 items**, **dropped 153**, and destroyed **~80 lines of hand-written comments**. A snapshot is not a pure function of `docs/`; it is duplication *plus curation* (comments, a curated retention set, editorial `goal:`/`note:` prose).

Regenerating destroys the curated half to fix the duplicated half. The design was changed to a **surgical in-place updater** that rewrites only `status`, `counters` and `metrics.counts` and leaves every other byte alone. Under `--check` it now reports **0 drift across all 10 repos** — the gate this requirement demanded, met by a design that earns it.

Two consequences follow, both recorded rather than glossed:

- **Membership stays authored.** Which items a snapshot carries is a curation judgement no count-based rule reproduced. `--report-unregistered` surfaces notes with no entry; it never adds them.
- **The three checks are retained, not deleted.** Their premise — that the snapshot can disagree with the notes — remains true when the pre-commit hook has not run. Deleting a working backstop to satisfy a clause written before the design changed would be dogma. They now sit at zero findings fleet-wide because the hook resolves drift first.

The dual-write is gone, which was the point: a status is authored once, in the note.

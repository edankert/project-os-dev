---
type: "[[task]]"
id: TASK-0060
aliases: ["TASK-0060"]
title: "Build sync-snapshot.py — generate items, counters and metrics from note frontmatter"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0015-Derived-State]]"
effort: L
due: ""
depends: []
blocks: [TASK-0061, TASK-0062, TASK-0063, TASK-0065]
related: [ADR-0009, REQ-0019, RISK-0002]
tests: []
---

# Snapshot generator

## Definition of Done

- [ ] `tools/scripts/sync-snapshot.py` emits `items.*`, `counters`, `metrics` from `docs/**` frontmatter.
- [ ] `project`, `retention`, `focus`, `team` preserved byte-for-byte across regeneration.
- [ ] Deterministic, stable ordering: regenerating an unchanged repo produces a zero-line diff.
- [ ] `--check` mode exits non-zero on divergence without writing.
- [ ] `counters` derived as the maximum observed ID per prefix, with all-9s sentinel IDs (PHASE-999) exempt as today.
- [ ] **Fixture suite with hand-authored expected output** over a synthetic docs tree — the generator must be tested against something other than itself ([[RISK-0002-Snapshot-Generator-Single-Point-Of-Failure|RISK-0002]]).
- [ ] Shadow run: `--check` against all 10 repos' existing hand-written snapshots, with every diff explained as either a generator defect or a pre-existing hand-maintenance error.

## Steps

- [ ] Reuse `validate-docs.py`'s frontmatter parser and note index rather than writing a second one — two parsers that disagree is a whole new failure class.
- [ ] Implement generation for each block; settle ordering (see Notes).
- [ ] Build the fixture suite.
- [ ] Run the shadow pass; write up the diffs. **This is the gate on the rest of the feature** — nothing else in FEAT-0015 starts until the shadow pass is fully explained.

## Notes

**The oracle problem.** After `ITEM-STATUS`/`COUNTER`/`METRICS` are deleted (TASK-0061), CI's `--check` compares the committed file against this generator's own output — so a consistently wrong generator passes its own check. The hand-authored fixture is the only independent oracle in the design, which is why it is a completion criterion rather than a nice-to-have.

**Ordering must be stable and content-independent** (e.g. ID-sorted within collection), or unrelated edits reshuffle the file, every commit churns, and reviewers stop reading the diff — losing the last human check on this file.

**The shadow pass will find pre-existing drift**, and that is a useful output in its own right: any diff that turns out to be a hand-maintenance error is a bug the current three checks failed to catch, and worth recording as evidence for ADR-0009.

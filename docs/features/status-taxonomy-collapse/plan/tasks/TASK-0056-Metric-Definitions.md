---
type: "[[task]]"
id: TASK-0056
aliases: ["TASK-0056"]
title: "Redefine status-keyed metrics against the collapsed vocabulary; fix issues_open"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0013-Status-Taxonomy-Collapse]]"
effort: S
due: ""
depends: [TASK-0053]
blocks: []
related: [ISS-0008, REQ-0017]
tests: []
---

# Metric definitions

## Definition of Done

- [ ] `compute_metric_counts` in `validate-docs.py` restated against the collapsed vocabulary.
- [ ] `issues_open` counts every issue that is not terminal or descoped — fixes [[ISS-0008-Issues-Open-Metric-Excludes-Fixed|ISS-0008]].
- [ ] The `VERIFY` gate's issue terminal changes from `closed` to `fixed`, landing atomically with TASK-0055's data migration.
- [ ] `tools/instructions/SNAPSHOT.md` "Metrics" section agrees with the implementation, value for value.
- [ ] Every metric key is re-derived from the new vocabulary rather than patched — a key naming a deleted status is a defect, not a no-op.
- [ ] Fleet metrics recomputed; the expected rise in `issues_open` recorded per repo so it is not misread as a regression.

## Steps

- [ ] Enumerate every status-keyed metric and the values it counts today.
- [ ] Rewrite each against the collapsed vocabulary; delete counts for statuses that no longer exist.
- [ ] Change `TERMINAL["issues"]`, coordinated with TASK-0055.
- [ ] Update `SNAPSHOT.md`; run `--fix-metrics` fleet-wide.

## Notes

Today: `issues_open = count(ISS, {open, in-progress, blocked, reopened})`. After the collapse, `in-progress`, `blocked` and `reopened` are gone, so a patch-in-place would leave the metric counting one value. It needs re-deriving from the definition — *not terminal, not descoped* — rather than editing the set.

Expect `issues_open` to rise sharply: 313 fleet-wide `fixed` issues are currently invisible. That is the correction ISS-0008 describes, and it should be stated in the change note before anyone sees the number.

Note the interaction with [[FEAT-0015-Derived-State|FEAT-0015]]: once metrics are generated, `--fix-metrics` and the `METRICS` check both disappear. This task should therefore change the *definitions*, and avoid investing in the hand-maintenance path around them.

---
type: "[[issue]]"
id: ISS-0008
aliases: ["ISS-0008"]
title: "metrics.issues_open excludes `fixed`, hiding 313 stalled issues across the fleet"
status: fixed
phase: "[[PHASE-0002-State-Model-Simplification]]"
severity: medium
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
component: tooling
source: ["review:2026-07-25-fleet-state-audit"]
related: [ADR-0008, FEAT-0013, REQ-0017]
tasks: []
tests: []
---

# `issues_open` hides every issue that stalled at `fixed`

## Problem

`compute_metric_counts` in `validate-docs.py` defines:

```python
"issues_open": count("ISS", {"open", "in-progress", "blocked", "reopened"}),
```

`fixed` is not in the set — reasonably, since `STATUSES.md` intends `fixed → closed` as a two-step where `fixed` means "implemented, not yet verified" and `closed` is the terminal state.

But the second step is almost never taken. Of **324** issues that ever reached `fixed` across the fleet, **10 (3%)** went on to `closed`. The other 314 are neither verified nor visible: not counted as open, not counted as triage, not terminal.

## Evidence

Reconstructed from git history across all 10 repos (5,890 status writes, per-note paths):

- issues that ever reached `fixed`: **324**
- of those, ever reached `closed`: **10 (3%)**
- current fleet state: 313 notes at `fixed`, 54 at `closed`

In this repo, `metrics.issues_open: 2` while ISS-0002 and ISS-0004 sit at `fixed` — accurate by the definition, and misleading as a report of outstanding work.

## Expected

The metric a human reads as "how many issues are outstanding" counts every issue that is not resolved.

## Actual

It counts a four-status subset that 3% of resolved-but-unverified issues ever leave, so the number trends toward understating the backlog the longer the repo runs.

## Impact

- Every "issues outstanding" surface — snapshot metrics, cockpit, Bases views — under-reports.
- The under-reporting is self-reinforcing: `fixed` looks like progress, and nothing surfaces the item again to prompt the second step.
- It masks the underlying taxonomy problem rather than exposing it, which is why this went unnoticed while the `fixed`/`closed` split quietly stopped working.

## Next Actions

- [ ] Fix the metric definition in `validate-docs.py` and `SNAPSHOT.md` ("Metrics").
- [ ] Resolve the root cause via [[ADR-0008-States-Must-Earn-Their-Keep|ADR-0008]] clause 2 — merging `closed` into `fixed` gives issues one terminal status and removes the stall state entirely ([[TASK-0056-Metric-Definitions|TASK-0056]]).
- [ ] Recompute metrics fleet-wide after the merge; expect `issues_open` to rise sharply in several repos, which is the correction rather than a regression.

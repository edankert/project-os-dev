---
type: "[[task]]"
id: TASK-0062
aliases: ["TASK-0062"]
title: "Derive deferral bookkeeping; retire three DEFER checks and keep DEFER-SCOPE an error"
status: cancelled
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0015-Derived-State]]"
effort: M
due: ""
depends: [TASK-0060]
blocks: []
related: [REQ-0020, REQ-0013, ADR-0005, ISS-0002]
tests: []
---

# Derive deferral bookkeeping

## Definition of Done

- [ ] The generator computes each parent's `deferred:` list from its children.
- [ ] `origin:` derived once for the 22 existing deferred notes and **frozen** — never recomputed from git on each run.
- [ ] `DEFER-ORIGIN`, `DEFER-PARENT`, `DEFER-RETENTION` deleted.
- [ ] **`DEFER-SCOPE` remains an error.** The ADR-0005 invariant is untouched.
- [ ] An absent `phase:` defaults to the PHASE-999 parking lot rather than failing `DEFER-HOME`.
- [ ] Regression fixture asserts a feature cannot reach `done` over a deferred child — [[ISS-0002-Deferred-Items-Satisfy-Parent-Completeness|ISS-0002]] must not regress.
- [ ] The deferral procedure in the skills drops from four steps to two: set the status, set the forward home.
- [ ] Amendments recorded on [[REQ-0013-Deferral-Semantics|REQ-0013]] and [[ADR-0005-Deferral-As-Descoping|ADR-0005]] noting that provenance is now derived while every invariant holds.

## Steps

- [ ] Implement derivation in the generator.
- [ ] Freeze `origin:` for the 22 existing notes (project-os-cockpit 2, your-health 5, your-trainer 15).
- [ ] Delete the three checks; keep and re-verify `DEFER-SCOPE`.
- [ ] Rewrite the procedure in `status-transition/SKILL.md` and `STATUSES.md`.
- [ ] Write the regression fixture; confirm it fails without `DEFER-SCOPE`.

## Notes

**What is being cut is bookkeeping, not the rule.** ISS-0002 — parents closing over parked work, which then vanished from every active surface — was a real bug and its fix stands. `DEFER-SCOPE` staying an error is a completion criterion rather than an assumption precisely because this task touches the machinery around that fix.

**Why freeze `origin:` rather than derive it continuously.** Git recovers a previous parent only when the deferral was committed as a distinct change; for older notes it may not be recoverable at all. Deriving on every run would make the value flicker as history is rewritten or squashed. Derive once, write it down, treat it as authored thereafter.

**Proportion.** Deferral costs an ADR, a requirement, a feature, four tasks, five validator checks, a procedure written twice, branches in three skills, two frontmatter fields, a parking lot and two metrics — for 22 notes in 2 of 10 repos, 15 of them in one. The invariant earns its place; the ceremony does not.

## Cancelled (2026-07-25) — premise withdrawn

This task assumed `SNAPSHOT.yaml` would be generated wholesale, so the fields it targets could be computed. That premise was rejected on evidence: the whole-file generator diverged on all 10 repos (it would have added 180 items, dropped 153, and destroyed ~80 comment lines), and was replaced by a surgical updater owning only `status`, `counters` and `metrics.counts` — see [[ADR-0009-Snapshot-Is-Generated|ADR-0009]]'s amendment and [[REQ-0019-Snapshot-Generated|REQ-0019]]'s.

With nothing generating the snapshot's membership or relationship fields, there is no mechanism for this task to use. It is **cancelled rather than deferred**: deferral means "still wanted, parked", and what was wanted here depends on a design the project has now declined.

The underlying motivation stands and is not lost — it is recorded in REQ-0020's amendment as a legitimate future target, to be pursued through a mechanism that does not require generating the snapshot.

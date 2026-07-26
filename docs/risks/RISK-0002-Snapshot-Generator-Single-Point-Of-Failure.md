---
type: "[[risk]]"
id: RISK-0002
aliases: ["RISK-0002"]
title: "A generated SNAPSHOT.yaml makes the generator a single point of failure for agent context in all 10 repos at once"
status: closed
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: ["review:2026-07-25-fleet-state-audit"]
likelihood: medium
impact: high
mitigation: []
related: [FEAT-0015, TASK-0060, ADR-0009, REQ-0019]
---

# Snapshot generator as a single point of failure

## Description

`SNAPSHOT.yaml` is what every agent reads at session start to establish what is active. Today it is hand-written: a bad edit corrupts one repo, and the validator's `ITEM-STATUS`/`COUNTER`/`METRICS` checks catch the disagreement because there are two independent copies to compare.

After [[FEAT-0015-Derived-State|FEAT-0015]], there is one copy and one writer. Three consequences follow:

**The error surface becomes fleet-wide.** A generator bug ships to all 10 repos through template sync and corrupts every snapshot on the next commit in each.

**The checks that would have caught it are gone.** [[REQ-0019-Snapshot-Generated|REQ-0019]] deletes `ITEM-STATUS`, `COUNTER` and `METRICS` on the grounds that their violations become unrepresentable — which is true of *hand-sync* failure and not of *generator* failure. Afterwards, `--check` in CI compares the committed file against the generator's own output, so a generator that is consistently wrong passes its own check. The oracle and the implementation are the same code.

**Failure is quiet.** A dropped item does not error; it simply is not in `items.*`, and the next agent reads a snapshot that says the work does not exist. Retention pruning makes this worse, because omitting terminal items is *correct* behaviour — so "item missing" cannot itself be treated as a defect signal.

A related hazard is non-determinism. If output ordering is unstable, or if retention keys on wall-clock time (see [[TASK-0063-Retention-In-Generator|TASK-0063]]), the file regenerates differently on different days and every commit churns it — which destroys reviewability and, worse, trains reviewers to skip the diff that is the last human check on this file.

## Mitigation

- **Shadow period before write authority.** Run `--check` against all 10 repos' existing hand-written snapshots; every diff explained as either a generator defect or a pre-existing hand-maintenance error. No repo gets a writing hook until its diff is fully accounted for.
- **Fixture suite as an independent oracle** — hand-authored expected output for a synthetic docs tree, so the generator is tested against something other than itself.
- **Deterministic, stable ordering** as an acceptance criterion of REQ-0019, verified by regenerating an unchanged repo and asserting a zero-line diff.
- **Retention expressed reproducibly** rather than by wall-clock, so generation is idempotent across days.
- **Git is the backstop.** The generated file is committed, so any corruption is diffable and revertible — which is an argument for keeping generation at commit time rather than moving it to session start.
- **Per-repo rollout**, not a single fleet sync, so a defect surfaces in one repo before it reaches nine others.
- Retain a `--check`-only mode permanently for CI, so a hand-edited snapshot is still detected as divergence rather than silently overwritten.

## Triggers

- A `--check` diff in a repo where no note changed.
- Regeneration producing a non-zero diff on an unchanged tree.
- `items.*` count dropping between runs without a corresponding retention-window change.
- An agent reporting that focus or an active item "does not exist" when the note is present on disk.
- Repeated churn in `SNAPSHOT.yaml` commits with no semantic change.

## Outcome (2026-07-25) — designed out rather than mitigated

This risk was written against a whole-file generator: a bug would corrupt agent context in all 10 repos at once, and CI's `--check` would compare the generator against itself.

That design was **rejected on shadow-run evidence** (ADR-0009 amendment) and replaced by a surgical updater that rewrites only `status`, `counters` and `metrics.counts` and never touches membership, comments or prose. The blast radius the risk described no longer exists:

- A defect can wrong a *field*, not delete an item — items are never emitted or pruned by the tool.
- The oracle problem is gone: the updater copies the note's status verbatim, so "correct" is checkable by reading the note, not by trusting the tool.
- `--check` reports **0 drift across all 10 repos**, and the two bugs found during development (a composite-ID collision resolving `FEAT-0009` to a change note, and a sentinel rule that exempted `ISS-0009` from counter integrity) were both caught by that check before any write.

The second of those was a **latent bug in the validator itself**, fixed fleet-wide: `set(str(int("0009")))` is `{"9"}`, so every zero-padded nines ID had silently escaped counter integrity.

Closed — the hazard was removed by design, not accepted.

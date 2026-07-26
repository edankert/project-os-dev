---
type: "[[task]]"
id: TASK-0063
aliases: ["TASK-0063"]
title: "Encode retention as generator policy; drop manual pruning from close-out"
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
related: [REQ-0019, ADR-0009]
tests: []
---

# Retention in the generator

## Definition of Done

- [ ] `retention: active-and-recent` applied deterministically by the generator.
- [ ] **The retention window is expressed reproducibly** — not by wall-clock — so regeneration is idempotent across days (see Notes).
- [ ] Deferred items are never pruned, per ADR-0005 and REQ-0013.
- [ ] Close-out's "Retention enforcement" step (step 9) removed.
- [ ] `SNAPSHOT.md` retention section rewritten to describe generator behaviour rather than agent instruction.
- [ ] Pruning a note from `items.*` never deletes or modifies the note itself — the note stays the archive.

## Steps

- [ ] Decide the window unit (see Notes) and record the reasoning.
- [ ] Implement pruning in the generator, with the deferred exemption.
- [ ] Verify `recent_changes_max` and the other `retention` keys still mean what they say, or update them.
- [ ] Remove the close-out step and rewrite `SNAPSHOT.md`.

## Notes

**The idempotence problem is the substance of this task.** If retention keys on "terminal and older than N days", the generated file depends on the current date as well as on `docs/**`. Two consequences, both bad: regenerating an unchanged repo tomorrow produces a diff, so the zero-diff acceptance criterion of [[REQ-0019-Snapshot-Generated|REQ-0019]] cannot hold; and CI's `--check` fails on repos that simply have not committed recently.

Options:

1. **Count-based** — keep the N most recent terminal items per collection. Fully reproducible; the window drifts with activity rather than time.
2. **Commit-anchored** — retain items terminal within the last N commits. Reproducible from repo state; more complex, needs git access in the generator.
3. **Explicit** — a `retained_until:` marker written once when an item goes terminal. Reproducible, but reintroduces authored state, which is what this feature is removing.

Option 1 is the obvious default; the decision belongs in this note either way, because whichever is chosen becomes a property every downstream repo depends on.

**Do not conflate pruning with deletion.** Pruning removes an entry from `items.*`; the note remains on disk and remains the long-term record. That distinction is already in `SNAPSHOT.md` and must survive the rewrite intact.

## Cancelled (2026-07-25) — premise withdrawn

This task assumed `SNAPSHOT.yaml` would be generated wholesale, so the fields it targets could be computed. That premise was rejected on evidence: the whole-file generator diverged on all 10 repos (it would have added 180 items, dropped 153, and destroyed ~80 comment lines), and was replaced by a surgical updater owning only `status`, `counters` and `metrics.counts` — see [[ADR-0009-Snapshot-Is-Generated|ADR-0009]]'s amendment and [[REQ-0019-Snapshot-Generated|REQ-0019]]'s.

With nothing generating the snapshot's membership or relationship fields, there is no mechanism for this task to use. It is **cancelled rather than deferred**: deferral means "still wanted, parked", and what was wanted here depends on a design the project has now declined.

The underlying motivation stands and is not lost — it is recorded in REQ-0020's amendment as a legitimate future target, to be pursued through a mechanism that does not require generating the snapshot.

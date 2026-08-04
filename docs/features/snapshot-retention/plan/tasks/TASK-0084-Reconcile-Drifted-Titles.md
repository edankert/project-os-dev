---
type: "[[task]]"
id: TASK-0084
aliases: ["TASK-0084"]
title: "Reconcile 579 drifted titles across the fleet, relocating narrative to `note:` where it earns its place"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["ADR-0018", "fleet measurement 2026-08-03"]
parent: "[[FEAT-0022]]"
effort: L
due: ""
depends: ["[[TASK-0083]]"]
blocks: ["[[TASK-0082]]"]
related: ["[[ADR-0018]]", "[[ISS-0030]]"]
tests: []
---

# Reconcile the drifted titles

## What

Before `title` becomes overwritten-from-the-note, decide what happens to each divergence. **579 fleet-wide**: 413 in `your-trainer`, 140 in `project-os-cockpit`, 26 here.

This is the task that prevents the other two from destroying anything, and it is the only one that needs judgement rather than code.

## The three dispositions

For each drifted entry:

- **Discard** — the snapshot title is a stale or abbreviated version of the note's. The note wins; nothing is lost. Expected to cover most of `project-os-cockpit`'s 140 and all 26 here, where snapshot titles are *shorter* than their notes'.
- **Relocate to `note:`** — the snapshot title carries narrative the note does not: root cause, current blocker, what changed and why. This is real content and `note:` is where ADR-0018 puts it. Expected to cover much of `your-trainer`'s 413, where snapshot titles run to 2,160 characters and hold crash-report forensics.
- **Promote to the note** — the snapshot title is simply *better* than the note's. Fix the note; the snapshot then derives correctly.

## Why this cannot be automated

The disposition depends on whether the extra text is *stale*, *narrative*, or *better* — which is a reading of content, not a property of it. A length heuristic would get `project-os-cockpit` roughly right and `your-trainer` badly wrong, since a longer snapshot title there is sometimes a live blocker and sometimes an account of work finished in June.

What *can* be mechanical: producing the worklist (`TASK-0083`'s drift check), grouping by repo and collection, and sorting by divergence size so the 351 titles over 200 characters are triaged first.

## Judgement to apply

- **Relocating is not free.** `note:` on a *terminal* item is curation nobody will read again, and under ADR-0018 rule 6 it also makes that entry permanently exempt from pruning. So narrative on finished work should mostly be **discarded**, not relocated — it is in git and in the note's body. Relocate for items still in flight.
- **That interaction is the trap in this task.** Relocating all 413 of `your-trainer`'s divergences to `note:` would exempt 413 entries from the retention this feature exists to deliver, and the file would barely shrink. Discard by default; relocate deliberately.
- The `# Pruned:` comment style already used in the fleet is the model for legibility: record *why* a batch was discarded, once per batch, not per item.

## Definition of Done

- [ ] Every one of the 579 divergences has a recorded disposition.
- [ ] Narrative worth keeping is in `note:` — and the count of entries thereby exempted from pruning is stated, so the trade against TASK-0082 is visible rather than discovered later.
- [ ] Notes corrected where the snapshot title was the better one.
- [ ] `sync-snapshot.py --check` clean fleet-wide with `title` derivation active.
- [ ] Per-repo commits, following `TASK-0055`'s fleet-migration pattern.
- [ ] Before/after snapshot sizes recorded per repo, so the predicted −28% in `your-trainer` is verified rather than assumed — this feature has already had one unmeasured size claim retracted (`ISS-0030`, 2026-08-03).

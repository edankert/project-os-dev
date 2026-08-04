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
- **Relocate into the note file** — the snapshot title carries narrative the note does not: root cause, current blocker, what changed and why. This is real content and it belongs in the `.md`, **not** in the snapshot's `note:` field, which ADR-0018 rule 3 declares scratch context. Expected to cover much of `your-trainer`'s 413, where snapshot titles run to 2,160 characters and hold crash-report forensics.
- **Promote to the note** — the snapshot title is simply *better* than the note's. Fix the note; the snapshot then derives correctly.

## How much of this is mechanical

More than first assumed. Measured on `your-trainer`'s 405 measurable divergences (2026-08-04), by whether the snapshot title's substantive words already appear in the note:

| | count | disposition |
|---|---:|---|
| >90% present in the note | **227** | discard — the note already says it |
| 50–90% present | 168 | inspect; usually a fragment worth folding in |
| <50% present — orphan prose | **10** | must be relocated into the note file, or it is lost |

So the worklist can be produced and *ordered* mechanically, and roughly half needs no judgement at all. What cannot be mechanical is the middle band and the orphans: whether the extra text is stale, live, or simply better than the note's own title is a reading of content. A length heuristic would get `project-os-cockpit` roughly right and `your-trainer` badly wrong, since a longer snapshot title there is sometimes a live blocker and sometimes an account of work finished in June.

**The similarity measure orders the work; it must not perform it.** A false positive discards prose that exists nowhere else — that is the same reason ADR-0018 rule 3 refuses to detect "already in the note" automatically.

## Judgement to apply

- **Relocation targets the note file, never `note:`.** Under ADR-0018 rule 3 that field is scratch context; moving durable narrative into it puts the prose back in the place with no archive, which is the defect this task exists to clear.
- **Discard is safe only where the note already carries the text** — 227 of 405 in `your-trainer`. Elsewhere, discarding destroys the only copy. This corrects the task's first draft, which said "discard by default" on the untested assumption that the narrative was in git and the note body; it is in git, but for ~178 titles it is not in the note.
- The `# Pruned:` comment style already used in the fleet is the model for legibility: record *why* a batch was discarded, once per batch, not per item.

## Definition of Done

- [ ] Every one of the 579 divergences has a recorded disposition.
- [ ] Narrative worth keeping is in the **note file**; no divergence is resolved by moving prose into the snapshot's `note:` field.
- [ ] The 10 orphan titles (<50% present in their note) are each accounted for individually — they are the only ones where a mistake is unrecoverable.
- [ ] Notes corrected where the snapshot title was the better one.
- [ ] `sync-snapshot.py --check` clean fleet-wide with `title` derivation active.
- [ ] Per-repo commits, following `TASK-0055`'s fleet-migration pattern.
- [ ] Before/after snapshot sizes recorded per repo, so the predicted −28% in `your-trainer` is verified rather than assumed — this feature has already had one unmeasured size claim retracted (`ISS-0030`, 2026-08-03).

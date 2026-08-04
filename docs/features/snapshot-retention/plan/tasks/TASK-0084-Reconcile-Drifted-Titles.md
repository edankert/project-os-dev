---
type: "[[task]]"
id: TASK-0084
aliases: ["TASK-0084"]
title: "Migrate 659 drifted titles mechanically: record every old value, then let derivation replace it"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["ADR-0018", "fleet measurement 2026-08-04"]
parent: "[[FEAT-0022]]"
effort: S
due: ""
depends: ["[[TASK-0083]]"]
blocks: ["[[TASK-0082]]"]
related: ["[[ADR-0018]]", "[[ISS-0030]]"]
tests: []
---

# Migrate the drifted titles

## What

Before `title` becomes derived, write every drifted snapshot title to a per-repo migration record, then let derivation overwrite it. **659 fleet-wide** (measured 2026-08-04 across all twelve repos): `your-trainer` 413, `project-os-cockpit` 140, `your-sudoku` 29, `project-os-dev` 26, `your-applications.com` 26, `your-health` 17, and 8 across the four smallest.

No item-by-item decision is required. That is a change from this task's first draft, which called it *"the only one that needs judgement rather than code"* and sized it `L`.

## Why the judgement was avoidable

The first draft framed the disposition as *discard, relocate, or promote* — a reading of each title's content, 659 times. That conflated two questions:

- **Is anything lost?** — a safety question, and the only one that must be answered before derivation runs.
- **Where does this prose ideally belong?** — an editorial question, answerable later, or never.

Recording every old title to one file per repo answers the first completely and defers the second at no cost. Nothing is lost, so nothing has to be decided now.

A containment test was considered and is **not needed**. Strict verbatim containment — is the snapshot title, whitespace- and case-normalised, present in its note? — resolves only **75 of 659 (11%)** fleet-wide, because most drift is paraphrase rather than duplication. A fuzzy test resolves far more but can delete text on a false positive, which is unacceptable for the 10 titles in `your-trainer` that exist nowhere else. Recording everything makes the test unnecessary rather than forcing a choice between a weak one and a dangerous one.

## The migration record

One file per repo, written before derivation is enabled there — `docs/reference/snapshot-title-migration-YYYY-MM-DD.md`, a `[[reference]]` note listing each affected ID with its old snapshot title and the note title replacing it.

- **Lossless**, so derivation can be enabled without inspecting anything.
- **Reviewable in one place**, rather than 659 diffs scattered across notes.
- **Does not pollute the notes.** Appending the 584 non-contained titles into their note bodies was the alternative, and would have added mostly-redundant paraphrase to 584 files — preservation by vandalism.
- Git already holds the old values; this is deliberate redundancy, because finding them in git means knowing which commit to look in.

## What remains for a human, later and optionally

Mining the record for prose worth folding into a note properly. `your-trainer`'s 10 orphan titles — under 50% word overlap with their note — are the obvious candidates, and the record should mark them so they are findable. This blocks nothing, and it is legitimate for it never to happen.

## Definition of Done

- [ ] Migration record written per affected repo, covering every drifted title before derivation is enabled there.
- [ ] The 10 low-overlap orphans flagged within the record so later mining has a starting point.
- [ ] Derivation enabled; `sync-snapshot.py --check` clean fleet-wide.
- [ ] Per-repo commits, following `TASK-0055`'s fleet-migration pattern, sequenced by [[TASK-0085-Fleet-Rollout|TASK-0085]].
- [ ] Before/after snapshot sizes recorded per repo, so the predicted −28% in `your-trainer` is verified rather than assumed — this feature has already had one unmeasured size claim retracted (`ISS-0030`).

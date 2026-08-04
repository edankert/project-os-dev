---
type: "[[adr]]"
id: ADR-0018
aliases: ["ADR-0018"]
title: "What the generator owns: it derives every field that has a note counterpart, it may remove entries by a reproducible rule but never add one, and item-level `note:` is scratch context that holds its entry until cleared"
status: proposed
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["fleet measurement 2026-08-03/04", "ISS-0030", "user decision 2026-08-04"]
decision: "Three rules. (1) Every snapshot field with a counterpart in the note's frontmatter is derived from it — `title` and feature `goal` join `status`, `counters` and `metrics.counts`. (2) Membership is derivable in ONE direction only: the generator may remove an entry meeting a reproducible rule and may never add one. (3) Item-level `note:`, the one field with no note counterpart, is **scratch context** rather than durable record — the note file is the archive, a non-empty `note:` HOLDS its entry from removal and is reported as a pending relocation, and clearing it is the author's confirmation that the durable copy exists"
context: "ADR-0009 made status, counters and metrics derived and left membership as curation, on evidence: a whole-file generator diverged on all 10 repos (180 items added, 153 dropped, ~80 curated comment lines destroyed), so TASK-0063 was cancelled. Six weeks later ISS-0030 found the consequence — retention is performed by nothing, its three flags are read by no code, and its rule named a status ADR-0008 deleted. Measured: your-trainer holds 709 terminal items of 1,065; its titles are 60% of the file and 413 of them have drifted from the notes they duplicate"
alternatives:
  - "Whole-file generation (the TASK-0063 design) — rejected, and stays rejected on its original evidence. A snapshot is duplication plus curation, and regenerating destroys the curated half to fix the duplicated half. Nothing here revisits that"
  - "A --prune subcommand run deliberately — rejected as the primary mechanism: it is a manual duty with a tool attached, and ISS-0030 exists because the manual duty was never performed. Retained as the --no-prune escape hatch's inverse, for operators who want to preview"
  - "A SNAP-RETENTION validator finding only — rejected as sufficient: it converts an invisible duty into a visible one and leaves the work manual. Worth adding later as a check that the rule ran, not as a substitute for running it"
  - "Delete the three retention flags and drop the policy — rejected: the policy is right, and the measured cost of abandoning it is a file where two of every three entries a query matches describe finished work"
  - "Truncate long titles at a fixed width (as TASK-0080 proposed) — rejected: it destroys the narrative rather than relocating it. The narrative has value and belongs in the item's note file — not in the snapshot's `note:` field, which rule 3 declares scratch and which would put it back somewhere with no archive"
consequences:
  - "Retention becomes a property of the system rather than a duty owed at close-out, and stops depending on anyone remembering"
  - "`title` drift becomes structurally impossible in the same way ADR-0009 made status drift impossible; 413 drifted titles in your-trainer, 140 in project-os-cockpit and 26 here are reconciled once and then cannot recur"
  - "your-trainer's snapshot loses roughly 28% to title derivation before a single entry is pruned, because its snapshot titles are longer than its note titles"
  - "The generator now deletes lines from a tracked file on every run. Git is the safety net, `--no-prune` is the escape hatch, and every removal is reported and comment-marked — but this is the first time the tool removes rather than rewrites, and that deserves the caution"
  - "An entry carrying `note:` prose is HELD from removal and reported, not permanently exempted. Measured, this holds 0 of 709 terminal items in your-trainer, 88 of 360 in project-os-cockpit and 19 of 77 here — a finite, closable backlog rather than a growing exempt set"
  - "Annotating an item stops being a life sentence for its snapshot entry. Under the first draft of this decision, an entry carrying `note:` was exempt from pruning forever, so the snapshot would have accumulated precisely the entries someone bothered to annotate"
  - "The mechanical signal is the field being empty, not a similarity heuristic. A tool guessing whether prose is 'already in the note' would destroy text on a false positive, and that risk is not worth automating away a judgement the author can make in seconds"
  - "ADR-0009's stated boundary changes and its docstring in sync-snapshot.py must change with it, or the script disclaims what it does"
related: [ADR-0009, ADR-0005, ADR-0017, ISS-0030, ISS-0031]
supersedes: ""
superseded: ""
---

# What the generator owns

## Context

[[ADR-0009-Snapshot-Is-Generated|ADR-0009]] drew a line: `status`, `counters` and `metrics.counts` are derived from the notes; everything else in `SNAPSHOT.yaml` is curation the generator does not touch. `sync-snapshot.py` states it in its own header:

> Unregistered notes are REPORTED, never auto-added -- which items a snapshot carries is the curation decision this script deliberately does not make.

That line was drawn on evidence and the evidence was good. A whole-file generator was built, shadow-run against all ten repos, and rejected: it would have added 180 items, dropped 153, and destroyed ~80 lines of hand-written comments. `TASK-0063` — retention as generator policy — was cancelled with it, and its cancellation note preserved the motivation *"to be pursued through a mechanism that does not require generating the snapshot."*

No such mechanism was built. Six weeks later [[ISS-0030-Retention-Is-Policy-Nothing-Performs|ISS-0030]] found what that cost: retention performed by nothing, three `keep_*` flags read by no code, and a normative rule still naming the `closed` status ADR-0008 deleted. Measured on 2026-08-03/04:

- `your-trainer` carries **709 terminal items of 1,065** — 451 `done` tasks, 205 `fixed` issues, 53 `done` features.
- Its **titles are 60% of the file** (231,506 of 386,354 bytes): median 77 characters, p90 585, max 2,160, with 351 items over 200.
- **413 of its 1,065 titles differ from the note they duplicate**, as do 140 in `project-os-cockpit` and 26 here. Nothing syncs them, so nothing can notice.

The drift runs in both directions, which is the diagnosis. `your-trainer` grew its titles into status narratives; the other repos abbreviated theirs. `title:` has no contract, so each repo invented one.

## Decision

The generator's ownership is defined by three rules rather than by a list of fields.

### 1. Fields with a note counterpart are derived, like `status`

A snapshot entry's `title` is written from the note's `title`, and a feature's `goal` from the note's `goal`. They join `status`, `counters` and `metrics.counts` in the set ADR-0009 made underivable-by-hand, and for the same reason: two copies with nothing comparing them is how they disagree.

**The test is whether the field has a counterpart in the note's frontmatter**, and it is what separates rule 1 from rule 3. `title` does — 579 fleet-wide divergences. `goal` does — all 22 feature notes here carry it, and 4 of the 12 snapshot entries carrying it have drifted. `note` does not, which is exactly why it needs different treatment rather than derivation.

This does not destroy the narrative that grew into `your-trainer`'s titles. That narrative has real value — an agent reading the snapshot learns *why* an item sits where it does without opening three notes — and it belongs in **the item's note file**, which is the archive. It does **not** belong in the snapshot's `note:` field: rule 3 makes that scratch, so parking it there would return it to a place with no durable home. The instruction is to relocate it into the note, not to delete it and not to move it sideways.

### 2. Membership is derivable in one direction only

The generator **may remove** an entry that satisfies a reproducible rule. It **may never add** one. Adding is the decision ADR-0009 reserved to curation and this decision does not reclaim it — `--report-unregistered` remains the mechanism, and it remains advisory.

An entry is removable when **all** of the following hold:

1. its status is terminal for its type — `done` task, `fixed` issue, `done` feature;
2. it is not among the **N most recent by ID** in its collection;
3. it is not `deferred` — never, under [[ADR-0005-Deferral-As-Descoping|ADR-0005]] and `DEFER-RETENTION`;
4. it is not named in `focus`;
5. its note exists on disk and parses — otherwise the entry may be the only surviving copy of its state;
6. its item-level `note:` field is empty (see rule 3). `goal:` does not appear here — under rule 1 it is derived, so it cannot hold anything.

**The window is count-based, never wall-clock.** This is the substance of what `TASK-0063` worked out and it is not negotiable: a date-keyed rule makes the output depend on the day it ran, so an untouched repo drifts overnight and CI's `sync-snapshot.py --check` fails on any repo that has not committed recently. `REQ-0019`'s zero-diff property is what forces this.

### 3. Item-level `note:` is scratch context, and holds its entry until cleared

Comments, ordering, `focus`, `project` and `team` are untouched, as before — those describe the snapshot itself and have no other home.

Item-level `note:` is different, and the difference was not seen when this decision was first drafted. It is **prose about an item, stored outside that item's own note, with no counterpart there** — which makes it the one thing in the file that is neither derivable nor snapshot-scoped. It is hereby declared **scratch context**: orientation for work in flight, not durable record. The note file is the archive.

So:

- A non-empty `note:` **holds** its entry from removal and is **reported** as a pending relocation.
- Clearing the field is the author's statement that whatever mattered now lives in the note. The entry then prunes normally.
- The hold is a **finite, closable backlog**, not a resting state.

**The first draft of this decision got this wrong**, and the error is worth recording because it is the shape this repo keeps finding. It made an annotated entry *permanently exempt*, which would have meant the snapshot accumulating precisely the entries someone bothered to annotate — annotation as a life sentence. `FEAT-0022`'s TASK-0084 then had to carry a warning that relocating narrative into `note:` would exempt 413 entries from the retention the feature exists to deliver. That warning disappears under this rule, because the field no longer confers permanence.

**The signal is the field being empty, not a similarity heuristic.** A measurement on 2026-08-04 showed that `note:` prose is mostly, but not always, already present in the note body — 32 of 32 in this repo, 102 of 120 in `project-os-cockpit`, 86 of 96 in `your-health`, leaving **28 orphans** across two repos. A tool that guessed would delete those 28 on a false positive. The author can settle it in seconds and the tool cannot settle it safely at all, so the tool does not try.

| repo | terminal | non-empty `note:` | removable now | held, pending relocation |
|---|---:|---:|---:|---:|
| your-trainer | 709 | 0 | 709 | 0 |
| project-os-cockpit | 360 | 88 | 272 | 88 |
| your-health | 274 | 36 | 238 | 36 |
| project-os-dev | 77 | 19 | 58 | 19 |

## Why this is not TASK-0063 returning

`TASK-0063` proposed **regenerating** the file. The objection was that regeneration computes the whole thing, so the curated half is destroyed to fix the duplicated half.

Removal-by-rule computes nothing. Every entry the rule does not match is byte-identical afterwards; comments, ordering and prose survive because nothing rewrites them; and the one thing that changes — whole entries disappearing — is exactly the operation `retention: active-and-recent` has always claimed to perform and never has.

The distinction is not a technicality. It is the difference between *"the file is a function of `docs/`"*, which is false, and *"entries meeting a stated rule do not belong in it"*, which is the policy already written down.

## Consequences

See frontmatter. The one to watch: **the generator now deletes lines from a tracked file on every run.** Git holds the history, `--no-prune` disables it, every removal is reported on stdout and marked with a `# Pruned:` comment — but this is the first operation in the system that removes rather than rewrites, and if it goes wrong it will go wrong in twelve repos at once. The rollout deserves the same care `TASK-0072` gave the generator itself.

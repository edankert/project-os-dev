---
type: "[[adr]]"
id: ADR-0018
aliases: ["ADR-0018"]
title: "What the generator owns: it may derive `title` as it derives `status`, and it may remove entries by a reproducible rule — but it may never add one, and never rewrites curated prose"
status: proposed
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["fleet measurement 2026-08-03/04", "ISS-0030", "user decision 2026-08-04"]
decision: "Extend ADR-0009's derived set in two directions and close it in a third. `title:` becomes derived from the note, like `status:`. Membership becomes derivable in ONE direction only — the generator may remove an entry that meets a reproducible rule, and may never add one. Curated prose (`note:`, `goal:`, comments, ordering) is never rewritten and never removed, and an entry carrying it is exempt from removal, which makes curation self-protecting without the generator having to understand it"
context: "ADR-0009 made status, counters and metrics derived and left membership as curation, on evidence: a whole-file generator diverged on all 10 repos (180 items added, 153 dropped, ~80 curated comment lines destroyed), so TASK-0063 was cancelled. Six weeks later ISS-0030 found the consequence — retention is performed by nothing, its three flags are read by no code, and its rule named a status ADR-0008 deleted. Measured: your-trainer holds 709 terminal items of 1,065; its titles are 60% of the file and 413 of them have drifted from the notes they duplicate"
alternatives:
  - "Whole-file generation (the TASK-0063 design) — rejected, and stays rejected on its original evidence. A snapshot is duplication plus curation, and regenerating destroys the curated half to fix the duplicated half. Nothing here revisits that"
  - "A --prune subcommand run deliberately — rejected as the primary mechanism: it is a manual duty with a tool attached, and ISS-0030 exists because the manual duty was never performed. Retained as the --no-prune escape hatch's inverse, for operators who want to preview"
  - "A SNAP-RETENTION validator finding only — rejected as sufficient: it converts an invisible duty into a visible one and leaves the work manual. Worth adding later as a check that the rule ran, not as a substitute for running it"
  - "Delete the three retention flags and drop the policy — rejected: the policy is right, and the measured cost of abandoning it is a file where two of every three entries a query matches describe finished work"
  - "Truncate long titles at a fixed width (as TASK-0080 proposed) — rejected: it destroys the narrative rather than relocating it. The narrative has value; `note:` is where it belongs, and it is already curation the generator leaves alone"
consequences:
  - "Retention becomes a property of the system rather than a duty owed at close-out, and stops depending on anyone remembering"
  - "`title` drift becomes structurally impossible in the same way ADR-0009 made status drift impossible; 413 drifted titles in your-trainer, 140 in project-os-cockpit and 26 here are reconciled once and then cannot recur"
  - "your-trainer's snapshot loses roughly 28% to title derivation before a single entry is pruned, because its snapshot titles are longer than its note titles"
  - "The generator now deletes lines from a tracked file on every run. Git is the safety net, `--no-prune` is the escape hatch, and every removal is reported and comment-marked — but this is the first time the tool removes rather than rewrites, and that deserves the caution"
  - "An entry carrying `note:` or `goal:` prose is never auto-removed. Measured, this exempts 0 of 709 terminal items in your-trainer, 88 of 360 in project-os-cockpit and 19 of 77 here — so curation is protected where it exists without blocking the cleanup where it does not"
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

### 1. `title` is derived, like `status`

A snapshot entry's `title` is written from the note's `title`. It joins `status`, `counters` and `metrics.counts` in the set ADR-0009 made underivable-by-hand, and for the same reason: two copies with nothing comparing them is how they disagree.

This does not destroy the narrative that grew into `your-trainer`'s titles. That narrative has real value — an agent reading the snapshot learns *why* an item sits where it does without opening three notes — and it belongs in **`note:`**, which already exists for exactly this purpose and which the generator already leaves alone. The instruction is to relocate it, not to delete it.

### 2. Membership is derivable in one direction only

The generator **may remove** an entry that satisfies a reproducible rule. It **may never add** one. Adding is the decision ADR-0009 reserved to curation and this decision does not reclaim it — `--report-unregistered` remains the mechanism, and it remains advisory.

An entry is removable when **all** of the following hold:

1. its status is terminal for its type — `done` task, `fixed` issue, `done` feature;
2. it is not among the **N most recent by ID** in its collection;
3. it is not `deferred` — never, under [[ADR-0005-Deferral-As-Descoping|ADR-0005]] and `DEFER-RETENTION`;
4. it is not named in `focus`;
5. its note exists on disk and parses — otherwise the entry may be the only surviving copy of its state;
6. it carries no `note:` or `goal:` prose.

**The window is count-based, never wall-clock.** This is the substance of what `TASK-0063` worked out and it is not negotiable: a date-keyed rule makes the output depend on the day it ran, so an untouched repo drifts overnight and CI's `sync-snapshot.py --check` fails on any repo that has not committed recently. `REQ-0019`'s zero-diff property is what forces this.

### 3. Curated prose is never rewritten, and protects its entry

Comments, ordering, `focus`, `project`, `team`, and `goal:`/`note:` prose are untouched — as before. Rule 6 extends that from *"not rewritten"* to *"not removed"*: an entry someone bothered to annotate is exempt from automatic removal.

This is the part that makes the whole decision safe. The generator does not need to understand curation; it only needs to recognise its presence. Measured, the exemption costs nothing where the problem is worst and protects the work where it exists:

| repo | terminal | carrying `note:`/`goal:` | auto-removable |
|---|---:|---:|---:|
| your-trainer | 709 | **0** | 709 |
| project-os-cockpit | 360 | 88 | 272 |
| your-health | 274 | 36 | 238 |
| project-os-dev | 77 | 19 | 58 |

## Why this is not TASK-0063 returning

`TASK-0063` proposed **regenerating** the file. The objection was that regeneration computes the whole thing, so the curated half is destroyed to fix the duplicated half.

Removal-by-rule computes nothing. Every entry the rule does not match is byte-identical afterwards; comments, ordering and prose survive because nothing rewrites them; and the one thing that changes — whole entries disappearing — is exactly the operation `retention: active-and-recent` has always claimed to perform and never has.

The distinction is not a technicality. It is the difference between *"the file is a function of `docs/`"*, which is false, and *"entries meeting a stated rule do not belong in it"*, which is the policy already written down.

## Consequences

See frontmatter. The one to watch: **the generator now deletes lines from a tracked file on every run.** Git holds the history, `--no-prune` disables it, every removal is reported on stdout and marked with a `# Pruned:` comment — but this is the first operation in the system that removes rather than rewrites, and if it goes wrong it will go wrong in twelve repos at once. The rollout deserves the same care `TASK-0072` gave the generator itself.

---
type: "[[task]]"
id: TASK-0083
aliases: ["TASK-0083"]
title: "`title` is derived from the note, and drifting one becomes a finding"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["ADR-0018", "fleet measurement 2026-08-04"]
parent: "[[FEAT-0022]]"
effort: M
due: ""
depends: []
blocks: ["[[TASK-0084]]"]
related: ["[[ADR-0018]]", "[[ADR-0009]]"]
tests: []
---

# `title` joins the derived set

## What

`sync-snapshot.py` writes each entry's `title` from its note's `title`, exactly as it already writes `status`. Hand-editing a snapshot title stops being possible in the sense that matters: the next sync overwrites it.

## Why it is worth its own task

Measured 2026-08-04, snapshot titles versus their notes':

| repo | **drifted** | | repo | **drifted** |
|---|---:|---|---|---:|
| your-trainer | **413** | | your-health | 17 |
| project-os-cockpit | 140 | | yourtrainer-mcp | 3 |
| your-sudoku | 29 | | articles | 3 |
| project-os-dev | 26 | | edankert.com | 1 |
| your-applications.com | 26 | | obsidian-supernote-sync | 1 |
| | | | **fleet** | **659** |

Nothing compares them, so nothing notices. This is the same failure ADR-0009 removed for `status` and the same one `ISS-0011` named for status tables: one fact in two places with no comparator.

The size effect is a consequence rather than the motive, and it runs both ways — `your-trainer` **−28% of file**, `project-os-cockpit` and `project-os-dev` roughly **+2%**, because those repos abbreviated where `your-trainer` inflated.

## The ordering constraint

This task lands **before** the prune (`TASK-0082`) and its migration (`TASK-0084`) sits between them. Deriving titles first surfaces the 659 divergences while every entry is still present; pruning first would delete entries whose titles hold narrative that exists nowhere else, and ADR-0018's condition 6 holds none of them back in `your-trainer`, where 0 of 709 terminal entries carry `note:` prose.

## The fail-safe, which `TASK-0082` has and this task needs too

The prune step refuses to act on uncertainty — *"unparseable note, missing note, ambiguous status → keep"*. Derivation has no equivalent as first drafted, and it needs one, because **it reads a note that may not supply a title.** Measured across the fleet on 2026-08-04:

- **3 zero-byte notes** — `project-os-cockpit` `TASK-0182`, `TASK-0183`, `TASK-0187`.
- **14 notes with unparseable frontmatter** — 8 in `your-trainer` (`REQ-0194`…`REQ-0201`), 5 in `your-health`, 1 in `your-applications.com`.
- **161 `CHG-*` snapshot entries that resolve to no note by ID at all**, because change notes are keyed by date-slug rather than a numeric ID.

Seventeen real notes and an entire collection. Derivation that blindly writes `note.title` over `entry.title` would blank or crash on every one.

Required behaviour:

- **Matching is by `id:` in the note's frontmatter**, and this must be stated rather than assumed — no note currently says how a snapshot entry is paired with its file. The `file:` path is a fallback, not the key.
- **No note, no `id:`, unparseable frontmatter, empty file, or absent/blank `title:` → leave the existing snapshot title untouched and report it.** Never write an empty title.
- **`CHG-*` and any other collection whose entries have no ID-addressable note are out of scope for derivation** — decide explicitly whether they are excluded or matched some other way, and record which.

## Decisions this task must make

- **Overwrite immediately, or report first?** **Report first — this is now a requirement rather than a recommendation**, because the code is shared across twelve repos and readiness is per-repo. Shipping overwrite-enabled rewrites 659 titles on first sync everywhere, destroying `your-trainer`'s 413 divergences before `TASK-0084` triages them. So: ship in report mode, migrate per repo, and switch to overwrite only where that repo's reconciliation is done. See [[TASK-0085-Fleet-Rollout|TASK-0085]] for the gating mechanism, which this shares with the prune.
- **What a drifted title becomes afterwards.** Once titles are derived, drift is structurally impossible and a check would be dead code, exactly as `ITEM-STATUS` became under ADR-0009 and was deleted. Prefer deleting the check after the migration over keeping a permanently-silent one; ADR-0011 forbids the permanent-warning shape and this is its cousin.
- **`goal:` is affected, and an earlier draft of this note said it was not.** Checked 2026-08-04: all 22 feature notes carry `goal:` in frontmatter, and of the 12 snapshot features carrying it, **4 have drifted from their note**. So `goal:` is the same defect as `title:` — a duplicated field with no comparator — and belongs in the same derivation, not in ADR-0018's scratch category. The distinguishing test is simply *does the field have a note counterpart*: `title` and `goal` do, `note` does not.

## Definition of Done

- [x] `title` written from the note, alongside `status`, in the same surgical style.
- [x] Fail-safe implemented and inversion-tested against all 17 real malformed notes plus a synthetic empty-title case: every one leaves the snapshot title untouched and is reported.
- [x] The matching rule (by note `id:`) and the disposition of the 161 `CHG-*` entries are documented in the note.
- [x] Transitional drift check exists, is used for the migration, and its post-migration disposition is recorded (delete or keep, with reasoning).
- [x] In any repo where derivation is enabled, snapshot `title` equals note `title` for every registered item whose note supplies one. Enabling it across the fleet is [[TASK-0085-Fleet-Rollout|TASK-0085]] and does not gate this task.
- [x] `sync-snapshot.py --check` clean in a dry-run against all twelve repos with derivation forced on, proving the code is fleet-safe before any repo opts in.
- [x] `SNAPSHOT.md` and `SCHEMAS.md` describe `title` as derived, stated once per REQ-0018.

---
type: "[[task]]"
id: TASK-0083
aliases: ["TASK-0083"]
title: "`title` is derived from the note, and drifting one becomes a finding"
status: backlog
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-08-04
updated: 2026-08-04
source: ["ADR-0018", "fleet measurement 2026-08-03"]
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

Measured 2026-08-03, snapshot titles versus their notes':

| repo | identical | **drifted** |
|---|---:|---:|
| your-trainer | 652 | **413** |
| project-os-cockpit | 450 | 140 |
| project-os-dev | 128 | 26 |

Nothing compares them, so nothing notices. This is the same failure ADR-0009 removed for `status` and the same one `ISS-0011` named for status tables: one fact in two places with no comparator.

The size effect is a consequence rather than the motive, and it runs both ways — `your-trainer` **−28% of file**, `project-os-cockpit` and `project-os-dev` roughly **+2%**, because those repos abbreviated where `your-trainer` inflated.

## The ordering constraint

This task lands **before** the prune (`TASK-0082`) and its migration (`TASK-0084`) sits between them. Deriving titles first surfaces the 579 divergences while every entry is still present; pruning first would delete entries whose titles hold narrative that exists nowhere else, and ADR-0018's condition 6 holds none of them back in `your-trainer`, where 0 of 709 terminal entries carry `note:` prose.

## Decisions this task must make

- **Overwrite immediately, or report first?** Overwriting is consistent with `status` and is the end state. Reporting first turns 579 silent divergences into a reviewable list, which is what `TASK-0084` needs. Recommend: land the check first, migrate, then switch to overwrite — three steps but no lost prose.
- **What a drifted title becomes afterwards.** Once titles are derived, drift is structurally impossible and a check would be dead code, exactly as `ITEM-STATUS` became under ADR-0009 and was deleted. Prefer deleting the check after the migration over keeping a permanently-silent one; ADR-0011 forbids the permanent-warning shape and this is its cousin.
- **`goal:` is affected, and an earlier draft of this note said it was not.** Checked 2026-08-04: all 22 feature notes carry `goal:` in frontmatter, and of the 12 snapshot features carrying it, **4 have drifted from their note**. So `goal:` is the same defect as `title:` — a duplicated field with no comparator — and belongs in the same derivation, not in ADR-0018's scratch category. The distinguishing test is simply *does the field have a note counterpart*: `title` and `goal` do, `note` does not.

## Definition of Done

- [ ] `title` written from the note, alongside `status`, in the same surgical style.
- [ ] Transitional drift check exists, is used for the migration, and its post-migration disposition is recorded (delete or keep, with reasoning).
- [ ] Fleet-wide: snapshot `title` equals note `title` for every registered item.
- [ ] `sync-snapshot.py --check` clean in all twelve repos after migration.
- [ ] `SNAPSHOT.md` and `SCHEMAS.md` describe `title` as derived, stated once per REQ-0018.

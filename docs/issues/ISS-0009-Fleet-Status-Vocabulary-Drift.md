---
type: "[[issue]]"
id: ISS-0009
aliases: ["ISS-0009"]
title: "Fleet status vocabulary drift: ~370 writes outside the taxonomy, including 71 tasks at the illegal status `superseded`"
status: fixed
phase: "[[PHASE-0002-State-Model-Simplification]]"
severity: medium
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
component: docs
source: ["review:2026-07-25-fleet-state-audit"]
related: [ADR-0008, FEAT-0013, REQ-0016]
tasks: []
tests: []
---

# Statuses outside the taxonomy, fleet-wide

## Problem

Roughly **370** of 5,890 `status:` writes across the fleet used values that appear in no note type's allowed list. 164 of them survive in current note state and are reported by `NOTE-STATUS` as warnings; the rest were migrated away or sit in notes the check cannot reach.

## Evidence

Values written that are in no taxonomy, from git history across 10 repos:

| Value | Writes | Nearest legal equivalent |
|---|---|---|
| `pending` | 166 | `backlog` |
| `fulfilled` | 80 | `implemented` |
| `todo` | 79 | `backlog` |
| `verified` | 79 | `implemented` (retired by ADR-0007) |
| `resolved` | 20 | `fixed` |
| `completed` | 12 | `done` |
| `published` | 11 | `released` |
| `met` | 7 | `implemented` |
| `complete`, `investigating`, `obsolete` | 4 | `done`, `in-progress`, `superseded` |

Current note state carrying illegal values:

- **71 tasks at `superseded`** — never a legal task status in any version of `STATUSES.md`
- **50 issues at `done`**, **30 at `pending`** — `done` is a task/feature word
- **8 tests at `active`**, plus `plan` notes at `doing`/`next`/`backlog`
- **4 phases at `draft`**, 1 at `superseded` — neither is in the phase taxonomy
- `reference` notes at `reference` and `complete`

`NOTE-STATUS` reports 164 of these, concentrated in your-trainer (160) and your-applications.com (4). It is a warning by deliberate design, and the code says why:

> Warning, not error, deliberately: this check reaches notes that were never validated before … Failing those builds outright would punish repos for drift the tooling allowed. Graduate to `report.error` once the fleet is migrated.

## Why the check misses most of it

`validate_unregistered_notes` only inspects notes **not** in `SNAPSHOT.yaml`. Notes that *are* registered are checked by `STATUS-VALUE` against their snapshot entry — which reads the snapshot's status, not the note's. A registered note whose frontmatter holds an illegal value passes both checks whenever the snapshot entry holds a legal one, and `ITEM-STATUS` only fires if the two differ in a way the comparison catches.

So the 164 reported findings are a floor, not a census.

## Expected

Every note carries a status from its type's taxonomy, and a note that does not fails the build.

## Actual

Illegal statuses accumulate silently, and the two most common (`pending`, `todo`) are synonyms for a state that already exists — evidence that authors reach for whatever word fits rather than consulting `STATUSES.md`.

## Impact

- Bases views, cockpit bands, and metric counts all key on status values; an unrecognised value falls through every filter and the item disappears from the surfaces meant to show it.
- It is upstream of nearly every other finding in the 2026-07-25 audit: a taxonomy nobody can recall is a taxonomy nobody applies.

## Next Actions

- [ ] Migrate the fleet to the collapsed vocabulary ([[TASK-0055-Fleet-Vocabulary-Migration|TASK-0055]]), which subsumes this drift rather than fixing it separately.
- [ ] Extend the status check to cover **registered** notes' frontmatter, not only unregistered ones ([[TASK-0054-Validator-Collapsed-Taxonomy|TASK-0054]]).
- [ ] Promote `NOTE-STATUS` to error once migration is clean, per [[ADR-0011-No-Permanent-Warning-Tier|ADR-0011]] clause 3.

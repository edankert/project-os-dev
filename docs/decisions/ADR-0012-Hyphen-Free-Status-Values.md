---
type: "[[adr]]"
id: ADR-0012
aliases: ["ADR-0012"]
title: "Status values carry no hyphens: merge in-progress and rolled-back, rename in-review and wont-fix"
status: accepted
owner: user:edwin
created: 2026-07-26
updated: 2026-07-26
source: ["user-report:2026-07-26"]
decision: "Remove every hyphenated value from the status vocabulary. Two are redundant and merge into values that already exist — `in-progress` → `doing`, `rolled-back` → `reverted`. Two are genuinely distinct and are renamed — `in-review` → `review`, `wont-fix` → `declined`. The vocabulary drops from 43 values to 41 and contains no hyphens."
context: "Reported while reading the cockpit: `in-review` wrapped mid-value in a status chip, and hyphenated values read badly wherever a status is shown as a token. A survey found no hyphenated frontmatter *keys* at all — those already use underscores — and only four hyphenated values, carried by 15 live notes across the fleet. Two of the four turned out to duplicate values already in the vocabulary."
alternatives:
  - "Leave the vocabulary alone and fix the display: render `in-review` as `in review` in the chip. Rejected as the primary fix — it treats the symptom, and the survey found the values are not merely ugly but partly redundant, which ADR-0008's 'states must earn their keep' says to resolve rather than restyle. The display fix (`white-space: nowrap`) still shipped, because a status is one token and must never break across lines whatever it is called."
  - "Rename all four (`inprogress`, `rolledback`, `review`, `declined`). Rejected: it would keep two values whose meaning is already covered, spending a fleet migration to preserve duplication."
  - "Merge all four into existing values. Rejected: nothing in the vocabulary means `in-review` (a feature awaiting sign-off is not `doing`) or `wont-fix` (a declined issue is not `deferred`, which means parked-but-wanted). Those two distinctions are real and are kept, under better names."
consequences:
  - "`in-progress` and `rolled-back` leave the vocabulary entirely; `doing` and `reverted` absorb them. Feature and issue vocabularies lose a value each."
  - "`in-review` → `review` and `wont-fix` → `declined` are pure renames; the band membership of each is unchanged (`review` active, `declined` archived)."
  - "15 live notes migrate across 3 repos (project-os-cockpit 2, your-sudoku 8, your-trainer 5) via `migrate-status-vocabulary.py`, which already rewrites notes and SNAPSHOT together."
  - "Every palette surface changes: `statuses.py`, `validate-docs.py`'s ALLOWED_STATUS, `base.css`, `cockpit.css`, `cockpit.js`, the Electron renderer, and STATUSES.md. TST-0019's parity suite fails until all agree, which is the point of having it."
  - "Legacy values are NOT retained as aliases upstream — the migration is mechanical and the script is run as part of adopting this ADR. Downstream tools may keep them for tolerance; that is their decision, not this one (see project-os-cockpit ADR-0008)."
supersedes: ""
superseded: ""
related: [ADR-0008, ADR-0006, ISS-0010]
---

# Status values carry no hyphens

## Context

The trigger was cosmetic and honest about being so: in the cockpit's status chip, `in-review` wrapped onto two lines as `in-` / `review`. That is a display bug and was fixed as one. But the question it raised — why do four values carry hyphens when thirty-nine do not? — turned out to be worth asking.

The survey answered a second question first: **no frontmatter key has ever carried a hyphen.** Keys are consistently underscored (`superseded_by`, `last_run`, `review_verdict`, `mitigated_by`). So the inconsistency is confined to four *values* out of forty-three:

| Value | Notes carrying it, fleet-wide |
|---|---|
| `in-progress` | 0 |
| `in-review` | 7 |
| `rolled-back` | 0 |
| `wont-fix` | 8 |

Fifteen notes across three repos. The vocabulary is declared in nine places; the notes are the small part.

## Decision

Two of the four are not naming problems. **`in-progress` means what `doing` means** — the vocabulary has carried both since the fleet's task and feature taxonomies were written independently. **`rolled-back` means what `reverted` means**, likewise. ADR-0008 established that a state must earn its keep, and a state whose meaning is already expressed by another has not. They merge.

The other two are real distinctions with poor names. A feature awaiting sign-off is not `doing`, and an issue that will not be fixed is not `deferred` — `deferred` means parked but still wanted, which is a different fact about the future. They are renamed rather than merged: `in-review` → **`review`**, `wont-fix` → **`declined`**.

The result is 41 values, none hyphenated, with two genuine distinctions preserved under names that read as single tokens wherever a status is displayed.

## Why this is worth a migration at all

It is a small win, and the honest case for doing it now rather than never is that the cost will not get smaller. Fifteen notes is the cheapest this change will ever be, the migration script already exists from ADR-0008's 64→53 collapse, and TST-0019's parity suite mechanically proves every surface agrees afterwards. The same change in a year, across a larger fleet, would be the same work over more notes.

The case for *not* doing it was real and is recorded in the alternatives: a display-layer fix costs one line. It was rejected because the survey found duplication, not just ugliness — and duplication in a status vocabulary is the thing ADR-0008 exists to remove.

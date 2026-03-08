# Status taxonomies and transitions

This file defines the allowed `status` values and recommended transitions for each note type.

If a project needs different states, update this file and the templates in `../../docs/__templates__/`.

## `[[task]]`
- Allowed: `backlog`, `next`, `doing`, `blocked`, `done`
- Typical transitions:
  - `backlog` → `next` → `doing` → `done`
  - `doing` → `blocked` → `doing`

## `[[issue]]`
- Allowed: `triage`, `open`, `in-progress`, `blocked`, `fixed`, `closed`
- Typical transitions:
  - `triage` → `open` → `in-progress` → `fixed` → `closed`
  - `in-progress` → `blocked` → `in-progress`

## `[[feature]]`
- Allowed: `backlog`, `planned`, `in-progress`, `in-review`, `done`
- Typical transitions:
  - `backlog` → `planned` → `in-progress` → `in-review` → `done`

## `[[requirement]]`
- Allowed: `draft`, `approved`, `verified`, `retired`
- Typical transitions:
  - `draft` → `approved` → `verified`
  - `verified` → `retired`

## `[[risk]]`
- Allowed: `open`, `mitigating`, `monitoring`, `closed`
- Typical transitions:
  - `open` → `mitigating` → `monitoring` → `closed`

## `[[workflow]]`
- Allowed: `draft`, `active`, `deprecated`
- Typical transitions:
  - `draft` → `active` → `deprecated`

## `[[change]]`
- Allowed: `merged`, `reverted`

## `[[adr]]`
- Allowed: `proposed`, `accepted`, `rejected`, `superseded`
- Typical transitions:
  - `proposed` → `accepted`
  - `accepted` → `superseded`
  - `proposed` → `rejected`

## `[[release]]`
- Allowed: `draft`, `staged`, `released`, `rolled-back`
- Typical transitions:
  - `draft` → `staged` → `released`
  - `released` → `rolled-back`

## `[[test]]`
- Allowed: `draft`, `ready`, `passing`, `failing`, `blocked`, `deprecated`
- Typical transitions:
  - `draft` → `ready` → `passing`
  - `ready` → `failing` → `ready`
  - `ready` → `blocked` → `ready`

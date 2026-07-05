---
type: instruction
id: INSTR-STATUSES
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [instructions, statuses]
---

# Status taxonomies and transitions

This file defines the allowed `status` values and recommended transitions for each note type.

If a project needs different states, update this file and the templates in `../../docs/__templates__/`.

## `[[task]]`
- Allowed: `backlog`, `next`, `doing`, `blocked`, `done`, `deferred`, `cancelled`
- Typical transitions:
  - `backlog` → `next` → `doing` → `done`
  - `doing` → `blocked` → `doing`
  - `backlog`/`next` → `deferred` (parked) or `cancelled` (will not be done)

## `[[issue]]`
- Allowed: `triage`, `open`, `in-progress`, `blocked`, `fixed`, `closed`, `reopened`, `wont-fix`, `deferred`
- Typical transitions:
  - `triage` → `open` → `in-progress` → `fixed` → `closed`
  - `in-progress` → `blocked` → `in-progress`
  - `closed` → `reopened` → `in-progress` (regression)
  - `triage`/`open` → `wont-fix` (deliberate no-action, keep the note) or `deferred` (parked)

## `[[feature]]`
- Allowed: `backlog`, `planned`, `in-progress`, `in-review`, `done`, `deferred`, `cancelled`, `superseded`
- Typical transitions:
  - `backlog` → `planned` → `in-progress` → `in-review` → `done`
  - `backlog`/`planned` → `deferred` (parked) or `cancelled` (will not be built)
  - `done` → `superseded` (replaced by a newer feature; link the successor)

## `[[phase]]`
- Allowed: `planned`, `active`, `done`, `deferred`
- Typical transitions:
  - `planned` → `active` → `done`
  - `planned` → `deferred`

## `[[requirement]]`
- Allowed: `draft`, `approved`, `implemented`, `verified`, `retired`, `deferred`, `cancelled`, `superseded`
- Typical transitions:
  - `draft` → `approved` → `implemented` → `verified` (`implemented` = built but not yet formally verified; `verified` still requires passing linked tests per `QUALITY.md`)
  - `verified` → `retired`
  - `draft`/`approved` → `deferred` or `cancelled`
  - any → `superseded` (replaced by a newer requirement; link the successor)

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

## `[[test]]`
- Allowed: `draft`, `ready`, `passing`, `failing`, `blocked`, `deprecated`
- Typical transitions:
  - `draft` → `ready` → `passing`
  - `ready` → `failing` → `ready`
  - `ready` → `blocked` → `ready`

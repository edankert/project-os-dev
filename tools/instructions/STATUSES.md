---
type: instruction
id: INSTR-STATUSES
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-07-21
tags: [instructions, statuses]
---

# Status taxonomies and transitions

This file defines the allowed `status` values and recommended transitions for each note type.

If a project needs different states, update this file and the templates in `../../docs/__templates__/`.

Terminal-status semantics: `done`/`closed`/`cancelled`/`wont-fix` **resolve** an item's place in its parent's scope (the parent can complete over them). `deferred` does **not** — it is a parked, non-terminal state governed by the deferral rules at the end of this file.

## `[[task]]`
- Allowed: `backlog`, `next`, `doing`, `blocked`, `done`, `deferred`, `cancelled`
- Typical transitions:
  - `backlog` → `next` → `doing` → `done`
  - `doing` → `blocked` → `doing`
  - `backlog`/`next` → `deferred` (descoped from the parent and parked; see "Deferral and re-adoption") or `cancelled` (will not be done)
  - `deferred` → `backlog` (re-adopted under a new or the original parent)

## `[[issue]]`
- Allowed: `triage`, `open`, `in-progress`, `blocked`, `fixed`, `closed`, `reopened`, `wont-fix`, `deferred`
- Typical transitions:
  - `triage` → `open` → `in-progress` → `fixed` → `closed`
  - `in-progress` → `blocked` → `in-progress`
  - `closed` → `reopened` → `in-progress` (regression)
  - `triage`/`open` → `wont-fix` (deliberate no-action, keep the note) or `deferred` (descoped and parked; see "Deferral and re-adoption")
  - `deferred` → `open` (re-adopted)

## `[[feature]]`
- Allowed: `backlog`, `planned`, `in-progress`, `in-review`, `done`, `deferred`, `cancelled`, `superseded`
- Typical transitions:
  - `backlog` → `planned` → `in-progress` → `in-review` → `done`
  - `backlog`/`planned` → `deferred` (descoped and parked; see "Deferral and re-adoption") or `cancelled` (will not be built)
  - `deferred` → `planned` (re-adopted)
  - `done` → `superseded` (replaced by a newer feature; link the successor)
- **A feature may not reach `done` while a requirement that names it in `implements:` still has an unresolved acceptance criterion** (ADR-0007, validator FEATURE-REQ) — unless that requirement is descoped (`deferred`/`cancelled`/`superseded`). Satisfy the requirement's criteria, or descope it, before closing the feature. This is in addition to the task and test gates in `QUALITY.md`.

## `[[phase]]`
- Allowed: `planned`, `active`, `done`, `deferred`
- Typical transitions:
  - `planned` → `active` → `done`
  - `planned` → `deferred`

## `[[requirement]]`
- Allowed: `draft`, `approved`, `implemented`, `retired`, `deferred`, `cancelled`, `superseded`
- **`implemented` is terminal** (ADR-0007). There is no `verified` requirement status: verification lives in `[[test]]` notes (which carry their own `passing`/`failing` status) and in the per-criterion evidence pointers on the acceptance checkboxes. Recording it a second time as a requirement status added no information and, in practice, was set on delivery or on nothing far more often than on proof.
- Typical transitions:
  - `draft` → `approved` → `implemented`
  - `approved` → `implemented` is set at **feature close-out**, not independently: once the feature named in the requirement's `implements:` has reached a terminal status, its acceptance criteria are ticked against evidence and any departed-from criterion is reconciled (`../skills/close-out/SKILL.md`, "Requirement advancement"). A requirement left at `draft`/`approved` once its feature is terminal (`done`, `cancelled`, or `superseded`) is a validator error (REQ-STALE) — if the feature was cancelled or superseded rather than delivered, supersede or cancel the requirement instead of advancing it.
  - Advancing to `implemented` requires every acceptance criterion to be **ticked with evidence or reconciled**; an unresolved criterion on a terminal requirement is a validator error (REQ-BOXES). The checkboxes, not the status word, are the evidence surface.
  - `implemented` → `retired`
  - `draft`/`approved` → `deferred` (descoped and parked; see "Deferral and re-adoption") or `cancelled`
  - `deferred` → `draft` (re-adopted)
  - any → `superseded` (replaced by a newer requirement; link the successor)
- **Ownership:** a requirement's `implements:` names **at most one** feature (ADR-0007). Two or more is a validator error — split the requirement, or pick the true owner. Zero is permitted (an unowned or cross-cutting requirement gates no feature).

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

## Deferral and re-adoption

`deferred` means "explicitly out of the current parent's scope, still wanted later". It is **not** terminal and never satisfies completeness: a parent whose scope list still contains a deferred item cannot reach a terminal status (enforced by `tools/scripts/validate-docs.py`).

Deferring an item is therefore a **descoping operation**, not just a status flip (decision: ADR "Deferral is a descoping operation" where adopted; procedure: `../skills/status-transition/SKILL.md`):

1. Remove the item's ID from the parent's scope list (e.g. the feature's `tasks:`) and record it in the parent's `deferred:` list instead.
2. On the deferred item, set `origin:` to the former parent (provenance — where the work was originally scoped) and clear `parent:`.
3. Give it a forward home: set `phase:` to a real future phase when one exists, else to the `PHASE-999` parking-lot note (create `docs/phases/PHASE-999-Parking-Lot.md` once if absent; all-9s sentinel IDs are counter-exempt).
4. Mirror all of this in `SNAPSHOT.yaml`. Deferred items count as **active** for snapshot retention — never prune them.

Re-adoption reverses it: assign a new (or the original) parent, add the ID back to that parent's scope list, set the non-parked status (`backlog`/`open`/`draft`/`planned`), and keep `origin:` as history. Backlog grooming reviews every parked item each pass (`../skills/backlog-grooming/SKILL.md`).

## `[[release]]`
- Allowed: `draft`, `staged`, `released`, `rolled-back`
- Typical transitions:
  - `draft` → `staged` → `released` (`staged` = verified and ready to deploy, not yet live; see `../skills/release-verification/SKILL.md`)
  - `released` → `rolled-back` (rollback occurred; keep the note and link the successor release when one ships)

## `[[plan]]`
- Allowed: `draft`, `active`, `done`, `superseded`
- Plans follow their parent feature; most projects leave plans at `draft`/`active`.

## `[[reference]]`
- Allowed: `active`, `deprecated`

---
type: "[[feature]]"
id: FEAT-0019
aliases: ["FEAT-0019"]
title: "A first-class design note type (DES-*)"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["user decision 2026-07-27", "downstream:project-os-cockpit FEAT-0042"]
goal: "Give designs their own note type, because a design has a lifecycle the reference type cannot express: it is proposed, accepted, implemented, and eventually superseded by the next revision."
requirements: []
tasks: ["[[TASK-0078]]", "[[TASK-0079]]"]
release: ""
related: ["[[ADR-0008]]"]
tests: []
---

# A first-class design note type

## Goal

`reference` models "durable material that is not lifecycle state". A design is the opposite: it is a proposal that gets argued over, accepted, built, and replaced. Downstream (project-os-cockpit FEAT-0042) started on `reference` + `scope: design-input` precisely to avoid this change — and then wanted the lifecycle, which is the signal that the type is real rather than convenient.

## Scope

- `[[design]]` type with the `DES` ID prefix, notes under `docs/designs/`.
- A status vocabulary drawn **entirely from values that already exist** — no new status values.
- Template, taxonomy, statuses, traceability, validator, snapshot sync, adapters.
- Fleet propagation, and migration of the one existing design note downstream.

## Out of Scope

- Anything about *rendering* designs. That is downstream FEAT-0042; this is the vocabulary it needs.
- A `designs` metric. Counting designs answers no question anyone has asked; the metric surface is already the place `risks_open` quietly carried retired vocabulary for months (ISS-0016).

## Acceptance

- `DES-*` notes validate, resolve as links, and sync into `items.designs`.
- The status vocabulary introduces **zero** new status values.
- `--self-check` catches the type being added to one status table and not another — the ISS-0016 guard, exercised on its first real use since it was written.
- A design note whose `asset:` does not resolve is reported.
- All 11 repos validate clean after propagation.

## Why zero new status values matters

Edwin's standing constraint (2026-07-26): *"I prefer not to introduce new states."* ADR-0008 is the reason — it collapsed the fleet vocabulary from 64 values to 53 after measuring that several had never been written once.

A design's lifecycle is expressible entirely in values already in use:

| Status | Already used by | Means here |
|---|---|---|
| `draft` | requirement, workflow, plan, release | being authored, not yet offered |
| `proposed` | adr | offered for review |
| `accepted` | adr | approved, to be built |
| `implemented` | requirement | the design is built |
| `superseded` | adr, feature, requirement, … | replaced by a later design |
| `cancelled` | task, feature, requirement | abandoned without replacement |

So this adds a *type*, not a vocabulary. That is the cheap kind of taxonomy change.

## Links
- Tasks: [[TASK-0078]], [[TASK-0079]]
- Consumer: project-os-cockpit FEAT-0042 / PHASE-009

## Result

Landed 2026-07-27. Zero new status values, as designed — the six-value lifecycle is drawn entirely from values already in the vocabulary.

**The STATUS-TABLE guard earned its keep on its first real use.** The type was added to `COLLECTION_TYPE` and deliberately not to `ALLOWED_STATUS` first, to see whether the ISS-0016 guard would notice:

```
ERROR [STATUS-TABLE] COLLECTION_TYPE names note type(s) 'design' with no entry
in ALLOWED_STATUS; a type renamed in one table and not the other leaves the
check comparing against nothing
```

That is exactly the class of miss ISS-0011 through ISS-0016 were about, caught before it could reach a downstream repo. A guard nobody has watched catch a real change is a guard nobody has tested.

New checks, inversion-verified in a scratch fixture: `DESIGN-ASSET` fires on a missing asset file and on a note declaring none; `DESIGN-ORPHAN` fires on an artifact no note claims; `NOTE-STATUS` rejects an illegal design status.

One bug found while writing them: `parse_frontmatter` takes a *path*, and I passed it file contents. The validator reported `internal error: 'str' object has no attribute 'read_text'` and exited 2 — which is the right behaviour, and worth noting because it means a crash in a check does not silently pass.

Downstream, project-os-cockpit's `REF-0001` became `DES-0001` at `docs/designs/`, status `implemented` (PHASE-008 shipped from it — `accepted` would understate it). Twelve files repointed. Fleet: 11 repos, 0 errors, self-check ok, cockpit suite 330 passed.

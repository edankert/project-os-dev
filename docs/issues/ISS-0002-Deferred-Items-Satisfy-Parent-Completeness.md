---
type: "[[issue]]"
id: ISS-0002
aliases: ["ISS-0002"]
title: "Deferred items are treated as complete: parents close over them and parked work vanishes from every active surface"
status: fixed
severity: high
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
component: lifecycle-rules
source: []
related: [FEAT-0011]
tasks: []
---

# Deferred items are treated as complete

## Description

`deferred` is defined in `STATUSES.md` only as "parked", and nothing defines what a deferred child means for its parent's completeness. In practice deferred items end up counted as done and their parents get closed over them:

- `QUALITY.md` gates feature `done` on "its **required** tasks are `done`" — "required" is undefined, so an agent closing out a feature reads deferred children as not-required and closes the parent.
- The validator's feature-done check (`tools/scripts/validate-docs.py`, VERIFY) only inspects IDs still present in the feature's `tasks:` list, so silently dropping a deferred ID from the list passes clean. It is also equally strict about `cancelled`, which pressures agents into flipping parked tasks to `done` just to close the feature.
- Downstream the damage compounds: snapshot retention prunes `done` features, and the cockpit sorts `deferred` dead last — after `cancelled` and `reverted` — so a deferred item under a closed parent vanishes from every active surface. Nothing ever re-surfaces it.

## Impact

- Feature/phase completion reports overstate what was actually delivered.
- Deferred (still wanted!) work silently disappears: no home, no owner, no re-surfacing mechanism.
- Agents are structurally incentivised to fake-complete parked tasks to satisfy the validator.

## Action Required

Fix via [[FEAT-0011-Deferral-Descoping|FEAT-0011]]: make deferral an explicit descoping operation (detach from parent with `origin` provenance + forward home), harden the validator, and surface parked items until re-adopted or cancelled. Decision recorded in [[ADR-0005-Deferral-As-Descoping|ADR-0005]].

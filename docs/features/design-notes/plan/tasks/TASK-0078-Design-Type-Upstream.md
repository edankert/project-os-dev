---
type: "[[task]]"
id: TASK-0078
aliases: ["TASK-0078"]
title: "Add the design type upstream: taxonomy, statuses, template, validator, sync"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-07-27
updated: 2026-07-27
source: ["[[FEAT-0019]]"]
parent: "[[FEAT-0019]]"
effort: "M"
depends: []
blocks: ["[[TASK-0079]]"]
related: []
tests: []
---

# Add the design type upstream

## Definition of Done

- [x] `STATUSES.md` gains a `[[design]]` section: `draft`, `proposed`, `accepted`, `implemented`, `superseded`, `cancelled` — every value already in the vocabulary
- [x] `docs/__templates__/design.md` exists, carrying `asset:` and `implements:` and no `id:`-free surprises
- [x] `validate-docs.py`: `ALLOWED_STATUS["design"]`, `ID_PREFIXES += DES`, `COLLECTION_TYPE["designs"]`
- [x] `sync-snapshot.py`: `COLLECTION_OF["design"] = "designs"`
- [x] The template `SNAPSHOT.yaml` gains `counters.DES` and `items.designs`
- [x] `TRACEABILITY.md` records the design link graph (a design implements features; features name it via `design:`)
- [x] A validator check reports a design note whose `asset:` does not resolve
- [x] `--self-check` passes, and **fails** if the type is added to one status table and not another (inversion-verified)
- [x] Adapters regenerated; `generate-adapters.py --check` clean

## Steps

- [x] STATUSES.md section first — it is the source `load_allowed_status()` overlays
- [x] Template
- [x] Validator: all four tables in one pass, then `--self-check`
- [x] sync-snapshot collection map
- [x] Snapshot template
- [x] The `asset:` resolution check, with an inversion test
- [x] Regenerate adapters

## Notes

This is the first real exercise of the STATUS-TABLE completeness guard since ISS-0016 built it. Adding a type touches `ALLOWED_STATUS`, `COLLECTION_TYPE` and the type-table assertions; if any one is missed the guard should say so rather than the miss surviving to a downstream repo. **Do the edits deliberately incompletely once and confirm it fires** — a guard that has never been observed catching a real change is a guard nobody has tested on the case it was built for.

No `designs` metric. `METRIC_PREFIXES` is now checked against `METRIC_STATUS_FILTERS` in both directions (ISS-0016), so adding `DES` to one without the other would error — and counting designs answers no question anyone has asked.

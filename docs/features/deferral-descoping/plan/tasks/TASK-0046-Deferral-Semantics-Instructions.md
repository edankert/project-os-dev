---
type: "[[task]]"
id: TASK-0046
aliases: ["TASK-0046"]
title: "Define deferral-as-descoping semantics in instructions and schemas"
status: done
phase: []
owner: user:edwin
created: 2026-07-21
updated: 2026-07-21
verification_waiver: "docs-only change set; verified mechanically — validate-docs clean on template + project-os-dev, Allowed: lines byte-identical (load_allowed_status unaffected), generate-adapters --check clean after regeneration"
source: []
parent: "[[FEAT-0011-Deferral-Descoping]]"
effort: S
due: ""
depends: []
blocks: [TASK-0047, TASK-0048]
related: [ADR-0005]
tests: []
---

# Deferral semantics in instructions and schemas

## Definition of Done

- [x] `STATUSES.md`: a "Deferral and re-adoption" section defining `deferred` as non-terminal descoping; re-adoption transitions (`deferred` → `backlog`/`open`/`draft`) added for task/issue/feature/requirement. Allowed status sets unchanged.
- [x] `QUALITY.md`: scope-resolution rule replaces the ambiguous "required tasks" wording — feature `done` requires every item in `tasks:` to be `done` or `cancelled`; deferred children must be descoped first via the deferral procedure.
- [x] `SNAPSHOT.md`: retention explicitly keeps `deferred` items (they are active); metrics section documents `tasks_deferred`/`issues_deferred`; feature/task type-specific fields note `deferred`/`origin`.
- [x] `TRACEABILITY.md`: `origin` (former parent, provenance) and feature `deferred:` (descoped children) fields defined; task parent rule gains the deferred exception (origin + phase replace parent while parked).
- [x] `SCHEMAS.md`: `origin` documented as a common optional field; feature `deferred` list documented.

## Steps

- [x] Edit the five instruction/schema files in `~/Dev/repos/project-os`.
- [x] Keep `Allowed:` lines byte-compatible with the validator's `load_allowed_status` parser.

## Notes

Semantics per [[ADR-0005-Deferral-As-Descoping|ADR-0005]]: `done`/`cancelled` resolve scope, `deferred` leaves it; forward home is a future phase or the `PHASE-999` parking-lot sentinel (already counter-exempt in the validator).

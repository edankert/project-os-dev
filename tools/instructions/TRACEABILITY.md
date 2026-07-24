---
type: instruction
id: INSTR-TRACEABILITY
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [instructions, traceability]
---

# Traceability rules

This documentation system relies on explicit link graphs so agents can follow relationships reliably.

## Required links (minimum)
- Task (`[[task]]`)
  - Must have exactly one `parent` (feature or issue).
- Feature (`[[feature]]`)
  - Should link its `requirements` and `tasks` (frontmatter lists).
- Phase (`[[phase]]`)
  - Should link planned `features`, `requirements`, `tasks`, and `issues` when phase-gated development is used.
  - Items with a `phase` value should link back to the corresponding `PHASE-*` note where possible.
- Issue (`[[issue]]`)
  - Should link impacted `features` and/or planned `tasks` (frontmatter or `related`).
- Requirement (`[[requirement]]`)
  - Must have `acceptance` criteria.
  - Should link implementing features and verifying scripts/workflows.
- Test (`[[test]]`)
  - Should link the requirements it verifies (`requirements`) and any relevant features/issues/tasks.
- Risk (`[[risk]]`)
  - Should link mitigation tasks or the items it impacts.
- Change (`[[change]]`)
  - Should link `issues` and `features` impacted by the change.
- Decision (`[[adr]]`)
  - Should link related items and use `supersedes`/`superseded` when applicable.

## Snapshot alignment
- Represent the link graph in `../../SNAPSHOT.yaml` using IDs.
- The snapshot must include `file` paths for jump-to-source.

## Import provenance
- When deriving items from existing sources, record origin in note frontmatter `source` and/or Evidence sections.
- See `IMPORTING.md` for recommended conventions.

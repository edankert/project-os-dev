---
type: skill
id: SKILL-ADR-AUTHORING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, adr]
---

# Skill: ADR authoring

## When to use
- A cross-cutting decision is needed (schema, directory layout, conventions, contracts).

## Inputs
- Decision statement, context, alternatives, consequences.

## Outputs
- ADR note + snapshot decision entry.

## Checklist
1. Allocate the next `ADR-####` (use `../../../SNAPSHOT.yaml -> counters.ADR`).
2. Create `../../../docs/decisions/ADR-####-Short-Description.md` from `../../../docs/__templates__/adr.md`.
3. Update `../../../SNAPSHOT.yaml` under `items.decisions`:
   - include `file`, `title`, `status`, `owner`, `decision`, `context`, and relationships
4. If superseding a prior ADR, set `supersedes`/`superseded` in notes + snapshot.

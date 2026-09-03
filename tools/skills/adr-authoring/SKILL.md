---
type: skill
id: SKILL-ADR-AUTHORING
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-08-12
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
3. **If the decision is a quantified rule** (*every member of DOMAIN satisfies P*), it is a rule-ADR:
   - **Name the domain first, and stop if it cannot be enumerated** — `../../instructions/DECISIONS.md` ("A decision that states a rule", the `## Domain` bullet) owns why an unnameable domain ends the attempt. Often the registry that would enumerate it is the real first deliverable.
   - Uncomment and fill the template's `## Rule` / `## Domain` / `## Conformance` block. Semantics are normative in `../../instructions/DECISIONS.md` ("A decision that states a rule"); `DECISION-RULE` enforces them, so land the conformance rather than promising it.
   - Record provenance in `## Context`: a harvested rule cites the issue family that nominated it (see the sibling search in `../issue-intake/SKILL.md`); a from-principle rule says so and lands its conformance the same day.
4. Update `../../../SNAPSHOT.yaml` under `items.decisions`:
   - include `file`, `title`, `status`, `owner`, `decision`, `context`, and relationships
5. If superseding a prior ADR, set `supersedes`/`superseded` in notes + snapshot.

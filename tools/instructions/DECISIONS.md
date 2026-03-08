---
type: instruction
id: INSTR-DECISIONS
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [instructions, decisions]
---

# Decision records (ADRs)

Use ADRs (`../../docs/decisions/ADR-####-*.md`) for durable decisions that affect multiple files/flows.

## When to create an ADR
- A convention/contract changes (schemas, status models, directory layout).
- There are real alternatives with tradeoffs.
- A choice impacts more than one workflow or team.

## How to record ADRs
1. Create the ADR note from `../../docs/__templates__/adr.md`.
2. Add/update the entry in `../../SNAPSHOT.yaml` under `items.decisions`.
3. Link the ADR to impacted items via `related`.

## Superseding
- If ADR B replaces ADR A:
  - ADR B sets `supersedes: [[ADR-A]]`
  - ADR A sets `superseded: [[ADR-B]]` and status becomes `superseded`

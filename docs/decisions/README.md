---
type: reference
id: DECISIONS-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [decisions]
---

# `docs/decisions/`

Architecture Decision Records (ADRs) capturing **why** we chose a design/process.

## What goes here
- `ADR-####-*.md` notes created from `../__templates__/adr.md`.

## When to add an ADR
- When there are viable alternatives and you want a durable record of rationale/tradeoffs.
- When choosing/altering conventions that affect multiple scripts/flows (directory layout, naming, artifact locations).
- When defining/locking down an interface (JSON shapes, CLI contract, environment variables).

## When not to add an ADR
- Routine bug fixes or mechanical refactors: use `ISS-*` + `CHG-*` instead.

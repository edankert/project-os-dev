---
type: instruction
id: INSTR-TAXONOMY
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [instructions, taxonomy]
---

# Taxonomy (allowed values)

This file defines default allowed values for common fields so multiple agents/LLMs stay consistent.

Projects may override; if you do, update templates and any automation that assumes these values.

## `owner` (all notes)
See `OWNERSHIP.md` for allowed formats and the canonical registry.

## `severity` (issues)
- `low`, `medium`, `high`, `critical`

## `priority` (requirements)
- `low`, `medium`, `high`

## `order` (phases)
Positive integer sort order for roadmap sequencing.

## `effort` (tasks)
- `XS`, `S`, `M`, `L`, `XL`

## `likelihood` (risks)
- `low`, `medium`, `high`

## `impact` (risks)
- `low`, `medium`, `high`

## `component` (issues)
Project-defined free text label, but keep it stable. Examples:
- `docs`, `build`, `tests`, `tooling`, `runtime`, `ui`, `api`

## `kind` (tests)
- `manual`, `automated`

## `level` (tests)
- `unit`, `integration`, `system`, `e2e`

## `scope` (tests)
- `feature`, `system`

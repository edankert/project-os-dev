---
type: reference
id: ISSUES-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [issues]
---

# `docs/issues/`

Issue notes are the canonical place to describe **problems**, **gaps**, and **bugs** in the repo/flows.

## What goes here
- `ISS-####-*.md` created from `../__templates__/issue.md`.

## When to add an issue
- A script/flow breaks or is unclear (missing prerequisites, ambiguous artifact locations, wrong paths).
- A format contract isn’t met (JSON shape mismatch, parameter list drift).
- There’s a documentation gap that blocks adoption or on-call response.

## What to include
- Repro steps, expected vs actual behavior, and evidence paths/log excerpts.
- Link to affected areas/flows/workflows (and to `TASK-*` once work is planned).

---
type: "[[workflow]]"
id: WF-0003
title: "Recovery and resume"
status: draft
owner: group:maintainers
created: 2026-01-29
updated: 2026-01-29
entrypoints:
  - tools/skills/snapshot-sync/SKILL.md
prereqs:
  - access to SNAPSHOT.yaml and docs
inputs:
  - SNAPSHOT.yaml
  - docs/**
outputs:
  - reconciled snapshot and notes
  - resumed focus or reassigned claims
related:
  - ../INDEX.md
  - ../../tools/instructions/HANDOFF.md
---

# Recovery and resume

## When to use
- Work stopped unexpectedly or multiple agents need to coordinate safely.

## Entrypoint(s)
- `tools/skills/snapshot-sync/SKILL.md`

## Prerequisites
- Access to `SNAPSHOT.yaml` and docs notes.

## Inputs
- Snapshot and relevant notes for in-flight work.

## Outputs
- Updated snapshot (focus, session, claims) and aligned notes.

## Notes / Troubleshooting
- Clear or update stale `claimed_by` fields.
- Record the new `session.current_step` before resuming.

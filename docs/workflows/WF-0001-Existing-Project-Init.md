---
type: "[[workflow]]"
id: WF-0001
title: "Existing project derive"
status: draft
owner: group:maintainers
created: 2026-01-29
updated: 2026-01-29
entrypoints:
  - tools/skills/project-derive/SKILL.md
prereqs:
  - access to existing docs/issues/changelog/tests
inputs:
  - README.md
  - docs/**
  - issue tracker export (if available)
  - changelog / release notes
  - CI/test reports
outputs:
  - docs/** notes (issues/features/requirements/tests/changes)
  - SNAPSHOT.yaml (populated and aligned)
related:
  - ../INDEX.md
  - ../../tools/instructions/IMPORTING.md
---

# Existing project derive

## When to use
- You are enabling project-os for a repository with existing history and artifacts.

## Entrypoint(s)
- `tools/skills/project-derive/SKILL.md`

## Prerequisites
- Access to the canonical sources for project behavior and history.

## Inputs
- Existing docs, tracker exports, CI/test outputs, and release notes.

## Outputs
- Derived notes and a populated `SNAPSHOT.yaml` reflecting active work.

## Notes / Troubleshooting
- If sources are incomplete, mark derived items `triage` or `draft` and capture provenance.

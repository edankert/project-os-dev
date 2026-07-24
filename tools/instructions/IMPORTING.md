---
type: instruction
id: INSTR-IMPORTING
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-05-08
tags: [instructions, import]
---

# Importing / deriving from existing projects

Use this when initializing project-os for an existing project to capture provenance and avoid losing context.

## Goals
- Preserve origin context for derived items (issues, requirements, features, tests, changes).
- Preserve durable source/reference packages separately when they should not become active project-os lifecycle state.
- Make imported items traceable back to source artifacts.
- Keep uncertainty visible (triage/draft) until validated.

## Provenance conventions
- Prefer using a `source` frontmatter field (list of strings/links) on imported notes.
- For evidence, use the note body “Evidence” section and/or `evidence` frontmatter where available.
- For source packages, registries, background material, and publication inputs that should remain outside project-os lifecycle tracking, store them under `docs/reference/` or another clearly named non-lifecycle docs directory and link to them from derived notes.
- Examples of sources:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - issue tracker IDs (e.g. `GH-1234`, `JIRA-ABC-19`)
  - release notes or changelog entries
  - CI job URLs / test report paths

## Status guidance
- Use `status: triage` or `status: draft` for items inferred from partial sources.
- Promote to active/approved when verified by a maintainer.

## Snapshot expectations
- `SNAPSHOT.yaml` should include all **active** derived items and the correct counters.
- Keep closed/done history in notes; follow retention policy in `SNAPSHOT.yaml`.

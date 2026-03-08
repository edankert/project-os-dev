---
type: skill
id: SKILL-PROJECT-DERIVE
status: active
owner: group:maintainers
created: 2026-01-29
updated: 2026-01-29
tags: [skills, init, import]
---

# Skill: Project derive (existing project → project-os)

## When to use
- You want to initialize project-os for an **existing** project and derive as much context as possible.
- You need to map existing artifacts (docs, code, tests, changelog, issue tracker) into project-os items.

## Inputs
- Project name and short summary.
- Primary sources to ingest (README, docs, issue tracker, changelog, CI/test output, release notes).
- Repo entrypoints you want to capture as workflows.

## Outputs
- `../../../SNAPSHOT.yaml` populated with derived items and clean counters.
- New notes under `../../../docs/` (issues, features, requirements, tasks, tests, changes, decisions, workflows).
- Provenance captured for imported items (see `../../instructions/IMPORTING.md`).

## Rules
- `../../../SNAPSHOT.yaml` is canonical; keep it aligned with notes.
- Prefer faithful capture over speculation; use `status: triage` or `status: draft` when uncertain.
- Use templates in `../../../docs/__templates__/` for all new notes.
- Store provenance in note frontmatter (`source`) and/or Evidence sections.

## Checklist
1. Inventory sources (record in a scratch note or checklist):
   - README / existing docs / architecture notes
   - Issue tracker exports (GitHub/Jira/etc.)
   - Changelog / release notes
   - Test suites and CI output
   - Key workflows/scripts (build/test/deploy/run)
2. Map sources to item types:
   - Bugs/gaps → `ISS-*`
   - Capabilities → `FEAT-*`
   - Acceptance criteria → `REQ-*`
   - Verification → `TST-*`
   - Shipped changes → `CHG-*`
   - Decisions (if present) → `ADR-*`
   - Entry points → `WF-*`
3. Allocate IDs and draft notes using templates:
   - Keep titles short and stable
   - Link relationships (requirements ↔ features ↔ tasks ↔ tests)
   - Capture provenance in `source` / Evidence sections
4. Populate `../../../SNAPSHOT.yaml`:
   - set `template.replace_me: false` and update `project.*`
   - set `updated` to now
   - set counters to the highest allocated IDs
   - add entries under `items.*` for all active/relevant items
   - keep `focus` empty unless work is actively in-flight
5. Create or update workflow notes:
   - use `../workflow-authoring/SKILL.md`
   - link workflow IDs in features/tests as appropriate
6. Run `../snapshot-sync/SKILL.md` to validate alignment and metrics.

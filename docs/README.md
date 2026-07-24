---
type: reference
id: DOCS-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-05-08
tags: [docs]
---

# Docs structure

This folder is a reusable documentation system intended to be reused across projects (Obsidian-enabled; Obsidian optional). It can hold both structured project-os lifecycle records and normal project documentation.
Without Obsidian, the Markdown remains usable; Obsidian wiki-links (`[[...]]`) and `.base` files can be treated as plain text.

## How to add new docs
- Start from a template in `__templates__/`.
- Use stable IDs (`PHASE-####`, `ISS-####`, `FEAT-####`, `TASK-####`, `ADR-####`, `REQ-####`, `RISK-####`, `TST-####`, `CHG-YYYYMMDD-Short-Description`).
- Keep notes linked (issues → tasks → changes; requirements → features → verification).
- If using Obsidian, follow the Obsidian-enabled conventions in `../tools/instructions/OBSIDIAN.md`.

## Where things go
Structured project-os lifecycle records use these conventional locations:
- `workflows/`: canonical workflow entrypoints.
- `phases/`: optional milestone notes for phase-gated development.
- `issues/`: problem reports and gaps to fix.
- `features/`: feature definitions and planning (tasks live under each feature).
- `requirements/`: requirements and acceptance criteria (traceable to features/tests).
- `tests/`: system-wide/cross-feature test notes describing verification (manual or automated) and linking coverage.
- `decisions/`: ADRs for design and process decisions.
- `changes/`: change notes for traceability after merges.
- `risks/`: risks and mitigations.
- `PHASES.md`: phase registry overview for milestone-based development (optional phase-gating).
- `GLOSSARY.md`: shared terms.
- `OWNERSHIP.md`: canonical registry of `owner:` identities (teams, groups, users, systems).
- `__templates__/`: note templates (canonical front-matter keys and statuses).
- `__bases__/`: optional Bases definitions for navigation/context views (human-facing; LLM source of truth is `../SNAPSHOT.yaml`).

Some sections may be intentionally empty in this template; see the `README.md` inside those directories.

Normal project documentation also belongs under `docs/`. Use purpose-specific subdirectories for material that should be readable and linkable but should not become active project-os lifecycle state:
- `reference/`: source packages, evidence policies, registries, background material, datasets, publication source, and other durable supporting context.
- `research/`: investigation notes, discovery material, source analysis, and exploratory findings that support later project-os records.
- Project-specific directories such as `guides/`, `architecture/`, or `operations/` when the project needs them.

If a document is part of planning, tracking, status, decisions, requirements, verification, or change history, use the structured lifecycle directories above and the appropriate template. If the material is durable supporting context, keep it under `docs/reference/`, `docs/research/`, or another clearly named project-documentation directory.

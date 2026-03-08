---
type: reference
id: DOCS-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-01-26
tags: [docs]
---

# Docs structure

This folder is a reusable documentation system intended to be reused across projects (Obsidian-enabled; Obsidian optional).
Without Obsidian, the Markdown remains usable; Obsidian wiki-links (`[[...]]`) and `.base` files can be treated as plain text.

## How to add new docs
- Start from a template in `__templates__/`.
- Use stable IDs (`ISS-####`, `FEAT-####`, `TASK-####`, `ADR-####`, `REQ-####`, `RISK-####`, `TST-####`, `CHG-YYYYMMDD-Short-Description`).
- Keep notes linked (issues → tasks → changes; requirements → features → verification).
- If using Obsidian, follow the Obsidian-enabled conventions in `../tools/instructions/OBSIDIAN.md`.

## Where things go
- `dashboards/`: navigation pages and status views (often rendered via Bases).
- `workflows/`: canonical workflow entrypoints.
- `issues/`: problem reports and gaps to fix.
- `features/`: feature definitions and planning (tasks live under each feature).
- `requirements/`: requirements and acceptance criteria (traceable to features/tests).
- `tests/`: system-wide/cross-feature test notes describing verification (manual or automated) and linking coverage.
- `decisions/`: ADRs for design and process decisions.
- `changes/`: change notes for traceability after merges.
- `risks/`: risks and mitigations.
- `PHASES.md`: phase registry for milestone-based development (optional phase-gating).
- `GLOSSARY.md`: shared terms.
- `OWNERSHIP.md`: canonical registry of `owner:` identities (teams, groups, users, systems).
- `__templates__/`: note templates (canonical front-matter keys and statuses).
- `__bases__/`: optional Bases definitions for dashboards/views (human-facing; LLM source of truth is `../SNAPSHOT.yaml`).

Some sections may be intentionally empty in this template; see the `README.md` inside those directories.

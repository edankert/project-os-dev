---
type: reference
id: STYLE
status: reference
owner: group:maintainers
created: 2026-01-26
updated: 2026-01-26
tags: [styleguide]
---

# Styleguide (Reference)

Markdown conventions:
- Every note has YAML front-matter including `type`, `id`, `status`, `owner`, `created`, `updated`.
- For templated notes, set `type` to a link to the template file by filename (e.g. `[[issue]]`) and use `tags` only for topical labels.
- Follow Obsidian-specific conventions in `../tools/instructions/OBSIDIAN.md`.
- Use stable IDs (`ISS-####`, `FEAT-####`, `TASK-####`, `ADR-####`, `REQ-####`, `RISK-####`, `WF-####`, `CHG-YYYYMMDD-...`).
- Put “Next actions” at the end of work notes.
- Prefer file links to real repo entrypoints and artifacts (scripts, configs, logs).

Status conventions (canonical list lives in templates):
- Tasks: `backlog|next|doing|blocked|done`
- Issues: `triage|open|in-progress|blocked|fixed|closed`
- Features: `backlog|planned|in-progress|in-review|done`

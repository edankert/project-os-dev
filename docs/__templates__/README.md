---
type: reference
id: TEMPLATES-README
status: active
owner: team:docs
created: 2026-01-26
updated: 2026-07-17
tags: [templates]
---

# `docs/__templates__/`

Canonical templates for note types and their front-matter keys.

Field definitions: `[[SCHEMAS]]`.

## What goes here
- One template per note type (`phase.md`, `issue.md`, `feature.md`, `task.md`, `adr.md`, `change.md`, `workflow.md`, `release.md`, `plan.md`, etc.).
  - Includes `test.md` for manual/automated verification notes.
  - Includes `reference.md` for durable explanatory or registry-style documents.
  - Includes `acceptance-tests.md` for the older single-document form (`docs/tests/ACCEPTANCE_TESTS.md`). The current form is one `test.md` note per check at `level: acceptance`, stored per `tools/instructions/LIFECYCLE.md` "Test storage"; a repo that has migrated deletes that file rather than keeping both, and a repo that has not is unaffected (see `../../tools/instructions/TESTING.md`).

## How to use templates
- Copy the appropriate template into the target directory.
- Leave `type:` as-is: it points to the template file (and serves as the canonical note-type identifier).
- Assign the next stable `id:` and set `title:`, `status:`, `owner:`, and any type-specific fields.
- Use `owner:` values defined in `[[OWNERSHIP]]` (or `unassigned`).
- Name the file as `ID-Short-Description.md` (see `../../tools/instructions/OBSIDIAN.md`).
- Keep `created:` stable; bump `updated:` when materially changing content.

## When to change templates
- When you introduce a new cross-cutting metadata field used by views/queries.
- When a status taxonomy changes (update templates and any snapshot-driven views/processes that assume it).

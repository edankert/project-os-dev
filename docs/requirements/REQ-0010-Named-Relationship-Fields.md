---
type: "[[requirement]]"
id: REQ-0010
aliases: ["REQ-0010"]
title: "Named relationship fields with multi-parent support and Bases filterability"
status: superseded
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-07-21
source: []
priority: high
scope: "template-wide"
acceptance:
  - "Child notes use semantic named fields (implements, fixes, affects, specifies, validates) instead of generic parent"
  - "All relationship fields are lists, supporting multiple parent references"
  - "Obsidian Bases can filter notes using contains on the new list fields"
  - "Feature notes no longer maintain redundant child lists (tasks, requirements, tests)"
  - "Overview.base template filters on the new fields to show related items per feature"
superseded: "[[REQ-0015-Relationship-Model]]"
implements: ["[[FEAT-0007-Relationship-Model]]"]
verifies: []
related: [REQ-0015, ISS-0004]
tests: []
---

# Named Relationship Fields

## Statement

Child notes must use semantic named relationship fields that clearly describe the link type, support multiple values (list), and are filterable by Obsidian Bases `contains` operator.

**This requirement is superseded.** The design was built (template commit `f44f507`) and then deliberately reverted in May 2026 (`3ea57ad`, `7204242`; see `docs/changes/CHG-20260508-Remove-legacy-views-and-extra-bases.md` in the template repo). The relationship model the system actually runs on is specified by [[REQ-0015-Relationship-Model|REQ-0015]].

## Acceptance Criteria

None of these were delivered — the design was reverted, not completed. They stay unticked as the record of what was intended.

- [ ] `implements` (list) on tasks — **not delivered.** `implements` survives only on requirements and plans, pointing *up* to features; tasks use scalar `parent`.
- [ ] `fixes` (list) on tasks — **not delivered.** Field absent repo-wide.
- [ ] `affects` (list) on issues — **not delivered.** Issues use `parent`.
- [ ] `specifies` (list) on requirements — **not delivered.** Shipped as `implements:` instead; the rename was reverted.
- [ ] `validates` (list) on tests — **not delivered.** Shipped as four separate lists (`requirements`, `features`, `issues`, `tasks`).
- [ ] All fields default to `[]` — **partial only.** True for `implements:`; false for `parent: ""` (scalar).
- [ ] Feature frontmatter drops `tasks`/`requirements`/`tests` — **not delivered, and now load-bearing in the opposite direction.** Feature `tasks:` was re-added and [[FEAT-0011-Deferral-Descoping|FEAT-0011]] built scope enforcement on top of it: a feature's `tasks:` list *is* its scope of record.
- [ ] `Overview.base` uses `contains` — **not delivered.** `Overview.base` was never created; `CONTEXT.base` covers the role via `file.hasLink(this.file)`.

## Supersession record (2026-07-21)

Found during the [[ISS-0004-Requirements-Never-Advance|ISS-0004]] backfill: this requirement sat at `draft` while its implementing feature FEAT-0007 was `done`, describing a model the project had already abandoned. A reader following it would have implemented against a design that contradicts the current system — and would have broken FEAT-0011's deferral enforcement in the process.

Resolution: **superseded, not amended.** Amending five criteria that all failed would produce a different requirement wearing this one's ID; the honest record is that the intent was tried, reverted, and replaced. [[REQ-0015-Relationship-Model|REQ-0015]] specifies the model that shipped and is in force.

The frontmatter `acceptance:` list is deliberately left unamended — it is historical intent, not a live contract.

## Traceability

- Implements: [[FEAT-0007-Relationship-Model]]
- Superseded by: [[REQ-0015-Relationship-Model]]
- Reverted by: `docs/changes/CHG-20260508-Remove-legacy-views-and-extra-bases.md` (template repo)

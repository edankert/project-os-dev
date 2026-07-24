---
type: "[[feature]]"
id: FEAT-0007
aliases: ["FEAT-0007"]
title: "Named relationship fields with child-to-parent linking"
status: done
phase: []
platform:
owner: user:edwin
created: 2026-04-05
updated: 2026-07-21
source: []
goal: "Relationship model for linking notes. NOTE: the semantic-named-field design was reverted in May 2026; the model in force is specified by REQ-0015"
release: ""
related: [REQ-0015, REQ-0010]
---

# Named Relationship Fields

> **Superseded design (2026-07-21).** The named-relationship-field model described below was built and then deliberately reverted in May 2026 (`CHG-20260508-Remove-legacy-views-and-extra-bases` in the template repo). The relationship model actually in force is specified by [[REQ-0015-Relationship-Model|REQ-0015]] — scalar `parent` downward, `implements` upward, feature child lists as scope of record. [[REQ-0010-Named-Relationship-Fields|REQ-0010]] (this feature's original requirement) is superseded. Read this section as history, not as the contract.

## Goal
Replace the ambiguous `parent` and `implements` fields with semantic named relationship fields (`implements`, `fixes`, `affects`, `specifies`, `validates`) that:
- Clearly describe the relationship between notes
- Support multiple values (list fields) for notes with multiple parents
- Are reliably filterable by Obsidian Bases using `contains`
- Enable contextual Overview.base dashboards per feature

## Scope

**In scope:**
- New relationship fields: `implements`, `fixes`, `affects`, `specifies`, `validates`
- All fields are lists (support multiple parents)
- Update all templates, schemas, traceability rules, bases dashboards, and skills
- Update SNAPSHOT.yaml schema for requirement `implements` → `specifies`
- Remove redundant parent→child lists from feature frontmatter (`tasks`, `requirements`, `tests`)

**Out of scope:**
- Migrating existing notes in downstream repos (handled per-project)
- Changing `depends`/`blocks` on tasks (these are peer relationships, not parent)
- Changing `related` field (stays as generic cross-reference)

## Field Mapping

| Type | New Field | Replaces | Points to | Semantics |
|---|---|---|---|---|
| Task | `implements` | `parent` (when feature) | Feature(s) | "delivers this feature" |
| Task | `fixes` | `parent` (when issue) | Issue(s) | "resolves this issue" |
| Issue | `affects` | `parent` | Feature(s) | "found in this feature" |
| Requirement | `specifies` | `implements` | Feature(s) | "constrains this feature" |
| Test | `validates` | `features`/`requirements`/`issues` | Feature(s)/Req(s) | "verifies this item" |

All fields are **lists** to support multiple parents. A task can both `implements: [FEAT-0042]` and `fixes: [ISS-0015]`.

## Feature frontmatter changes
Remove `requirements`, `tasks`, `tests` lists — children point up via their named fields. The Overview.base replaces these with a live, always-accurate view.

Keep: `goal`, `release`, `related`.

## Acceptance
- All templates use named relationship fields instead of `parent`/`implements`
- SCHEMAS.md documents the new fields
- Overview.base filters using `contains` on the new list fields
- Feature-scaffold skill generates Overview.base with correct filters
- TRACEABILITY.md reflects the new link graph rules

## Links
- Requirements: [[REQ-0015-Relationship-Model]] (in force) — supersedes [[REQ-0010-Named-Relationship-Fields]] (original, reverted design)

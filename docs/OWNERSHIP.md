---
type: reference
id: OWNERSHIP
status: active
owner: team:docs
created: 2026-01-27
updated: 2026-01-27
tags: [ownership, teams, groups, users]
---

# Ownership registry

This file is the canonical registry for `owner:` identities used throughout `docs/`, `tools/`, and `SNAPSHOT.yaml`.

## Rules
- Every `owner:` value used anywhere must be defined in this file (or be `unassigned`).
- `team:*` and `group:*` must list membership (at minimum: maintainers/contacts).
- If a note is owned by a group/rotation, define who maintains the membership list.
- `system:*` owners are automation identities:
  - Do not list `system:*` under team/group “Maintainers” or “Members”.
  - Instead, list automation under an explicit “Automation” section for the owning team/group.

## Owner ID formats
- Teams: `team:<name>` (long-lived org units)
- Groups: `group:<name>` (cross-team working groups / rotations)
- Users: `user:<handle>` (individuals)
- Systems: `system:<name>` (automation identities)
- Unassigned: `unassigned`

## Teams

### `team:docs`
- Purpose: maintain this documentation system structure and authoring conventions.
- Maintainers:
  - `REPLACE ME (add user:<handle> list)`
- Members:
  - `REPLACE ME`
- Automation:
  - `REPLACE ME (e.g. system:llm)`

## Groups

### `group:maintainers`
- Purpose: maintain normative instructions (`tools/instructions/*`) and skills (`tools/skills/*`).
- Maintainers:
  - `REPLACE ME`
- Members:
  - `REPLACE ME`
- Automation:
  - `REPLACE ME (e.g. system:llm)`

## Users

Add one entry per person when you want explicit membership mapping.

### `user:REPLACE_ME`
- Name: `REPLACE ME` (optional)
- Teams: `REPLACE ME` (e.g. `team:docs`)
- Groups: `REPLACE ME` (e.g. `group:maintainers`)

## Systems

### `system:llm`
- Purpose: LLM/agent actions (when you want a non-human owner label).
  - Note: list this under a team/group “Automation” section when it is part of their tooling, but not as a human member.

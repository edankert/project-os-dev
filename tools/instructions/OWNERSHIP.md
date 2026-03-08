---
type: instruction
id: INSTR-OWNERSHIP
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [instructions, ownership]
---

# Ownership rules (`owner:`)

## Canonical registry
- The canonical registry of owners is `../../docs/OWNERSHIP.md`.
- Any `owner:` value used anywhere must be listed in that registry (or be `unassigned`).

## Allowed owner formats
- `team:<name>`: long-lived org unit responsible for the item
- `group:<name>`: cross-team group or rotation
- `user:<handle>`: individual
- `system:<name>`: automation identity
- `unassigned`: explicitly not owned yet

## Semantics
- `owner` means accountable for driving status forward and keeping `SNAPSHOT.yaml` + notes consistent.
- For work items:
  - `[[task]]`: implementer/assignee
  - `[[feature]]`: feature lead/coordinator
  - `[[issue]]`: triager/driver
  - `[[requirement]]`: stakeholder/approver
  - `[[risk]]`: risk steward
  - `[[test]]`: maintainer of the procedure/automation
  - `[[workflow]]`: maintainer of the canonical entrypoint

## Membership
- If `owner` is a `team:*` or `group:*`, membership/maintainers must be documented in `../../docs/OWNERSHIP.md`.
- If `owner` is a `group:*` rotation, `../../docs/OWNERSHIP.md` must specify who maintains the rotation list.
- `system:*` owners are automation identities and must not be treated as human members:
  - Do not list `system:*` under team/group “Maintainers” or “Members”.
  - If a team/group relies on automation, record it under an explicit “Automation” section in `../../docs/OWNERSHIP.md`.

## Defaults
- Use `unassigned` for new work items until someone takes ownership.
- Use `team:docs` for documentation-system structure and dashboards.
- Use `group:maintainers` for normative instructions and skills.

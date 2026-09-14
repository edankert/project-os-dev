---
type: skill
id: SKILL-CHANGE-NOTE
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, changes]
---

# Skill: Change note

## When to use
- After a change lands that affects users/flows/paths/contracts (scripts, env vars, outputs).

## Inputs
- Summary of what changed, why, and references (commit/PR if available).

## Outputs
- A new `../../../docs/changes/CHG-YYYYMMDD-Short-Description.md` note.
- `../../../SNAPSHOT.yaml` updated (`items.changes`) for the most recent/high-impact changes.

## Checklist
1. Create the change note from `../../../docs/__templates__/change.md`.
2. **Write the `## Impact` list: the screens this change altered.** Ask an LLM to draft it from the diff and the repo's `SUR-*` notes — one `[[SUR-####]]` link per screen, then one sentence a person using the product would understand. Then check every id against the surface notes; a link that resolves to nothing puts a screen on the walk sheet that nobody can open. A change that altered no screen writes `No screen changed` and the reason. The rule is `../../instructions/TESTING.md`, "The walk", rule 2; the shape a parser reads is `../../../docs/__templates__/SCHEMAS.md`, `change.md`.
3. Link the change to `issues:` and `features:` (use note links in the frontmatter).
4. Update `../../../SNAPSHOT.yaml`:
   - add/update an entry under `items.changes` for this change
5. If the change introduces new hazards, run `../risk-scan/SKILL.md`.

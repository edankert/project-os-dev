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
2. Link the change to `issues:` and `features:` (use note links in the frontmatter).
3. Update `../../../SNAPSHOT.yaml`:
   - add/update an entry under `items.changes` for this change
4. If the change introduces new hazards, run `../risk-scan/SKILL.md`.

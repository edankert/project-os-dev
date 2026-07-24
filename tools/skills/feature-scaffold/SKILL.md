---
type: skill
id: SKILL-FEATURE-SCAFFOLD
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, features]
---

# Skill: Feature scaffold

## When to use
- A prompt requests a new capability or significant enhancement (not just a bugfix).

## Inputs
- Feature request text, constraints, acceptance expectations, affected workflows/areas.
- Target phase (optional; consult `../../../docs/PHASES.md` for phase definitions).

## Outputs
- `../../../SNAPSHOT.yaml` updated (`items.requirements`, `items.features`, `items.tasks`, `focus`).
- A new feature folder under `../../../docs/features/<slug>/` containing:
  - `FEAT-####-Short-Description.md`
  - `plan/PLAN.md`
  - `plan/tasks/TASK-####-*.md` (initial breakdown)

## Checklist
1. Decide whether new `REQ-*` notes are needed (acceptance criteria that should outlive tasks).
2. **Determine phase assignment**:
   - Consult `../../../docs/PHASES.md` and any relevant `../../../docs/phases/PHASE-*.md` note for phase definitions and current active phase.
   - Assign a `phase` if the feature belongs to a specific milestone (`[[PHASE-####]]` preferred; leave empty if phase-gating not used).
   - Check `focus.phase` in snapshot for the currently active phase.
3. Allocate IDs (use `../../../SNAPSHOT.yaml -> counters`).
4. Update `../../../SNAPSHOT.yaml`:
   - create `items.requirements` (if needed) and link them to the feature
   - create `items.features.<FEAT-####>` with `goal`, `phase`, `requirements`, `tasks`, `workflows`
   - create initial `items.tasks` entries with `parent: FEAT-####` and inherit `phase` from feature
   - if `phase` is a `PHASE-*` ID, add the feature/task IDs to `items.phases.<PHASE-####>` and the phase note
   - set `focus.feature` and `focus.task` (if starting immediately)
   - update `focus.phase` if this feature represents a new active phase
5. Create the feature notes from templates:
   - requirement note(s): `../../../docs/__templates__/requirement.md` (set `phase` if applicable)
   - feature note: `../../../docs/__templates__/feature.md` (set `phase` in frontmatter)
   - plan: concise sequence for delivery
   - tasks: each with clear DoD and inherited `phase` from feature
6. **Impact analysis (mandatory for features with requirements):**
   - Run `../impact-analysis/SKILL.md` against new or linked requirements.
   - Check for conflicts with existing requirements on overlapping features.
   - If conflicts are found, stop and present resolution options before implementation.
7. **Risk scan:**
   - Review the feature against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
8. If the feature requires verification, create `TST-*` notes (use `../test-authoring/SKILL.md`) and link them from the feature/requirements/tasks.

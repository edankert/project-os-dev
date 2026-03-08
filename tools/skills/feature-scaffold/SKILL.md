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
   - Consult `../../../docs/PHASES.md` for phase definitions and current active phase.
   - Assign a `phase` if the feature belongs to a specific milestone (leave empty if phase-gating not used).
   - Check `focus.phase` in snapshot for the currently active phase.
3. Allocate IDs (use `../../../SNAPSHOT.yaml -> counters`).
4. Update `../../../SNAPSHOT.yaml`:
   - create `items.requirements` (if needed) and link them to the feature
   - create `items.features.<FEAT-####>` with `goal`, `phase`, `requirements`, `tasks`, `workflows`
   - create initial `items.tasks` entries with `parent: FEAT-####` and inherit `phase` from feature
   - set `focus.feature` and `focus.task` (if starting immediately)
   - update `focus.phase` if this feature represents a new active phase
5. Create the feature notes from templates:
   - requirement note(s): `../../../docs/__templates__/requirement.md` (set `phase` if applicable)
   - feature note: `../../../docs/__templates__/feature.md` (set `phase` in frontmatter)
   - plan: concise sequence for delivery
   - tasks: each with clear DoD and inherited `phase` from feature
6. **Impact analysis (mandatory for features with requirements):**
   - Run `../impact-analysis/SKILL.md` against any new or linked requirements.
   - Identify which existing features share the same component or user-facing area.
   - Check for tensions between the new feature's requirements and existing requirements on overlapping features.
   - If conflicts are found: STOP and present resolution options to the user before proceeding.
   - If no conflicts: note "Impact analysis complete — no conflicts" and proceed.
7. **Risk scan (mandatory check):**
   - Review the feature against risk scan triggers (see `../../instructions/LIFECYCLE.md` — Risk scan triggers section).
   - Check for: new dependencies, new env vars, path changes, performance changes, security/credential exposure.
   - If ANY trigger applies: run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no triggers apply: note "No new risks identified" and proceed.
8. If the feature requires verification, create `TST-*` notes (use `../test-authoring/SKILL.md`) and link them from the feature/requirements/tasks.

---
type: skill
id: SKILL-FEATURE-SCAFFOLD
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-04
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
  - `plan/tests/TST-####-*.md` — **one acceptance check, by rule** (see step 9)

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
   - If conflicts are found, how to resolve them is the user's decision (`../../instructions/LIFECYCLE.md`, "When to pause for the user").
7. **Requirement approval gate:**
   - The gate is `../../instructions/STATUSES.md` `[[feature]]`: approve the requirement (or amend it first, then approve) before the feature moves to `doing`.
   - Approval means the acceptance criteria are the ones you intend to build against; if the plan already departs from them, amend the requirement now rather than at close-out.
   - The requirement is advanced again at close-out (`../close-out/SKILL.md`, step 3 "Requirement advancement").
8. **Risk scan:**
   - Review the feature against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no trigger applies, record the negative result (`../../instructions/LIFECYCLE.md`, "Risk scan triggers").
9. **Emit one acceptance check beside the plan — by rule, not by judgement.**
   - Create `plan/tests/TST-####-*.md` from `../../../docs/__templates__/test.md` with `level: acceptance` and `covers: ["[[FEAT-####]]"]`. No `command:` — a check somebody walks.
   - **This is not conditional.** It used to read *"if the feature requires verification"*, and the answer was decided per feature, at the end, under time pressure. Measured across the twelve project-os repos on 2026-08-20: **236 features reached a terminal status with no acceptance check covering them** — 147 of those in the three repos that hold a suite at all. A rule applied when somebody remembers is not a rule.
   - **The escape is `acceptance_exception:` on the feature**, and it is what makes the rule honest rather than a thing people disable. The cases that qualify are listed once in `../../../docs/__templates__/SCHEMAS.md`, `feature.md`. Say so once, in the note, at scaffold time when the reason is actually known.
   - `FEATURE-UNCOVERED` warns at close-out for anything that is neither covered nor excepted, so the scaffold and the validator ask the same question at the two ends of the work.
   - For anything beyond the one acceptance check — unit, integration, regression — use `../test-authoring/SKILL.md` and link from the feature/requirements/tasks as before.

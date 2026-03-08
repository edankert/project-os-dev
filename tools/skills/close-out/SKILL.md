---
type: skill
id: SKILL-CLOSE-OUT
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, closeout]
---

# Skill: Close-out

## When to use
- At the end of an implementation task or when an issue is resolved.

## Inputs
- Completed task/issue/feature IDs.

## Outputs
- Updated statuses, optional change note, and cleaned focus.

## Checklist
1. **Verification gating (mandatory gate — do this FIRST):**
   - List all `TST-*` IDs linked to the task/issue being closed.
   - For each linked test, check its `status` in the snapshot and note.
   - If ANY linked test is not `status: passing`: **STOP. Do not transition to `done`/`closed`/`verified`.** Report which tests are blocking and what needs to happen before close-out can proceed.
   - If no tests are linked and the work is a functional code change: flag this to the user — verification may be missing. Create test notes if appropriate (use `../test-authoring/SKILL.md`).
   - Only proceed to step 2 once all linked tests are `passing` (or the user explicitly waives verification for this item).
2. Update notes:
   - task `status: done` (and `updated`)
   - issue `status: fixed/closed` if resolved
   - feature progress if milestones were reached
3. Update `../../../SNAPSHOT.yaml`:
   - set the same statuses
   - update relationships if new tasks/issues/risks were created
   - clear or move `focus` to the next task
   - update `metrics`
4. If user-facing behavior/paths/contracts changed:
   - create `../../../docs/changes/CHG-YYYYMMDD-Short-Description.md`
   - link it to `issues`/`features` in note + snapshot
5. **Risk scan (mandatory check):**
   - Review the completed work against risk scan triggers (see `../../instructions/LIFECYCLE.md` — Risk scan triggers section).
   - Check for: new dependencies, new env vars, path changes, performance changes, security/credential exposure.
   - If ANY trigger applies: run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no triggers apply: note "No new risks identified" and proceed.
6. **Retention enforcement:**
   - If the closed item matches the retention policy for pruning (e.g., `keep_done_tasks_in_snapshot: false` and task is now `done`): remove it from the snapshot. The note under `docs/` is the archive.
   - Update `metrics` counts after pruning.

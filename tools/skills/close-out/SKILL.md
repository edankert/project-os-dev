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
1. **Verification gating (mandatory first):**
   - List all `TST-*` IDs linked to the task/issue/requirement/feature being closed.
   - Verify each linked test is `status: passing` in the snapshot and note.
   - If any linked test is not passing, stop before applying terminal statuses and report the blocker.
   - If no tests are linked and the work is a functional code change, flag that verification may be missing and create test notes when appropriate.
2. Update notes:
   - task `status: done` (and `updated`)
   - issue `status: fixed/closed` if resolved
   - feature progress if milestones were reached
   - phase `status: done` only when its exit criteria and linked work are complete
3. Update `../../../SNAPSHOT.yaml`:
   - set the same statuses
   - update relationships if new tasks/issues/risks were created
   - clear or move `focus` to the next task
   - update `metrics`
4. If user-facing behavior/paths/contracts changed:
   - create `../../../docs/changes/CHG-YYYYMMDD-Short-Description.md`
   - link it to `issues`/`features` in note + snapshot
5. **Risk scan:**
   - Review the completed work against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no trigger applies, record that no new risks were identified in the relevant task/issue note or final summary.
6. **Mechanical validation:**
   - Run `bash tools/scripts/validate-docs.sh` and fix every reported error before finishing — the same validator gates pre-commit and CI.
7. **Independent review:**
   - If this close-out created/updated a `TST-*` or `CHG-*` note, or sets a requirement to `verified` / feature to `done`, run `../independent-review/SKILL.md` before applying the terminal status.
8. **Retention enforcement:**
   - Apply `retention` settings from `../../../SNAPSHOT.yaml`.
   - Preserve notes under `../../../docs/`; prune only snapshot entries when policy says to keep the snapshot active/recent.
   - Update `metrics` after pruning.

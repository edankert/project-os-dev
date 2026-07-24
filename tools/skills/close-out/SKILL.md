---
type: skill
id: SKILL-CLOSE-OUT
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-07-21
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
   - feature progress if milestones were reached; a feature may only go `done` when every task in its `tasks:` list is `done` or `cancelled` — a `deferred` ID in the list blocks the transition until descoped via `../status-transition/SKILL.md`, "Deferral procedure" (never flip a parked task to `done` or drop it silently)
   - phase `status: done` only when its exit criteria and linked work are complete
3. **Requirement advancement (mandatory when closing a feature):**
   - List every requirement linked to the closing feature (`requirements:` on the feature, `implements:` on the requirement — note the direction: a requirement's `implements` names the features that implement *it*).
   - Walk that requirement's acceptance criteria one by one. Tick each satisfied criterion in the note body with an evidence pointer (repo path, `path:line`, command, or note ID). A criterion with no evidence does not get ticked.
   - If the delivered work deliberately departed from a criterion, **reconcile it — never tick it to fit**: amend, narrow, or supersede it via `../impact-analysis/SKILL.md` and record what changed and why in an `## Amendments` section of the note. Silently rewriting or dropping a criterion destroys the audit trail.
   - Keep frontmatter `acceptance:` (criteria of record) and the body checkboxes (verification record) describing the same criteria; frontmatter wins where they disagree.
   - Set the requirement to `implemented` once **all** features listed in its `implements:` are `done`. If some are still open, leave the status and note which feature is outstanding.
   - If the last implementing feature ends `cancelled` or `superseded` rather than `done`, the requirement is not implemented — supersede it (link the successor) or cancel it. Leaving it at `draft`/`approved` is a validator error (REQ-STALE), which treats every terminal feature status as resolved.
   - `implemented → verified` remains gated on passing `[[test]]` notes (`../../instructions/QUALITY.md`); do not shortcut it.
4. Update `../../../SNAPSHOT.yaml`:
   - set the same statuses (including advanced requirements)
   - update relationships if new tasks/issues/risks were created
   - clear or move `focus` to the next task
   - update `metrics`
5. If user-facing behavior/paths/contracts changed:
   - create `../../../docs/changes/CHG-YYYYMMDD-Short-Description.md`
   - link it to `issues`/`features` in note + snapshot
6. **Risk scan:**
   - Review the completed work against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no trigger applies, record that no new risks were identified in the relevant task/issue note or final summary.
7. **Mechanical validation:**
   - Run `bash tools/scripts/validate-docs.sh` and fix every reported error before finishing — the same validator gates pre-commit and CI.
8. **Independent review:**
   - If this close-out created/updated a `TST-*` or `CHG-*` note, or sets a requirement to `verified` / feature to `done`, run `../independent-review/SKILL.md` before applying the terminal status.
9. **Retention enforcement:**
   - Apply `retention` settings from `../../../SNAPSHOT.yaml`.
   - Preserve notes under `../../../docs/`; prune only snapshot entries when policy says to keep the snapshot active/recent.
   - Update `metrics` after pruning.

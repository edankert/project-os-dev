---
type: skill
id: SKILL-CLOSE-OUT
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-04
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
   - If any linked test is not passing, the terminal status waits and the blocker is reported. Complete every other part of the close-out in full, then say exactly what was left out and why (`../../instructions/LIFECYCLE.md`, "When to pause for the user").
   - If no tests are linked and the work is a functional code change, flag that verification may be missing and create test notes when appropriate.
2. Update notes:
   - task `status: done` (and `updated`)
   - issue `status: fixed` if resolved
   - feature `status: done` only when its gate in `../../instructions/STATUSES.md` `[[feature]]` holds; a `deferred` ID in `tasks:` must first be descoped via `../status-transition/SKILL.md`, "Deferral procedure"
   - phase `status: done` only when its gate in `STATUSES.md` `[[phase]]` holds
   - **plan** `status` follows its feature (`STATUSES.md` `[[plan]]`); a plan left `active` under a shipped feature claims work is in flight that finished weeks ago (ISS-0010)
3. **Requirement advancement (mandatory when closing a feature):**
   - List every requirement linked to the closing feature (`requirements:` on the feature, `implements:` on the requirement; note the direction: a requirement's `implements` names the feature that implements *it*).
   - **This walk gates the close-out, it does not follow it.** The gate is `STATUSES.md` `[[feature]]`; this walk is how it is satisfied, and the requirement's status flip below is the consequence of the walk, not a precondition for it.
   - Walk that requirement's acceptance criteria one by one. Tick each satisfied criterion in the note body with an evidence pointer (repo path, `path:line`, command, or note ID). A criterion with no evidence does not get ticked.
   - If the delivered work deliberately departed from a criterion, **reconcile it — never tick it to fit**: amend, narrow, or supersede it via `../impact-analysis/SKILL.md` and record what changed and why in an `## Amendments` section of the note. Silently rewriting or dropping a criterion destroys the audit trail.
   - Keep frontmatter `acceptance:` (criteria of record) and the body checkboxes (verification record) describing the same criteria; frontmatter wins where they disagree.
   - Set the requirement to `implemented` once the feature named in its `implements:` is `done`. A requirement naming no feature is not advanced by any feature's close-out. The transitions themselves, including what happens when the feature ends `cancelled` or `superseded`, are stated once in `STATUSES.md` `[[requirement]]`.
4. `../../../SNAPSHOT.yaml`: the derived fields follow the notes (`../../instructions/LIFECYCLE.md`, "Mandatory Automated Documentation"). What still needs a decision:
   - add entries for genuinely new items, and prune per `retention` — membership is curation, not derivation
   - update relationships if new tasks/issues/risks were created
   - clear or move `focus` to the next task (`focus` is intent, and stays hand-authored)
5. If user-facing behavior/paths/contracts changed:
   - create `../../../docs/changes/CHG-YYYYMMDD-Short-Description.md`
   - link it to `issues`/`features` in note + snapshot
   - A document written for a person (a review, a report, a design) is filed as a `reference` note under `docs/reference/` in Markdown, from `../../../docs/__templates__/reference.md`; a page published outside the repo is a copy, and its URL goes in the note's `source:`. Reason: the cockpit lists reference notes and nothing lists a page on another host, so a deliverable that lives only there is invisible to the next session (project-os-dev ISS-0045).
6. **Risk scan:**
   - Review the completed work against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no trigger applies, record the negative result (`../../instructions/LIFECYCLE.md`, "Risk scan triggers").
7. **Mechanical validation:**
   - Run `bash tools/scripts/validate-docs.sh` and fix every reported error before finishing.
   - Before pushing and after, follow `../../instructions/LIFECYCLE.md` close-out steps 8 and 9 (`--as-committed`, then confirm the CI run went green).
8. **Independent review:**
   - At the review gates stated once in `../../instructions/QUALITY.md` ("Independent review (clean-context)"), run `../independent-review/SKILL.md` before applying the terminal status.
9. **Retention enforcement**: apply the policy in `../../instructions/SNAPSHOT.md` "Retention policy"; membership is curation the sync script leaves alone.

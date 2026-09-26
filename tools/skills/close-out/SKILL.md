---
type: skill
id: SKILL-CLOSE-OUT
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-18
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
   - Verify each linked test is `status: passing` in the snapshot and note. **Acceptance checks are excluded**: one rests at `active` and its verdict is an event in the release ledger, so `passing` is not a state it has (`../../instructions/STATUSES.md` `[[test]]`).
   - If any linked test is not passing, the terminal status waits and the blocker is reported. Complete every other part of the close-out in full, then say exactly what was left out and why (`../../instructions/LIFECYCLE.md`, "When to pause for the user").
   - If no tests are linked and the work is a functional code change, flag that verification may be missing and create test notes when appropriate.
2. Update notes:
   - task `status: done` (and `updated`)
   - issue `status: fixed` if resolved
   - feature `status: done` only when its gate in `../../instructions/STATUSES.md` `[[feature]]` holds; a `deferred` ID in `tasks:` must first be descoped via `../status-transition/SKILL.md`, "Deferral procedure"
   - feature `status: done`: first move the lasting facts up. Write what shipped, and why each non-obvious choice was made, into the feature note or an ADR. Its tasks and issues move to `docs/archive/` once the release is out (`tools/scripts/archive-notes.py`), and a reader should not have to open them to learn why the feature works the way it does. In your-trainer, the reason Android checks Strava when the app returns lived only in a task and an issue (project-os-dev ISS-0091).
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
6. **The screens this change altered, and the checks it reopened:**
   - **Write the change note's `## Impact` list.** Ask an LLM to draft it from the diff and the repo's `SUR-*` notes: one `[[SUR-####]]` link per screen altered, each with one sentence a person using the product would understand. Check that every id resolves to a surface note. A change that altered no screen writes `No screen changed` and the reason. This list is the only input a release walk's survey has, and it is recorded nowhere else (`../../instructions/TESTING.md`, "The walk", rule 2).
   - If the work changed a screen an acceptance check asserts against, also record an **invalidation event** in the working ledger for each such check, naming this change or task id. The ledger refuses it without one, and the reason on the event is why that check is owed again.
   - **These two are what the walk adds to close-out.** Do not enumerate the suite: name the screens this change actually altered and the checks that assert against them.
7. **Risk scan:**
   - Review the completed work against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no trigger applies, record the negative result (`../../instructions/LIFECYCLE.md`, "Risk scan triggers").
8. **Mechanical validation:**
   - Run `bash tools/scripts/validate-docs.sh` and fix every reported error before finishing.
   - Run the project's full test suite and fix every failing test, including one that failed before this work (`../../instructions/QUALITY.md`, "A failing test is fixed"). Record the run, with no failures, in the feature note's `## Verification`.
   - An error you cannot fix gets an `ISS-*` only under the filing bar in `../../instructions/QUALITY.md` ("The filing bar"). The issue carries the error's code and message word for word, and one open issue per code and subject is enough; add to it instead of filing a second. An error this work caused is fixed, never filed.
   - Before pushing and after, follow `../../instructions/LIFECYCLE.md` close-out steps 8 and 9 (`--as-committed`, then confirm the CI run went green).
9. **Independent review:**
   - At the review gates stated once in `../../instructions/QUALITY.md` ("Independent review (clean-context)"), run `../independent-review/SKILL.md` before applying the terminal status.
   - Fix what the review finds in this work before closing (ADR-0047). File only what the filing bar admits, and ask the owner any question in the close-out summary, with a recommendation, instead of leaving it in an issue.
10. **Retention enforcement**: apply the policy in `../../instructions/SNAPSHOT.md` "Retention policy"; membership is curation the sync script leaves alone.
11. **After a release is out**: run `python3 tools/scripts/archive-notes.py` to see which finished tasks, issues, change notes and retired checks it would move to `docs/archive/`, then `--apply`, sync, validate and commit the move on its own. Archived notes keep resolving by id, draw only structural findings, and are out of search through the repo `.ignore` (project-os-dev ISS-0091).

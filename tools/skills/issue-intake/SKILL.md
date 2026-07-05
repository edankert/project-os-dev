---
type: skill
id: SKILL-ISSUE-INTAKE
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-01-27
tags: [skills, issues]
---

# Skill: Issue intake

## When to use
- A prompt reports a bug, mismatch, broken workflow, unclear documentation, or unexpected behavior.

## Inputs
- User prompt, repro steps/logs, and any affected repo paths.

## Outputs
- `../../../SNAPSHOT.yaml` updated (`items.issues` + links to affected features/tasks).
- A new/updated `../../../docs/issues/ISS-####-Short-Description.md` note.
- Optional: new `TASK-*` entries/notes if work can be immediately planned.

## Checklist
1. **Spec-ambiguity check (before allocating any ID)** — ambiguity is upstream of documentation and no amount of tracking fixes an unclear ask. Treat these as unit tests for the request; if any fails, ask the user (or record the open question in the note and set `status: triage`) instead of guessing:
   - Every term in the request has one meaning in this project (no undefined nouns like "the importer" when two importers exist).
   - Expected vs actual behavior is stated observably (a command, input, and output — not "works properly").
   - Scope is bounded: it is clear what is explicitly NOT included.
   - Success is verifiable: you can already sketch the `TST-*` procedure that would prove the fix; if you cannot, the request is not specific enough.
   - No hidden conflicts: the request does not contradict an existing `REQ-*`/`ADR-*` (if unsure, run `../impact-analysis/SKILL.md` now rather than after implementation).
2. Assign the next `ISS-####` (use `../../../SNAPSHOT.yaml -> counters.ISS`).
3. **Determine phase (optional)**:
   - If the issue is tied to a specific milestone, assign a `phase` (consult `../../../docs/PHASES.md` and relevant `../../../docs/phases/PHASE-*.md` notes).
   - If the issue affects an existing feature, inherit phase from that feature.
   - Leave `phase` empty for issues not tied to a specific milestone.
4. Update `../../../SNAPSHOT.yaml`:
   - add `items.issues.<ISS-####>` with `title`, `status`, `severity`, `component`, `phase` (if applicable), `file`
   - link to impacted `features` and/or planned `tasks`
   - if `phase` is a `PHASE-*` ID, add the issue/task IDs to `items.phases.<PHASE-####>` and the phase note
   - set `focus.issue` if this is the current work
5. Create/update the issue note from `../../../docs/__templates__/issue.md`:
   - set `phase` in frontmatter if applicable
   - include repro, expected vs actual, evidence paths
6. If the fix requires implementation:
   - ensure there is a parent `FEAT-*` (create if needed)
   - create one or more `TASK-*` under the feature and link them in snapshot + notes
   - tasks inherit phase from the issue or parent feature
7. **Impact analysis:**
   - If the issue links to existing features, run `../impact-analysis/SKILL.md` to check whether the proposed fix may conflict with existing requirements.
   - If conflicts are found, stop and present resolution options before implementation.
8. **Risk scan:**
   - Review the issue against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
9. If verification is needed, create a `TST-*` note (use `../test-authoring/SKILL.md`) and link it from the issue/task/requirement as appropriate.

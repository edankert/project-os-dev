---
type: skill
id: SKILL-ISSUE-INTAKE
status: active
owner: group:maintainers
created: 2026-01-27
updated: 2026-09-04
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
1. **Spec-ambiguity check (before allocating any ID)** — ambiguity is upstream of documentation and no amount of tracking fixes an unclear ask. Treat these as unit tests for the request and run all five on every intake; the check is not conditional (ADR-0004), only the action on a failure is. The threshold is the same for all five: if the readings lead to materially different work, the reading is the user's decision, so ask, or record the open question in the note and set `status: triage` (`../../instructions/LIFECYCLE.md`, "When to pause for the user"). Otherwise implement the reading the wording most directly supports and record the assumption in the note, where the next reader can see it and dispute it:
   - Every term in the request has one meaning in this project (no undefined nouns like "the importer" when two importers exist).
   - Expected vs actual behavior is stated observably (a command, input, and output — not "works properly").
   - Scope is bounded: it is clear what is explicitly NOT included.
   - Success is verifiable: you can already sketch the `TST-*` procedure that would prove the fix; if you cannot, the request is not specific enough.
   - No hidden conflicts: the request does not contradict an existing `REQ-*`/`ADR-*` (if unsure, run `../impact-analysis/SKILL.md` now rather than after implementation).
2. **Sibling search (mandatory, before allocating any ID)** — ask once per intake: has an issue of this kind been filed here before? The search is **bounded**: grep this repo's `../../../docs/issues/` by keyword and by the surface the issue touches — a lookup, not a semantic read of the corpus. Record the outcome either way:
   - **No sibling:** one line in the issue note or final summary — *"no sibling found (searched: \<terms\>)"* — the same explicit negative the risk scan uses. That line is the entire cost in the common case, which is what keeps a mandatory step proportionate on the system's highest-frequency operation (the ADR-0016 concern). It stays mandatory rather than conditional because conditional steps get skipped by deciding the condition does not apply, even when it does (ADR-0004).
   - **A sibling exists:** this is the **second issue of its kind**, which is the harvest trigger — `../../instructions/DECISIONS.md` ("A decision that states a rule", the Provenance paragraph) owns why the second instance and not the first or the third. Still file this issue (it is a real instance), and **propose a rule-ADR covering the family** instead of leaving a third one-off to be filed later (`../adr-authoring/SKILL.md`). Link the sibling issues and the proposed rule to each other.
3. Assign the next `ISS-####` (use `../../../SNAPSHOT.yaml -> counters.ISS`).
4. **Determine phase (optional)**:
   - If the issue is tied to a specific milestone, assign a `phase` (consult `../../../docs/PHASES.md` and relevant `../../../docs/phases/PHASE-*.md` notes).
   - If the issue affects an existing feature, inherit phase from that feature.
   - Leave `phase` empty for issues not tied to a specific milestone.
5. Update `../../../SNAPSHOT.yaml`:
   - add `items.issues.<ISS-####>` with `title`, `status`, `severity`, `component`, `phase` (if applicable), `file`
   - link to impacted `features` and/or planned `tasks`
   - if `phase` is a `PHASE-*` ID, add the issue/task IDs to `items.phases.<PHASE-####>` and the phase note
   - set `focus.issue` if this is the current work
6. Create/update the issue note from `../../../docs/__templates__/issue.md`:
   - set `phase` in frontmatter if applicable
   - include repro, expected vs actual, evidence paths
   - put the reporter's words verbatim in the "As reported" callout under Problem, and keep your paraphrase outside it; a fix is judged against the sentence the reporter wrote
7. If the fix requires implementation:
   - ensure there is a parent `FEAT-*` (create if needed)
   - create one or more `TASK-*` under the feature and link them in snapshot + notes
   - tasks inherit phase from the issue or parent feature
8. **Impact analysis:**
   - If the issue links to existing features, run `../impact-analysis/SKILL.md` to check whether the proposed fix may conflict with existing requirements.
   - If conflicts are found, how to resolve them is the user's decision (`../../instructions/LIFECYCLE.md`, "When to pause for the user").
9. **Risk scan:**
   - Review the issue against risk scan triggers in `../../instructions/LIFECYCLE.md`.
   - If any trigger applies, run `../risk-scan/SKILL.md` and create/update `RISK-*` notes.
   - If no trigger applies, record the negative result (`../../instructions/LIFECYCLE.md`, "Risk scan triggers").
10. If verification is needed, create a `TST-*` note (use `../test-authoring/SKILL.md`) and link it from the issue/task/requirement as appropriate.

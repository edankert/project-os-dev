---
type: skill
id: SKILL-INDEPENDENT-REVIEW
status: active
owner: group:maintainers
created: 2026-07-05
updated: 2026-07-05
tags: [skills, review, verification]
---

# Skill: Independent review

## Why this exists
A model reviewing its own output shares its blind spots: same-family generation and review cluster errors in the same places, and self-approved fixes have been measured to contain correctness issues at material rates. Independence — a different model (or a human) reviewing with fresh context — is the active ingredient, not extra review passes by the author. This skill defines when an independent pass is required and how the notes/snapshot serve as the handoff surface.

## When to use
- A change creates or updates any `TST-*` note (the author of a fix must not be the sole judge of the test that guards it).
- A change carries a `CHG-*` note (behavior, paths, or contracts changed).
- A close-out would transition a requirement to `verified` or a feature to `done`.
- Any time a `verification_waiver` is being recorded (the waiver itself deserves a second pair of eyes).

## Inputs
- The diff (or changed file list) for the work being reviewed.
- The relevant notes: task/issue note, linked `TST-*` notes, the `CHG-*` note, and `../../../SNAPSHOT.yaml` focus/items entries. These are the handoff surface — the reviewer should be able to reconstruct intent from notes alone, without the author's conversation context.

## Outputs
- A review verdict recorded in the reviewed note's frontmatter:
  - `reviewed_by: <model-or-person identifier>` (e.g. `model:gpt-5.2`, `model:gemini-3-pro`, `user:edwin`)
  - `review_date: YYYY-MM-DD`
  - `review_verdict: approved | changes-requested`
- Findings filed as `ISS-*` notes (status `triage`) when the review surfaces defects.

## Independence rules
1. The reviewer must be a **different model family** than the author of the change, or a human. A second session of the same model is NOT independent — it reproduces the same blind spots.
2. The reviewer gets the notes and the diff, not the author's reasoning transcript. If the change cannot be justified from the notes alone, that is itself a finding (the documentation failed its handoff purpose).
3. The reviewer's job is to **refute**, not to confirm: actively look for inputs/states where the change is wrong, and for guarding tests that would still pass if the fix were reverted (a test that cannot fail does not guard).

## Checklist
1. Identify the review scope: changed files + the `TST-*`/`CHG-*` notes involved.
2. Launch the review with a different model (examples: a Claude Code subagent with a different-family model override, a Codex/Cursor session, or a human reviewer). Provide: the diff, the linked notes, and the acceptance criteria from any linked `REQ-*`.
3. Ask the reviewer for three explicit judgments:
   - **Correctness**: does the change do what the task/issue note says, and is there a concrete input/state where it fails?
   - **Guarding**: would each linked `TST-*` actually fail if the change were reverted or subtly broken? (If tooling is available, run mutation testing — see `../../instructions/TESTING.md`, "Test adequacy".)
   - **Consistency**: do the notes (status, links, CHG impact list) match what the diff actually does?
4. Record the verdict in the reviewed note frontmatter (`reviewed_by`, `review_date`, `review_verdict`).
5. If `changes-requested`: file `ISS-*` notes for the findings, keep the item out of terminal status, and loop.
6. If `approved`: proceed with close-out per `../close-out/SKILL.md`.

## What NOT to do
- Do not satisfy this skill by having the authoring model re-read its own diff — that is self-review wearing a badge.
- Do not skip the review because tests pass: the review exists precisely because author-written tests share the author's blind spots.

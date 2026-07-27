---
type: skill
id: SKILL-INDEPENDENT-REVIEW
status: active
owner: group:maintainers
created: 2026-07-05
updated: 2026-07-21
tags: [skills, review, verification]
---

# Skill: Independent review

## Why this exists
A session reviewing its own output shares its commitments: it watched the work being rationalised and inherits the conclusion. **Fresh context is the active ingredient** — a reviewer that never saw the author's reasoning approaches the artifact as a stranger.

That is a change from what this skill used to say, and it is evidence-backed rather than assumed (ADR-0013). The rule was "a different model family"; an experiment against the one case in the fleet with a known answer found a clean-context session of the *same model as the author* catching the defect the family rule predicted only a different family could catch — and describing it more accurately than the different-pin reviewer had. Family was a proxy; context is the mechanism.

Two kinds of correlation were being conflated. Shared **weights** correlate capability. Shared **context** correlates commitment. This fleet's misses have consistently been the second kind: claims written wider than the code, surviving because everyone arrived already holding the claim.

## When to use
- A change creates or updates any `TST-*` note (the author of a fix must not be the sole judge of the test that guards it).
- A change carries a `CHG-*` note (behavior, paths, or contracts changed).
- A close-out would transition a requirement to `implemented` or a feature to `done`.
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
1. The reviewer must start from a **clean context** — the notes and the diff, never the author's reasoning trace — and must not be the session that authored the work. A human pass also satisfies this. Model family is not the gate (ADR-0013); a different family is welcome and is no longer required. `reviewed_by` still records the model, as provenance rather than a compliance token: a later reader needs to know who reviewed, and a future finding about a specific model's blind spots needs the data. Record both sides when it is not obvious ("authored by model:X, reviewed by model:Y").
2. **Never write the verdict before the reviewer returns it.** `review_verdict` is transcribed from what the review actually returned, never anticipated, and never filled in "pending" optimism — recording an approval you expect to receive is the review-level version of ticking an acceptance criterion to fit. If a close-out needs the field present before the review lands, leave it empty and finish the close-out after the verdict arrives.
3. The reviewer gets the notes and the diff, not the author's reasoning transcript. If the change cannot be justified from the notes alone, that is itself a finding (the documentation failed its handoff purpose).
4. The reviewer's job is to **refute**, not to confirm: actively look for inputs/states where the change is wrong, and for guarding tests that would still pass if the fix were reverted (a test that cannot fail does not guard).

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

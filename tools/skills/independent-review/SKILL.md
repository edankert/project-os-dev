---
type: skill
id: SKILL-INDEPENDENT-REVIEW
status: active
owner: group:maintainers
created: 2026-07-05
updated: 2026-09-04
tags: [skills, review, verification]
---

# Skill: Independent review

## Why this exists
A session reviewing its own output shares its commitments: it watched the work being rationalised and inherits the conclusion. **Fresh context is the active ingredient** — a reviewer that never saw the author's reasoning approaches the artifact as a stranger.

That is a change from what this skill used to say, and it is evidence-backed rather than assumed (ADR-0013). The rule was "a different model family"; an experiment against the one case in the fleet with a known answer found a clean-context session of the *same model as the author* catching the defect the family rule predicted only a different family could catch — and describing it more accurately than the different-pin reviewer had. Family was a proxy; context is the mechanism.

Two kinds of correlation were being conflated. Shared **weights** correlate capability. Shared **context** correlates commitment. This fleet's misses have consistently been the second kind: claims written wider than the code, surviving because everyone arrived already holding the claim.

## When to use
- At the three review gates stated once in `../../instructions/QUALITY.md`, "Independent review (clean-context)"; a change note owes no review (ADR-0019).
- Optionally, when a `verification_waiver` is being recorded: the waiver deserves a second pair of eyes, though no gate requires it.

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
1. What makes a review independent is stated once in `../../instructions/QUALITY.md`, "Independent review (clean-context)". `reviewed_by` still records the model, as provenance rather than a compliance token: a later reader needs to know who reviewed, and a future finding about a specific model's blind spots needs the data. Record both sides when it is not obvious ("authored by model:X, reviewed by model:Y").
2. **Never write the verdict before the reviewer returns it.** `review_verdict` is transcribed from what the review actually returned, never anticipated, and never filled in "pending" optimism — recording an approval you expect to receive is the review-level version of ticking an acceptance criterion to fit. If a close-out needs the field present before the review lands, leave it empty and finish the close-out after the verdict arrives.
3. The reviewer gets the notes and the diff, not the author's reasoning transcript. If the change cannot be justified from the notes alone, that is itself a finding (the documentation failed its handoff purpose).
4. The reviewer's job is to **refute**, not to confirm: actively look for inputs/states where the change is wrong, and for guarding tests that would still pass if the fix were reverted (a test that cannot fail does not guard).

## Checklist
1. Identify the review scope: changed files + the `TST-*`/`CHG-*` notes involved.
2. Launch the review in a clean context that is not the authoring session (examples: a fresh Claude Code subagent such as `independent-reviewer`, a separate Codex or Cursor session, or a human reviewer). The rule is stated once, in `../../instructions/QUALITY.md` "Independent review (clean-context)". Provide: the diff, the linked notes, and the acceptance criteria from any linked `REQ-*`.
3. Ask the reviewer for three explicit judgments:
   - **Correctness**: does the change do what the task/issue note says, and is there a concrete input/state where it fails?
   - **Guarding**: would each linked `TST-*` actually fail if the change were reverted or subtly broken? (If tooling is available, run mutation testing — see `../../instructions/TESTING.md`, "Test adequacy".)
   - **Consistency**: do the notes (status, links, CHG impact list) match what the diff actually does?
   - Ask for **every finding**, each labelled **reproduced** (a command the reviewer ran and what it printed) or **not reproduced**. Do not tell the reviewer to be conservative, to report only high severity, or to omit what it could not reproduce: a reviewer told that an unreproduced finding is not a finding drops the plausible ones itself, and nobody downstream ever sees them. The filter belongs in step 5.
4. Record the verdict in the reviewed note frontmatter (`reviewed_by`, `review_date`, `review_verdict`).
5. If `changes-requested`: file `ISS-*` notes for the findings, keep the item out of terminal status, and loop. The repro filter applies here, at transcription, which is a separate pass by construction: a reproduced finding becomes an `ISS-*` at `triage` carrying its command and output; a finding the reviewer could not reproduce is recorded in the reviewed note's review section as a lead, and becomes an issue only once someone reproduces it.
6. If `approved`: proceed with close-out per `../close-out/SKILL.md`.

## What NOT to do
- Do not satisfy this skill by having the authoring model re-read its own diff — that is self-review wearing a badge.
- Do not skip the review because tests pass: the review exists precisely because author-written tests share the author's blind spots.
- Do not filter findings in the reviewer's prompt or output schema. Ask for everything; filter when transcribing.

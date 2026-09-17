---
type: skill
id: SKILL-WALK-PROCEDURE
status: active
owner: group:maintainers
created: 2026-09-14
updated: 2026-09-14
tags: [skills, testing, release, walk]
---

# Skill: Write or rewrite a sitting's procedure

## When to use
- `python3 tools/scripts/walk-sheet.py --check` reports that a sitting's procedure no longer covers what the release owes, or reports no procedure for a sitting at all.
- Before handing over a walk sheet, when the sitting's owed checks have changed since the procedure was written (`../release-prep/SKILL.md`, step 2a).

What a procedure is, what a step is, what a tag is, what an owed part is and what the validator refuses are stated once in `../../instructions/TESTING.md`, "The walk", rule 9. This skill restates none of it; it is the order of operations.

## Inputs
- The sitting: its `### ` heading, `state:` and `bench:` from `docs/tests/acceptance/WALK.md`.
- Every check that sitting claims — its `## Setup`, `## Steps` and `## Expect`, verbatim.
- The `SUR-*` notes, so each step can name the screen it happens on.
- The existing procedure, where there is one. Rewriting beats regenerating from nothing: the walker's own wording is worth keeping.

## Outputs
- `docs/tests/acceptance/walk/<name>.md`, from `../../../docs/__templates__/procedure.md`.
- A `--check` run that passes.

## Checklist

1. **Read every check in the sitting first, in full.** Do not work from titles. The procedure is a script over those notes and its expectation lines quote them word for word.
2. **Number the steps of any check whose procedure is unheaded prose**, in that check's own note, before citing it. Until you do, the whole check is one owed part and the procedure can only walk it as one thing (`TESTING.md`, "The walk", rule 9). Editing the check is expected here: a check is brought to its four headings when somebody is walking it ("A check is walkable by a stranger").
3. **Write the `## Setup` once**, as the state every step below assumes, in the register a check's own Setup line uses: what must be true, and the cheapest way to get there.
4. **Write the steps in the order a person can actually perform them.** One action per step. Start the first line with the screen — its `SUR-####` id or its exact title — then the action.
   If a later observation needs an earlier action whose own check may already have passed, declare it with `requires:`. Scope named setup items with `setup_for:` and put a changed required state in `state_for:`. Use `step_platforms:` for steps that exist on only one platform and `action_for:` for different paths to the same observation. Use `capture_for:` at the source and `use_capture:` at the later step when a comparison needs earlier evidence; include that source in `requires:`. Use `timer_for:` only for a wait with an authored duration in seconds. Mark known missing fixtures or unresolved decisions with `readiness_for:` and a concrete reason. The exact fields and validation rules are in `TESTING.md`, rule 9.
5. **Merge an action several checks share into one step.** That is the point of writing a procedure at all: your-trainer's REL-0017 sheet printed the same fake-trainer setup four times in one sitting. Merging happens at the step, not at the expectation: one action, then one expectation line per check that expects something from it.
6. **Under each step, write one expectation line per thing to observe.** Each one quotes a line of that check's `## Expect` section word for word and ends with its tags, `` `TST-####.N` ``. A line may carry more than one tag only when every check it names words that expectation identically — the validator compares the quote against each of them.
7. **Run `python3 tools/scripts/walk-sheet.py --check --platform <platform>`.** Fix what it names and run it again. **Keep the procedure only when it passes**: an unchecked procedure on a walk sheet is a list of things to do that may not be the things the release owes.
8. **Read what it says about coverage.** Covering every owed part is what the check requires; covering every live check in the sitting is the aim. Say which checks are not yet reached, and why, under `## Not covered here`.
9. Close out per `../../instructions/LIFECYCLE.md` — the procedure is a `reference` note and its sitting's owed set is what changed.

## What not to do

- **Do not invent a test observation no check asks for.** A procedure may retain a necessary preparation action, such as starting the ride needed by a later owed observation. Preparation has no verdict tag.
- **Do not drop an owed part** because it is awkward to reach. The validator will catch it; more to the point, the release owes it.
- **Do not paraphrase an `## Expect` line.** A tick recorded from a procedure step stands as a verdict on the check itself, and it only stands because the line says what the check says (project-os-cockpit ADR-0041). If the check's wording is wrong, fix the check's wording, in its note, and then quote the fixed line.
- **Do not widen the sitting to make the script work.** Two checks in one sitting whose setups genuinely conflict mean the sitting is wrong, and `WALK.md` is the owner's file: say which two checks conflict and ask, rather than splitting it yourself (`../../instructions/LIFECYCLE.md`, "When to pause for the user").
- **Do not write a duration** anywhere in it (`TESTING.md`, "The walk", rule 8).

---
type: skill
id: SKILL-RELEASE-TEST-PROCEDURE
status: active
owner: group:maintainers
created: 2026-09-14
updated: 2026-09-27
tags: [skills, testing, release, release-test]
---

# Skill: Write or rewrite a section's procedure

## When to use
- `python3 tools/scripts/release-test.py --check` reports that a section's procedure no longer covers what the release owes, or reports no procedure for a section at all.
- Before handing over a release test sheet, when the section's owed checks have changed since the procedure was written (`../release-prep/SKILL.md`, step 2b).

What a procedure is, what a step is, what a tag is, what an owed part is and what the validator refuses are stated once in `../../instructions/TESTING.md`, "The release test", rule 9. This skill restates none of it; it is the order of operations.

## Inputs
- The section: its `### ` heading, `state:` and `bench:` from `docs/tests/acceptance/RELEASE-TEST.md`.
- Every check that section claims — its `## Setup`, `## Steps` and `## Expect`, verbatim.
- The existing procedure, where there is one. Rewriting beats regenerating from nothing: the tester's own wording is worth keeping.

## Outputs
- `docs/tests/acceptance/release-test/<name>.md`, from `../../../docs/__templates__/procedure.md`, in the shape that template shows: groups under `### ` headings, a `Start:` line under each, one short action line per step, and tag-only lines under it.
- A `--check` run that passes with no warning about this procedure.

## Checklist

1. **Read every check in the section first, in full.** Do not work from titles. The procedure is a script over those notes, and the page prints their Expect lines under your actions.
2. **Number the steps of any check whose procedure is unheaded prose**, in that check's own note, before citing it. Until you do, the whole check is one owed part and the procedure can only test it as one thing (`TESTING.md`, "The release test", rule 9). Editing the check is expected here: a check is brought to its four headings when somebody is testing it ("A check is testable by a stranger").
3. **Write the `## Setup` as named items**, `- [trainer] Connect the fake trainer.`, one thing to do each, and map each id in `setup_for:`. An item every step needs is `all`, and the page prints it under "Before you start". An item only some steps need names them, and the page prints it under "Later" with the number of the first check that needs it. Things to have on the bench belong in the section's `bench:` in `RELEASE-TEST.md`, not here.
4. **Sort the steps into groups that start from the same state.** Give each group a `### ` heading that says what its steps have in common, such as "Hub layout" or "Power from a separate source". Under the heading, write one `Start:` line: what the app and the bench must look like before the group's first step. The page prints it once, and again only after skipped steps. Do not use `state_for:`; `--check` warns about it.
5. **Write each step as one short action line**, at most about 20 words: what to do, not what to see. It does not name the screen. Put the steps in the order a person can actually perform them, one action each. If a later observation needs an earlier action whose own check may already have passed, declare it with `requires:`. Use `step_platforms:` for a step that exists on only one platform and `action_for:` for different paths to the same observation. Use `capture_for:` at the source and `use_capture:` at the later step when a comparison needs earlier evidence, and include that source in `requires:`. Use `timer_for:` only for a wait with an authored duration in seconds. The exact fields and validation rules are in `TESTING.md`, rule 9.
6. **Merge an action several checks share into one step.** That is the point of writing a procedure at all: your-trainer's REL-0017 sheet printed the same fake-trainer setup four times in one section. Merging happens at the step, not at the expectation: one action, then one tag line per check step it tests.
7. **Under each step, write the tags alone**, `` - `TST-####.N` ``, one line per check step it tests. Never quote the Expect text: the page prints the check's current Expect line for this platform in its place (project-os-dev ADR-0050 D2). If that line is too long or mixes both platforms, shorten it in the check note itself, one line per platform marked `[android]` or `[ios]` (`TESTING.md`, "A check is testable by a stranger"). A change of meaning there is a change to the check.
8. **Mark what cannot be done as written** with `readiness_for:` on the step: `kind: preparation` for a missing fixture, device or control, `kind: decision` for an open product question, a one-line `reason`, the `issue` when there is one, and `result:` when the result to offer is not the default. Two examples from the approved Equipment Hub page: a setup nobody can build yet is `{kind: preparation, reason: "No way to set this up yet.", issue: "ISS-0512"}`, which suggests Blocked; hardware nobody owns is `{kind: preparation, reason: "Nobody owns one.", result: excused}`.
9. **Run `python3 tools/scripts/release-test.py --check --platform <platform>`** for each platform the section is tested on. Fix every error and every warning it names about this procedure, including lines over their word limit, and run it again. **Keep the procedure only when it passes**: an unchecked procedure on a release test sheet is a list of things to do that may not be the things the release owes.
10. **Generate the section and read it as the tester will**: `python3 tools/scripts/release-test.py --release REL-#### --platform <platform>`. Each check should read as one action and one expected line. Where an expected line is still long, go back to step 7.
11. **Read what `--check` says about coverage.** Covering every owed part is what the check requires; covering every live check in the section is the aim. Say which checks are not yet reached, and why, under `## Not covered here`.
12. Close out per `../../instructions/LIFECYCLE.md` — the procedure is a `reference` note and its section's owed set is what changed.

## What not to do

- **Do not invent a test observation no check asks for.** A procedure may retain a necessary preparation action, such as starting the ride needed by a later owed observation. Preparation has no result tag.
- **Do not drop an owed part** because it is awkward to reach. The validator will catch it; more to the point, the release owes it. Mark it with `readiness_for:` instead.
- **Do not quote or paraphrase an `## Expect` line** in the procedure. A tick recorded from a procedure step stands as a result on the check itself only because the tester read the check's own words (project-os-cockpit ADR-0041). If the check's wording is wrong or long, fix it in the check's note.
- **Do not put a screen name, a step number or a restated start state in an action line.** The group's heading and `Start:` line carry the state, and the page numbers the checks itself. Refer to another check by what it does, not by its number: the printed numbers change with what a release owes.
- **Do not widen the section to make the script work.** Two checks in one section whose setups genuinely conflict mean the section is wrong, and `RELEASE-TEST.md` is the owner's file: say which two checks conflict and ask, rather than splitting it yourself (`../../instructions/LIFECYCLE.md`, "When to pause for the user").
- **Do not write a duration** anywhere in it (`TESTING.md`, "The release test", rule 8).

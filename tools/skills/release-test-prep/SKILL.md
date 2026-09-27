---
type: skill
id: SKILL-RELEASE-TEST-PREP
status: active
owner: group:maintainers
created: 2026-09-27
updated: 2026-09-27
tags: [skills, testing, release, release-test]
---

# Skill: Prepare a release for testing

## When to use
- The owner asks to prepare a release for testing, such as "prepare v2.3.0 for testing".
- From `../release-prep/SKILL.md`, before the release test is handed over.

This skill turns that request into one pass over every platform the release is tested on. An agent writes the words: the procedures, the what-changed lines and the shorter Expect lines. Code still draws the page, keeps the progress and writes results to the ledger (project-os-dev ADR-0050, D3). What the page is and what its checks mean are stated once in `../../instructions/TESTING.md`, "The release test"; this skill is the order of operations.

## Inputs
- The release note, `docs/releases/REL-####-*.md`, and the platforms it is tested on.
- `docs/tests/acceptance/RELEASE-TEST.md`: the sections, their `gallery:` command and any `length_limits:`.
- The ledgers under `docs/releases/ledgers/`, the change notes added since each platform's last release tag, and the acceptance checks.

## Outputs
- Current screenshots in `docs/tests/acceptance/gallery/candidate/`.
- A procedure in the approved shape for every section whose owed checks changed.
- `docs/tests/acceptance/release-test/what-changed-<platform>.md` for each platform, from `../../../docs/__templates__/what-changed.md`.
- Expect lines short enough for the length check, split per platform where they differ.
- A `--check` run with no error and no length warning, and the release test opened in the cockpit.

## Checklist

Do the steps in this order, for each platform the release is tested on. Keep a list, as you go, of what you changed and of what needs the owner.

1. **Screenshots.** Run the command the section order file names in `gallery:`. A project with no `gallery:` skips this step and says so. Then generate the page, `python3 tools/scripts/release-test.py --release REL-#### --platform <platform>`, and list every picture it flags as older than the change it should show. Recapture those, or list them for the owner when they need a device you cannot drive.
2. **Changed sections.** Run `python3 tools/scripts/release-test.py --check --platform <platform>`. A section needs work when its procedure is refused, when it has no procedure, or when the length check names it. Touch only those sections, and say which ones you left alone and why.
3. **Procedures.** For each section that needs work, write or rewrite its procedure with `../release-test-procedure/SKILL.md`: groups with a `Start:` line, one short action per step, tag-only lines, setup items the page can split into "On the bench", "Before you start" and "Later", and each check that cannot be done as written marked with `readiness_for:` and its suggested result.
4. **What changed.** Write `docs/tests/acceptance/release-test/what-changed-<platform>.md` with `tag:` set to the platform's last release tag. For each change note added since that tag, and each screen its Impact list names on this platform, write one line: the screen, a colon, one sentence of at most 25 words saying what a person sees now, and the change note as a `[[CHG-...]]` link. Read the Impact sentence and, where it is unclear, the diff. A change note with no `platforms:` gets one here: decide from its Impact lines and its diff which platforms it changed, and add the field to the note. Leave out a line for a platform the change did not touch.
5. **Expect lines.** For each expected line the length check reports, shorten it in the check note itself, keeping what the tester must see. Split a line that describes both platforms into an `[android]` line and an `[ios]` line (`TESTING.md`, "A check is testable by a stranger"). **A change of meaning is a change to the check**: if the shorter line asks for something different, the check is owed again: record an invalidation for it in each platform's ledger, naming the task this preparation runs under and the reason (`../../instructions/TESTING.md`, "When to invalidate"). Ask the owner first when the check has already passed for this release. Shortening the same words is not a change of meaning.
6. **Checks.** Run `python3 tools/scripts/release-test.py --check --platform <platform>` and `bash tools/scripts/validate-docs.sh`. Keep your edits only when both pass with no length warning for the sections you touched. Where a line cannot be shortened without losing what the check asks, leave it, and list it for the owner.
7. **Hand over.** Generate the page for each platform, open the release test in the cockpit's Tests pane so the owner can look it over before testing starts, and end with two short lists: what you changed, by section; and what needs the owner, such as pictures you could not recapture, checks marked blocked, and meaning changes you made.

## What not to do

- **Do not change what a check asks for without reopening it.** A result stands for the check's own words; changing the words under a pass makes that pass claim something nobody tested (project-os-cockpit ADR-0041).
- **Do not rewrite a section nothing flagged.** A procedure the tester already knows is worth more than a fresher one.
- **Do not write expected results into a procedure.** They live in the check notes, one line per platform where they differ (ADR-0050, D2).
- **Do not record a result.** Preparing the release test is not testing it.
- **Do not write a duration** anywhere (`TESTING.md`, "The release test", rule 8).

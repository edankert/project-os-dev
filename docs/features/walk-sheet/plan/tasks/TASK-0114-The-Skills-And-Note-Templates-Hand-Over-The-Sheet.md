---
type: "[[task]]"
id: TASK-0114
aliases: ["TASK-0114"]
title: "release-prep generates the sheet, release-verification walks it, close-out records the invalidations, and the task and change templates offer 'Acceptance checks reopened'"
status: done
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]] rules 2, 6 and 8", "[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]"]
parent: "[[FEAT-0029-The-Walk-Sheet]]"
effort: M
due: ""
depends: ["[[TASK-0111-TESTING-md-States-The-Walk-Once]]"]
blocks: ["[[TASK-0115-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[ISS-0046-Release-Verification-Still-Writes-Test-Verdicts-By-Hand]]", "[[ISS-0060-The-Acceptance-Gate-Reads-A-Mark-And-Never-The-Ledger]]", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]"]
tests: []
---

# The skills hand over a sheet, not a list

## What

Three skills and two note templates change so that the sheet is what an agent hands the person preparing a release, and so that the survey has something to read. Today release-prep step 2 says "list every check it calls a blocker" and release-verification step 7 says "present the procedure to the user for execution", one check at a time. Step 7.4 still writes `status: passing` and `last_verified:` onto acceptance notes, which the ledger model retired (STATUSES.md, `level: acceptance`; ISS-0046).

## Definition of Done

- [x] `~/Dev/repos/project-os/tools/skills/release-prep/SKILL.md` step 2 runs `python3 tools/scripts/walk-sheet.py --release <REL> --platform <platform>` for each platform the release note names, reports the owed count and the sitting count, and links the sheet from the release note's Verification section. The step links to TESTING.md "The walk" and restates no rule.
- [x] `~/Dev/repos/project-os/tools/skills/release-verification/SKILL.md` step 7 says the person walks the sheet in its order, sitting by sitting, and records each verdict as a ledger event through the cockpit or the ledger write path. Step 7.4 no longer writes `status:` or `last_verified:` onto an acceptance note. The release test matrix in step 4 gains a column "Sitting" filled from the sheet so the matrix and the sheet agree on order.
- [x] `~/Dev/repos/project-os/tools/skills/close-out/SKILL.md` gains one step: for a change that alters a surface an acceptance check asserts against, record an invalidation event in the working ledger naming the change id for each such check, and optionally write `## Acceptance checks reopened` on the task or change note naming the screens and the checks, or "None" with the reason. The step says this is the only close-out action the walk adds and links to TESTING.md "The walk" rule 2. Step 1's "verify each linked test is status: passing" excludes acceptance checks, which rest at `active`.
- [x] `~/Dev/repos/project-os/docs/__templates__/task.md` and `docs/__templates__/change.md` carry `## Acceptance checks reopened` as a commented-out section with a one-line comment: name the checks this change reopens and the screens to look at, or write "None" and why.
- [x] `~/Dev/repos/project-os/tools/skills/test-authoring/SKILL.md` gains one line: an acceptance check that depends on another passing first names it in `after:`.
- [x] `bash tools/scripts/validate-docs.sh` is clean and the template's skill tests, where they exist, pass.

## Steps

- [x] Edit release-prep step 2 and the release note template's Verification section (one line: "Walk sheet: `<path or command>`").
- [x] Edit release-verification steps 4, 7 and 7.4; remove the note-writing instruction rather than softening it.
- [x] Edit close-out: add the step after the change-note step, and amend step 1.
- [x] Edit task.md and change.md.
- [x] Edit test-authoring.
- [x] Validate and run the skill tests.

## Notes

- your-trainer already writes `## Acceptance checks reopened` on 33 task notes by convention, with "None" and a reason as the common case. The template section makes that convention visible; it does not make it mandatory. Rule 2 of ADR-0029 depends on the invalidation event, which is already refused without a change id, not on this section.
- The close-out step must not become the sweep the cockpit's ADR-0036 withdrew. It asks for an event per reopened check and nothing when nothing is reopened; it does not ask the agent to enumerate the suite.

## Evidence

- **release-prep step 2** is now "Generate the walk sheet": one `walk-sheet.py` run per platform the release note names, the owed and sitting counts reported, and the sheet linked from the release note. It says what an "Unplaced" row means and keeps one line for a repo that has not migrated and so has no ledger. It links TESTING.md "The walk" and restates no rule.
- **release-verification step 4** gains a **Sitting** column filled from the sheet, with one line saying why: the matrix and the sheet then agree on the order instead of offering two.
- **release-verification step 7** is now "Walk the sheet, and re-run the other tests". The person walks the survey first, then sitting by sitting; every row carries its own procedure; every verdict is a ledger event with `method: manual`. The instruction to write `status:` and `last_verified:` onto an acceptance note is **removed**, not softened (ISS-0046). A manual test that is not an acceptance check keeps its old treatment in one paragraph.
- **close-out** gains step 6, the invalidation events and the optional `## Acceptance checks reopened` section, with the sentence that it asks nothing when nothing was reopened and must not become a sweep of the suite. Steps 6 to 9 became 7 to 10; the four files that cite close-out step 3 are unaffected.
- **close-out step 1** now excludes acceptance checks from "verify each linked test is `status: passing`": one rests at `active` and `passing` is not a state it has.
- **`docs/__templates__/task.md` and `change.md`** carry `## Acceptance checks reopened` commented out, with the one-line instruction and the note that the ledger event, not the section, is what the gate reads.
- **`docs/__templates__/release.md`** Verification section opens with the walk sheet line.
- **test-authoring** gains the `after:` line under the acceptance branch.
- `bash tools/scripts/validate-docs.sh` is OK; all seven template test scripts pass (74, 15, 31, 3, 32, 26, 23 assertions, 0 failures); `generate-adapters.py --check` reports all 35 artifacts current.

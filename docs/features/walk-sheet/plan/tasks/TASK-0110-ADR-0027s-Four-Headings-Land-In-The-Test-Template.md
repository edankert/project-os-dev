---
type: "[[task]]"
id: TASK-0110
aliases: ["TASK-0110"]
title: "ADR-0027's four headings, Setup, Steps, Expect and Not this check, land in the test template, TESTING.md and the test-authoring skill"
status: done
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]] rule 5"]
parent: "[[FEAT-0029-The-Walk-Sheet]]"
effort: S
due: ""
depends: []
blocks: ["[[TASK-0113-The-Generator-And-Its-Fixture-Test]]"]
related: ["[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]"]
tests: []
---

# The headings a sheet row prints

## What

A new acceptance check is born with four headings, Setup, Steps, Expect and Not this check, because the walk sheet prints the first three of them for every row. ADR-0027 proposed the shape on 2026-09-06 and nothing has landed; the template's `docs/__templates__/test.md` still has Purpose, Procedure, Expected results, Evidence and Adequacy. This task lands the headings only. ADR-0027's validator rule for a check missing them stays on that ADR's own acceptance thread.

## Definition of Done

- [x] `~/Dev/repos/project-os/docs/__templates__/test.md` carries `## Setup`, `## Steps`, `## Expect` and `## Not this check` under the acceptance-only block, each with a one-line comment saying what goes there in ADR-0027's words: Setup is the state the walk needs and the cheapest way to reach it; Steps are numbered, one action each; Expect is one observable line per assertion in the surface's own words; Not this check is the boundary and the check that covers it.
- [x] `~/Dev/repos/project-os/tools/instructions/TESTING.md` states the shape once, in a short subsection under "Where the acceptance suite lives", and says provenance goes below the procedure or into frontmatter.
- [x] `~/Dev/repos/project-os/tools/skills/test-authoring/SKILL.md` step 3's manual branch links to that subsection instead of "write an unambiguous procedure and expected results", and no longer says to leave an acceptance check at `status: ready` (an acceptance check rests at `active`, STATUSES.md).
- [x] The existing headings for a non-acceptance manual test are untouched; only the acceptance block changes.
- [x] `bash tools/scripts/validate-docs.sh` in the template is clean, and the template's own test scripts still pass.

## Steps

- [x] Read ADR-0027's Decision section and copy its four definitions verbatim into the template comments; do not paraphrase, because the ADR is where the wording was argued.
- [x] Edit `docs/__templates__/test.md`: replace the acceptance-only fenced block's body so it carries `area:` (unchanged) and the four headings below the frontmatter, and leave the executable-test headings as they are.
- [x] Edit `tools/instructions/TESTING.md`: add the subsection, six to ten lines, linking to ADR-0027 by its project-os-dev id in prose.
- [x] Edit `tools/skills/test-authoring/SKILL.md` step 3.
- [x] Run `bash tools/scripts/validate-docs.sh` and the template's test scripts.

## Notes

- Existing corpora are rewritten on contact, never swept (ADR-0027). This task touches no consumer's checks. The sheet's "Setup: not stated" label (TASK-0113) is what brings a check into contact.
- ADR-0027 also proposes a title rule, seven to ten words, one clause. That is guidance, not a heading, and belongs to ADR-0027's acceptance box 3; leave it out of this task.

## Evidence

- `~/Dev/repos/project-os/docs/__templates__/test.md` carries `## Setup`, `## Steps`, `## Expect` and `## Not this check` in an acceptance-only block, delimited by two HTML comments, with ADR-0027's own wording in each placeholder. `Procedure` and `Expected results` are untouched below it, for a manual test that is not an acceptance check.
- `~/Dev/repos/project-os/tools/instructions/TESTING.md` gains "A check is walkable by a stranger" under "Where the acceptance suite lives": the four headings, the provenance rule, and the rewritten-on-contact rule.
- `~/Dev/repos/project-os/tools/skills/test-authoring/SKILL.md` step 3 now has an acceptance branch that links to that subsection and rests the check at `active`, and a separate branch for every other manual test that keeps `ready`.
- `bash tools/scripts/validate-docs.sh` is OK in the template; the six test scripts pass (26, 23, 74, 15, 31 and 3 assertions, 0 failures).

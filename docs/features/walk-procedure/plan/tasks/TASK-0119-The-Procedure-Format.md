---
type: "[[task]]"
id: TASK-0119
aliases: ["TASK-0119"]
title: "The procedure format: where a sitting's procedure lives, its headings, the expectation-tag spelling, what an owed part is, and the TESTING.md text that states it once"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decisions 3 and 5"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: M
due: ""
depends: []
blocks: ["[[TASK-0120-The-Procedure-Validator]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]"]
related: ["[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect]]"]
tests: []
---

# The procedure format

## What

A person or an LLM writing a procedure for a sitting has one template and one schema entry to follow. The format carries: the sitting it belongs to, a Setup stated once, numbered steps that each name a surface, and expectation lines tagged with the check step they satisfy.

## Definition of Done

- [x] ADR-0045 is accepted and its three open boxes are answered. *(2026-09-14: one file per sitting under `docs/tests/acceptance/walk/`, linked from WALK.md; each file aims to cover every live check in its sitting and the validator requires only the owed ones; each expectation line quotes the check's Expect text word for word.)*
- [ ] A template exists, `docs/__templates__/procedure.md`, for a file at `docs/tests/acceptance/walk/<sitting>.md`, and `walk.md` shows how WALK.md links each sitting's procedure file.
- [ ] `SCHEMAS.md` describes the shape a parser reads: the sitting name it matches in WALK.md, the Setup heading, the step numbering, how a step names a surface (by `SUR-*` id or by title), the tag grammar (ASCII `TST-####.N`, or a bare `TST-####` for a one-part check), and how an expectation line carries its verbatim quote of the check's Expect text.
- [ ] "Owed part" is defined in TESTING.md: one numbered item under a check's `## Steps` (or `## Procedure`), or the whole check when its steps are not numbered. The definition says what happens when a check's steps are renumbered after a procedure cites them, and says that the LLM writing a sitting's procedure numbers a prose-only check's steps in the check note when it gets to it.
- [ ] TESTING.md "The walk" states the procedure rules once. The template and schema link there.
- [ ] A worked example in the template uses one real shape: a data-only trainer sitting with a shared setup and a single drivable-trainer comparison step tagged for three checks.

## Steps

- [ ] Count, on your-trainer's 39 owed Android checks, how many have numbered steps under a heading today. Record it; it decides how many parts are whole checks.

## Notes

- [[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect|ISS-0064]] matters here: a check whose procedure sits in unheaded prose has no numbered steps, so the validator can only count it as one part.
- ADR-0027 stays: the check note is still walkable by a stranger. The procedure is a script over checks, not a replacement for them.

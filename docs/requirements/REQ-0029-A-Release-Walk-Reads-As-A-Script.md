---
type: "[[requirement]]"
id: REQ-0029
aliases: ["REQ-0029"]
title: "A release walk reads as a script: the changed screens with a rider-facing sentence and before and after captures, then one procedure per sitting that a validator holds to the owed set"
status: draft
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0044-A-Surface-Is-A-Screen-By-Default]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "Edwin, 2026-09-14: approved goal wording for the v2.2.0 walk"]
priority: high
scope: "The project-os template: tools/instructions/TAXONOMY.md and TESTING.md, docs/__templates__/surface.md, change.md, walk.md and SCHEMAS.md, tools/scripts/walk-sheet.py and its fixture test, the procedure validator, and the change-note, close-out, release-prep and new procedure skills. The cockpit page and each consumer's surfaces, change notes, captures and procedures are downstream."
acceptance:
  - "TAXONOMY.md says a surface is a screen by default and states four rules once: a state is not a surface; a dialog, sheet or panel is a child with parent:; a check that walks several screens names their parent; a screen placed differently per platform is one surface."
  - "change.md's Impact section lists SUR-* ids, each with one rider-facing sentence, and the change-note and close-out skills ask an LLM to draft it from the diff."
  - "The survey lists every surface named in the Impact section of a change note merged since the last release tag, with its sentences, and shows before and after captures where the gallery maps a capture key to that surface. It prints no test id. Without a reachable release tag it says so."
  - "A procedure for a sitting lives in one file under docs/tests/acceptance/walk/, linked from WALK.md, and states the setup once, then numbered steps that each name a surface, with expectation lines that quote the check's Expect text word for word and carry ASCII tags such as TST-0648.4."
  - "The validator fails on an owed part no step cites, an owed part two steps cite, a tag naming a retired check, a tag naming a step the check does not have, and a quoted expectation that does not match the check's Expect text; it passes when none of these holds. A fixture test proves each failure and the pass."
  - "For a sitting with a procedure the sheet prints the setup and only the steps citing an owed part; a sitting without one prints per-check rows as REQ-0028 describes."
  - "A skill regenerates a sitting's procedure when its owed checks change and keeps the result only if the validator passes."
  - "TESTING.md 'The walk' states these rules once; the templates, skills, generator and validator link to it without restating."
implements: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
verifies: []
related: ["[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]"]
tests: ["[[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]]", "[[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After]]"]
---

# A release walk reads as a script

## Statement

When a release is walked, the walk sheet shall open with the screens the release changed, each with one sentence a rider would understand and before and after captures where they exist, and shall present each sitting that has a written procedure as that procedure: the setup once, then numbered steps naming the screen, with each expectation tagged by the check it satisfies. A validator shall refuse a procedure that leaves an owed part uncited, cites one twice, or cites a retired check or a missing step.

Words used here. A **procedure** is a written script for one sitting. An **owed part** is one numbered step of a check the release still owes; a check with no numbered steps is one part. An **expectation tag** is a label such as `TST-0648.4` on a procedure line.

This requirement is drafted against two decisions, accepted by Edwin on 2026-09-14, [[ADR-0044-A-Surface-Is-A-Screen-By-Default|ADR-0044]] and [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]]. Both are accepted, so the condition for approving it is met; approval is the owner's act and has not been recorded.

It is owned by FEAT-0031 because a requirement has at most one owning feature (ADR-0007). The first three criteria are built by [[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens|FEAT-0030]].

## Acceptance Criteria

- [ ] TAXONOMY.md says a surface is a screen by default and states the four rules once — evidence:
- [ ] change.md's Impact section lists `SUR-*` ids with one rider-facing sentence each, and the change-note and close-out skills ask an LLM to draft it from the diff — evidence:
- [ ] The survey lists the surfaces named by change notes since the last release tag, with sentences and before and after captures, no test ids, and says so when no tag is reachable — evidence:
- [ ] A procedure lives in one file per sitting under `docs/tests/acceptance/walk/`, states the setup once, then numbered steps naming a surface, with expectation lines quoting the check's Expect text and ASCII tags — evidence:
- [ ] The validator fails on each of the five defects (uncited, doubly cited, retired check, missing step, quote mismatch) and passes otherwise, proven by a fixture test — evidence:
- [ ] The sheet prints only the procedure steps citing an owed part, and per-check rows for a sitting without a procedure — evidence:
- [ ] A skill regenerates a procedure when its sitting's owed checks change, and keeps it only if the validator passes — evidence:
- [ ] TESTING.md "The walk" states the rules once — evidence:

## Traceability

- Implements: [[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]
- Verified by: [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]], [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After]]

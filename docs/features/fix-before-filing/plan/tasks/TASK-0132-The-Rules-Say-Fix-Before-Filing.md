---
type: "[[task]]"
id: TASK-0132
aliases: ["TASK-0132"]
title: "The rules say fix before filing"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]", "[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
parent: "[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]"
effort: "Medium"
due: ""
depends: []
blocks: [TASK-0133]
related: ["[[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix]]", "[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]"]
tests: [TST-0006]
---

# The rules say fix before filing

## Definition of Done
- [x] `QUALITY.md` in `~/Dev/repos/project-os`: the "Only a behavioural finding blocks" bullet is replaced by ADR-0047's rule. A finding about code the feature changed is fixed before the feature closes. It is filed only under the filing bar. Blocking decides only whether round two runs.
- [x] `LIFECYCLE.md`, "Scope of a change", says the rule does not apply to code the current feature changed. The file stays under its 1,000-word budget (`test-word-budgets.sh`).
- [x] `independent-review/SKILL.md` step 5 fixes first and files only under the bar. Findings below the bar go in the note's review section.
- [x] The close-out skill says a validator error the session caused is fixed, and filing is for errors that need a decision or lie outside the work. This closes [[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix|ISS-0028]].
- [x] Each rule is stated once, and every other file links to it.
- [x] `generate-adapters.py --check`, `test-word-budgets.sh` and `run-tests.py` pass in the template.

## Notes
- ADR-0047 was accepted by Edwin on 2026-09-18.

## Done, 2026-09-18
Implemented in `3c979ee`. `QUALITY.md` replaces ADR-0028's severity bar with "A finding is fixed in the feature that caused it" and "The filing bar". `LIFECYCLE.md` "Scope of a change" now fixes a defect in code the feature changed, at 990 words against its 1,000-word budget. The review skill's "After the review" section and the close-out skill follow. The close-out skill now says what to do with a validator error you cannot fix, which closes [[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix|ISS-0028]].

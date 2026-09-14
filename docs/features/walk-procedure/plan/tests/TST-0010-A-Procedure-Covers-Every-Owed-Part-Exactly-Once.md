---
type: "[[test]]"
id: TST-0010
aliases: ["TST-0010"]
title: "A procedure covers every owed part exactly once, the validator refuses one that does not, and the sheet prints only the owed steps"
status: active
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[TASK-0120-The-Procedure-Validator]]"]
scope: feature
level: acceptance
entrypoint: ""
command: ""
last_verified: ""
covers: ["[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
issues: []
tasks: ["[[TASK-0120-The-Procedure-Validator]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]"]
artifacts: []
adequacy: ""
mutation_score: ""
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]", "[[TST-0009-The-Sheet-Is-The-Ledgers-Owed-Set-In-The-Authored-Order]]"]
area: "the walk"
after: []
---

# A procedure covers every owed part exactly once

## Setup

The template repo checked out beside this one. The fixture harness TASK-0120 writes, which builds a repo with a ledger, a WALK.md, check notes with numbered steps and one procedure per fixture. When TASK-0120 lands, its path goes in `command:` and this note stops recording a verdict (ADR-0025).

## Steps

1. Run the harness against the fixture whose procedure cites every owed part once.
2. Run it against the fixture where one owed part is cited by no step.
3. Run it against the fixture where one owed part is cited by two steps.
4. Run it against the fixture where a tag names a retired check.
5. Run it against the fixture where a tag names step 9 of a check with 4 steps.
6. Generate the sheet for the first fixture, where two of its checks have already passed.
7. Generate the sheet for a fixture sitting that has no procedure.

## Expect

- Step 1 passes.
- Steps 2 to 5 each fail, and each message names the check id and step number involved.
- Step 6 prints the setup once and leaves out every step whose tags are all for passed checks.
- Step 7 prints the per-check rows the sheet prints today, unchanged.

## Not this check

- Whether the procedure's wording matches the check. The validator checks coverage only (ADR-0045 decision 4).
- The survey. That is [[TST-0011-The-Survey-Lists-Changed-Screens-With-Before-And-After|TST-0011]].

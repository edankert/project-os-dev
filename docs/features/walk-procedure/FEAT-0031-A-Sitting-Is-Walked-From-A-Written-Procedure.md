---
type: "[[feature]]"
id: FEAT-0031
aliases: ["FEAT-0031"]
title: "A sitting is walked from a written procedure: setup once, a screen on every step, each expectation tagged with its check, and a validator that holds it to the owed set"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["Edwin, 2026-09-14, approved goal: 'Then it gives one procedure per sitting (checks sharing one setup): the setup stated once, each step naming the screen it happens on, and each expectation tagged with the check it satisfies.'", "Edwin, 2026-09-14: 'an LLM can always be integrated in these solutions'"]
goal: "A person walks a sitting from one procedure instead of from each check in turn: the setup is stated once, every step names its screen, every expectation line says which check step it satisfies, and a script refuses the procedure if it misses or double-counts anything the release owes."
requirements: ["[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tasks: ["[[TASK-0119-The-Procedure-Format]]", "[[TASK-0120-The-Procedure-Validator]]", "[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]", "[[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure]]", "[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
release: ""
acceptance_exception: ""
related: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0027-An-Acceptance-Check-Is-Walkable-By-A-Stranger]]", "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]", "[[FEAT-0029-The-Walk-Sheet]]", "[[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently]]", "[[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect]]"]
---

# A sitting is walked from a written procedure

## Goal

A person walking a sitting reads one procedure. It states the setup once. Each numbered step names the screen it happens on. Each line saying what should be seen quotes the check's own Expect text word for word and carries an ASCII tag such as `TST-0648.4`, meaning it satisfies step 4 of check TST-0648. The procedure lives in one file per sitting under `docs/tests/acceptance/walk/`, linked from WALK.md, and is written once for the whole product, not per release. The walk sheet prints only the steps that cite something the release still owes. A validator refuses the procedure if an owed step is cited by nothing, cited twice, or cited from a retired check or a step that does not exist, or if a quoted expectation does not match the check.

Today the sheet prints each check separately inside a sitting. On your-trainer's v2.2.0 sheet the fake-trainer setup is printed four times in one sitting and the drivable-trainer comparison four times across checks ([[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure|ADR-0045]], Context).

## Scope

In, all in the template repo:

1. **The format** ([[TASK-0119-The-Procedure-Format|TASK-0119]]): where a procedure lives, its headings, the tag spelling, and the TESTING.md text.
2. **The validator** ([[TASK-0120-The-Procedure-Validator|TASK-0120]]) and its fixture test, which is the command on [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].
3. **The sheet** ([[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure|TASK-0121]]): `walk-sheet.py` prints a procedure's owed steps, and per-check rows where a sitting has no procedure.
4. **The skill** ([[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure|TASK-0122]]): an LLM regenerates a sitting's procedure when its owed checks change, and keeps it only when the validator passes.
5. **Downstream** ([[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit|TASK-0123]]): sync to your-trainer and project-os-cockpit, and REQ-0028's amendment recorded.

Out:

- Automatic merging of steps without a written procedure.
- Any ledger change. A verdict is still one event per check.
- Writing any consumer's procedures. your-trainer's are its TASK-0906.
- The cockpit's per-step ticks (project-os-cockpit FEAT-0150).

## What an owed part is

The validator needs a unit to count. Decided by Edwin on 2026-09-14: an **owed part** is one numbered item under a check's `## Steps` heading (or `## Procedure` where Steps is absent), for a check the ledger says this platform owes. A check whose steps are not numbered is one part, cited by its bare id. This matches the way the review counted repetition ("TST-0648 steps 12 to 15").

It depends on how many owed checks have numbered steps. [[ISS-0064-A-Walk-Row-Falls-Back-For-Steps-And-Not-For-Expect|ISS-0064]] measured that most your-trainer rows keep their procedure in unheaded prose, so many will be one part each. The LLM writing a sitting's procedure numbers those steps in the check note when it gets to them, and the check then has one part per step.

## Acceptance

- The fixture test fails the validator on each of the five defects (the four coverage defects and a quoted expectation that does not match), one fixture each, and passes a procedure that cites every owed part once. [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]].
- On a fixture sitting with a procedure and some checks already passed, the sheet prints the setup once and only the steps that cite an owed part.
- On a fixture sitting with no procedure, the sheet prints exactly what it prints today.
- The procedure skill exists and tells the agent to rerun the validator before keeping a regenerated procedure.

## Risk scan

No new external dependency, environment variable or credential. One new authored file shape per consumer (the procedure) and one new validator entry point. The LLM that drafts a procedure runs inside the agent session, not inside the generator or validator, so neither script gains a network call or a model dependency. No `RISK-*`.

## Links

- Decision: [[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]].
- Requirement: [[REQ-0029-A-Release-Walk-Reads-As-A-Script]].
- Downstream: your-trainer FEAT-0121 (v2.2.0 procedures), project-os-cockpit FEAT-0150 (the page and step ticks).

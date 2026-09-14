---
type: "[[task]]"
id: TASK-0120
aliases: ["TASK-0120"]
title: "The procedure validator fails on an owed part no step cites, an owed part two steps cite, a tag naming a retired check and a tag naming a missing step, with a fixture test for each"
status: backlog
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 4"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: L
due: ""
depends: ["[[TASK-0119-The-Procedure-Format]]"]
blocks: ["[[TASK-0122-A-Skill-Regenerates-A-Sittings-Procedure]]", "[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[ISS-0063-The-Sheet-And-The-Cockpit-Scope-The-Acceptance-Suite-Differently]]", "[[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses]]"]
tests: ["[[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once]]"]
---

# The procedure validator

## What

A script reads a sitting's procedure, the check notes and the ledger, and fails with a message naming the check and step when the procedure and the owed set disagree. It is how an LLM-written procedure is trusted without a person re-reading every check.

## Definition of Done

- [ ] For a release and platform, the validator computes owed parts from the same owed set `walk-sheet.py` uses (one implementation, ADR-0029 rule 7).
- [ ] It fails, naming the check and step, when: an owed part is cited by no step; an owed part is cited by more than one step; a tag names a check at `status: retired`; a tag names a step number the check does not have.
- [ ] It also fails when a tag names a check that belongs to a different sitting, or say in this task why that is allowed.
- [ ] It passes a procedure that cites every owed part exactly once, even when it also cites parts that are not owed.
- [ ] A fixture harness proves each failure with its own fixture and proves the pass. It is the `command:` on [[TST-0010-A-Procedure-Covers-Every-Owed-Part-Exactly-Once|TST-0010]], and each assertion is shown to fail when its rule is removed (record the mutations in TST-0010's `adequacy:`).
- [ ] Where it runs is decided (PLAN.md open question 1): `walk-sheet.py --check`, a `validate-docs.sh` rule, or both. Record why.

## Steps

- [ ] Write the four failing fixtures first.
- [ ] Put the code where the cockpit's byte-identical bundle picks it up (PLAN.md soft dependency).

## Notes

- A procedure goes stale without being edited: a ledger event can make a new part owed. The regenerate skill (TASK-0122) is the answer; the validator is what tells you.
- [[ISS-0065-The-Templates-Own-CI-Runs-None-Of-Its-Seven-Harnesses|ISS-0065]]: the template's CI runs none of its harnesses. This harness would be the eighth. Do not fix that here, but say in the change note that it has the same exposure.

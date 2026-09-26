---
type: "[[task]]"
id: TASK-0170
aliases: ["TASK-0170"]
title: "validate-docs.sh ends with one verdict for every step, and walk problems are marked ERROR [WALK]"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0089-The-Validator-Said-OK-And-The-Commit-Was-Refused]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0089-The-Validator-Said-OK-And-The-Commit-Was-Refused]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0028-The-Last-Line-Of-Validate-Docs-Is-The-Whole-Verdict]]"]
---

# validate-docs.sh ends with one verdict for every step, and walk problems are marked ERROR [WALK]

## Definition of Done
- [x] The last line of `validate-docs.sh` is its verdict for every step it ran; the Python validator's own line no longer reads as the whole verdict when run from the script. It reads `validate-docs [notes]: OK` there, and the script ends with `validate-docs: OK (<root>: notes and walk procedures)` or `validate-docs: FAIL (notes: OK; walk procedures: FAIL)`.
- [x] `walk-sheet.py --check` prints each disagreement as `ERROR [WALK] ...`, and a broken ledger too.
- [x] A test reproduces the your-trainer case (a walk failure after a passing validator) and asserts the last line says FAIL (TST-0028).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0028: four mutations, all caught).

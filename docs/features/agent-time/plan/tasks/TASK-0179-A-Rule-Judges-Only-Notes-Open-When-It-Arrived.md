---
type: "[[task]]"
id: TASK-0179
aliases: ["TASK-0179"]
title: "A content rule judges only notes still open when it arrived, and --changed shows only what changed"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0094-A-Rule-Judges-Notes-That-Closed-Before-It-Existed]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0094-A-Rule-Judges-Notes-That-Closed-Before-It-Existed]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0036-A-Rule-Judges-Notes-Open-When-It-Arrived]]"]
---

# A content rule judges only notes still open when it arrived, and --changed shows only what changed

## Definition of Done
- [x] Each content rule has the date it arrived; a note finished before that date is not judged by it. Structural checks still cover every note. `RULE_ARRIVED` in `validate-docs.py` holds the template dates of REQ-BOXES, FEATURE-REQ, VERIFY-ACCEPTANCE, FEATURE-UNCOVERED and REVIEW-STALE. A repo's own date is the first commit of its `validate-docs.py` containing the rule, whichever is later. A note counts as finished before the rule when its status resolves it and its `updated:` is on or before that date. The hidden findings are counted in one line.
- [x] `validate-docs.py --changed` prints only findings about files changed since HEAD, with a count of the rest. The exit status still counts every error.
- [x] Measured on your-trainer: findings about finished notes before and after (table below).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0036: five mutations, all caught).

## Measured on your-trainer, 2026-09-26

Findings whose first word is a note id, and how many of those notes are finished (their status resolves them for their type).

| Validator | Findings | About finished notes |
|---|---|---|
| Template at the start of PHASE-0009 (`ca29288`) | 1,139 | 327 (29%) |
| With this task and TASK-0169 to TASK-0178 | 977 | 150 (15%) |

The 177 hidden findings are REQ-BOXES 116, FEATURE-REQ 28, FEATURE-UNCOVERED 24 and REVIEW-STALE 9. Of the 150 left, 141 are verification findings (VERIFY-ACCEPTANCE 130, VERIFY-WAIVED 8, VERIFY 3). The 130 are tasks finished in September whose acceptance checks the unreleased 2.2.0 walk still owes, which is live release work. The 654 LEDGER-FIELD findings do not name a note first and are TASK-0183's.

---
type: "[[task]]"
id: TASK-0130
aliases: ["TASK-0130"]
title: "Re-run the FEAT-0107 review the new way"
status: backlog
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Small"
due: ""
depends: [TASK-0126, TASK-0127, TASK-0128]
blocks: [TASK-0131]
related: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]"]
tests: []
---

# Re-run the FEAT-0107 review the new way

## Definition of Done
- [ ] A new-style review has been run against `your-trainer` at `a5425c6e^`. That is the code FEAT-0107's review saw on 2026-09-17, before it returned `changes-requested` in `a5425c6e`. The review ran in a separate git worktree, so `your-trainer`'s working tree was never touched.
- [ ] The reviewer received only the packet and the standard author prompt. It got no hint about what the old review found.
- [ ] The result is recorded in this note against three known answers:
  - [ ] **ISS-0462**: Android never checks a real trainer for a missing Control Point, so one of the three detection sources works only for the mock. This refutes an acceptance criterion.
  - [ ] **ISS-0463**: the compatibility test reads the trainer's capability once, at the start, so a trainer that is later found to be data-only reports FAIL rows instead of N/A. This refutes an acceptance criterion.
  - [ ] **ISS-0466**: deleting all six write guards leaves the 1322 Android tests passing.
- [ ] The measurements are recorded: tool calls, turns, minutes, peak context and total context tokens, taken with the reference note's query.
- [ ] **Pass**: ISS-0462 and ISS-0463 are both found as *refuted* claims within the budget. **Fail**: either is missed. On a fail, record which step lost it, and change TASK-0127 or TASK-0128 before TASK-0131 starts.

## Steps
- [ ] `git -C ~/Dev/repos/your-trainer worktree add <scratch>/yt-feat0107 a5425c6e^`
- [ ] Generate the packet there and run the reviewer with the budget hook active.
- [ ] Compare with the known answers, record the results, and remove the worktree.

## Notes
- The old review took 70 tool calls and found the ISS-0466 defect at calls 34–39. It also returned twelve findings in all, per `a5425c6e`'s message. Losing the smaller ones is intended; losing a blocking one is not.
- One re-run is weak evidence. If time allows, repeat once against a second known review, such as FEAT-0108.

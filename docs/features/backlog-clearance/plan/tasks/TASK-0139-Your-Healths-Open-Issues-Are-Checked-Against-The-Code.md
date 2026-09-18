---
type: "[[task]]"
id: TASK-0139
aliases: ["TASK-0139"]
title: "your-health's open issues are checked against the code"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]", "Edwin, 2026-09-18: 'first check your-health'"]
parent: "[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"
effort: "Large"
due: ""
depends: []
blocks: []
related: ["[[TASK-0138-Your-Trainers-Open-Issues-Are-Checked-Against-The-Code]]"]
tests: []
---

# your-health's open issues are checked against the code

## Definition of Done
- [ ] Each of the 63 open issues is obsolete, fixed, kept, declined or a question, with evidence dated 2026-09-18 or later in its own note. ISS-0164 and ISS-0180 are left out: another session has uncommitted work on them, begun 2026-09-13.
- [ ] Small fixes are either made, each with a test that fails without it, or collected into one work-order issue in your-health, as your-trainer's ISS-0484 was. That is Edwin's choice for your-trainer, and it is expected here.
- [ ] Edwin has received one list of questions, each with a recommendation.
- [ ] The uncommitted work in your-health (21 files, including SNAPSHOT.yaml) stays out of every commit.

## Result, 2026-09-18

Seven read-only reviewers checked nine issues each, as ordinary agents. Their evidence was spot-checked for five issues and matched every time. Committed as your-health `0bdf4af`.

| End state | Count |
|---|---|
| Already done, still marked open | 23 |
| Declined: nobody would notice today | 5 |
| Real, kept, with what a reader notices | 15 |
| Real and small, collected into work order [[your-health#ISS-0181]] | 12 |
| Question for Edwin | 8 |

**37% were stale**, between your-trainer's March batch (80%) and its newer issues (20%). The record trailed the code by about two weeks: several fixes committed on 2026-09-02 still showed as open, backlog or planned.

**Kept with care.** ISS-0170 (high: a meal section set out of order makes a meal reach Health Connect as a near-whole-day record) is kept to be coordinated with TASK-0446, whose uncommitted change to the same code lengthens those spans. ISS-0112 is the template validator's, and is filed here as [[ISS-0070-A-Snapshot-That-Does-Not-Parse-Still-Passes-Validation|ISS-0070]].

**The other session's work stayed out.** your-health had 21 uncommitted files from another session, SNAPSHOT.yaml among them. The committed snapshot was rebuilt in a worktree at HEAD with only this review's notes, and staged from there. Their files are unchanged.

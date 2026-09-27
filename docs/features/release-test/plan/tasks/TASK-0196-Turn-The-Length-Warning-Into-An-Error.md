---
type: "[[task]]"
id: TASK-0196
aliases: ["TASK-0196"]
title: "Turn the length check from a warning into an error once your-trainer's Android and iOS sections pass it"
status: backlog
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "S"
due: ""
depends: ["[[TASK-0195]]"]
blocks: []
related: ["[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]"]
tests: []
---

# Turn the length check from a warning into an error once your-trainer's Android and iOS sections pass it

The length check becomes an error by default, so a release test cannot grow back to 37,000 words unnoticed.

## Definition of Done
- [ ] Every Android and every iOS section in your-trainer passes the length check with no warning.
- [ ] The template's switch defaults to error.
- [ ] Every consumer with a release test passes after the sync, or has a task to shorten its sections.

## Steps
- [ ] Confirm your-trainer's Android and iOS runs are clean.
- [ ] Flip the default and sync.

## Notes
- This waits on your-trainer's rewrite of its other sections, which is outside this repo.

## State, 2026-09-27

The budget stays at 300 plus 40 per check (TASK-0195). After the rewrite, no your-trainer section is over it on either platform. Five lines are still over their word limit, each kept long on purpose. On Android they are TST-0350.1 and TST-0353.1, which quote the app's copy. On iOS they are TST-0350.1, TST-0015.2 and TST-0329.3, which keep every assertion. So the first box needs Edwin to accept these lines, or the switch to exempt a line that quotes app copy, before the default flips to error.

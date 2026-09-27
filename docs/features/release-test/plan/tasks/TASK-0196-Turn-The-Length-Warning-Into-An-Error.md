---
type: "[[task]]"
id: TASK-0196
aliases: ["TASK-0196"]
title: "Turn the length check from a warning into an error once your-trainer's Android and iOS sections pass it"
status: done
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
- [x] Every Android and every iOS section in your-trainer passes the length check with no warning. your-trainer b5cb041f, 2026-09-27: TST-0350 and TST-0353 split their quoted copy into two steps, two lines shortened, two sections trimmed; `--check` prints nothing on either platform.
- [x] The template's switch defaults to error. project-os aa5fd7e (`LengthLimits.error = True`); project-os 116d14e also refuses a quoted procedure line by default (REQ-0034).
- [x] Every consumer with a release test passes after the sync, or has a task to shorten its sections. your-trainer passes (bbd72118). project-os-cockpit's own macOS release test does not: three owed checks are still prose, so it sets `length_limits: {error: false}` until its ISS-0315 is fixed at its next release preparation (34effb9).

## Steps
- [x] Confirm your-trainer's Android and iOS runs are clean. Clean on both platforms after the sync.
- [x] Flip the default and sync. Synced to project-os-dev (b5a29ab), your-trainer (bbd72118) and project-os-cockpit (34effb9, with the bundle re-copied).

## Notes
- This waits on your-trainer's rewrite of its other sections, which is outside this repo.

## State, 2026-09-27

The budget stays at 300 plus 40 per check (TASK-0195). After the rewrite, no your-trainer section is over it on either platform. Five lines are still over their word limit, each kept long on purpose. On Android they are TST-0350.1 and TST-0353.1, which quote the app's copy. On iOS they are TST-0350.1, TST-0015.2 and TST-0329.3, which keep every assertion. So the first box needs Edwin to accept these lines, or the switch to exempt a line that quotes app copy, before the default flips to error.

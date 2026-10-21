---
type: "[[issue]]"
id: ISS-0108
aliases: ["ISS-0108"]
title: "The release gate blocks on every hand-run check, so a person's testing grows with every feature and every platform; your-trainer capped it at ten per platform"
status: open
phase: ""
owner: user:edwin
created: 2026-10-20
updated: 2026-10-21
source: ["your-trainer ADR-0020, accepted by Edwin on 2026-10-20: 'I have read it and agree, please continue ...'", "your-trainer REVIEW-2026-10-ManualValidationAtScale"]
reported_by: agent
question: "Should the template's \"Release gating\" adopt your-trainer's budget, ten hand-run checks per platform and only for taste, real hardware or a real account, and should release-test.py print the budget line and refuse to seal over it?"
severity: high
component: "instructions"
parent: ""
related: []
tests: []
tasks: ["[[TASK-0205]]", "[[TASK-0207]]"]
---

# The release gate blocks on every hand-run check

## Problem

`TESTING.md`, "Release gating", blocks a release while any hand-run acceptance check has no result. Every check therefore costs a person time before anything ships, whatever it finds. The list grows with every feature, and it grows again with a second platform.

your-trainer measured what that costs:

- 345 of its 449 active acceptance checks are run only by hand. The next Android release owes 98 of them, and the first iOS release owes all 345.
- In v2.1.8, Edwin recorded 107 results by hand over four days, and one of them found a real regression.
- Riders and beta testers found 63 of its 183 trainer bugs, on trainers Edwin does not own. Acceptance testing found about 15.
- The same setup is being copied into your-sudoku, project-os-cockpit and project-os-deck.

## What your-trainer decided

your-trainer ADR-0020 was accepted on 2026-10-20. A release owes at most ten hand-run checks per platform. Each of them needs a person for one of three things: taste, a real trainer or sensor on a real radio, or a real third-party account. Every other check leaves the hand-run list in one of three ways:

- it gets a `command:`;
- it retires;
- or the release note names it as covered by a staged rollout.

Tasks close on evidence an agent produced. Taste questions go on a weekly page, and an item nobody objects to within seven days counts as accepted. That page never blocks a release.

## Expected

1. **`TESTING.md`, "Release gating"**, states the budget and the three kinds of check that may stay hand-run. The release gate blocks on those checks and on CI, and on nothing else.
2. **`tools/scripts/release-test.py`** prints a budget line on each platform's sheet: owed hand-run checks against the limit. It refuses to seal a ledger over the limit unless the release note says why. The cockpit's `ledger.owed()` counts the same way.
3. **The budget is a project setting**, ten by default, so a repo with no hardware can set a lower number.

## One thing the change should also say

A `command:` takes a check off every platform's list at once. your-trainer found nine checks whose test exists on Android only. If one of those got an Android-only `command:`, iOS would stop owing it, and nothing would test it there. The rule should either say that a cross-platform check's command runs every platform's test, or allow a `command:` per platform.

## What is done, and what is left

[[TASK-0205-A-Command-Covers-One-Platform-Hand-Steps-Stay-Owed-And-The-Sheet-Prints-The-Budget|TASK-0205]] built the template side in project-os a76657d. A check's `commands:` covers one platform, so a test written for Android no longer clears iOS, and `hand_steps:` keeps only the steps a person must run. Each sheet prints the hand-run budget against `hand_run_limit:`, ten by default. `TESTING.md`, "Release gating", states the three rules.

Still open: `release-test.py` and the seal do not yet refuse a ledger over the limit, and project-os-cockpit's `ledger.owed()` still counts by `command:` alone, so the cockpit's count and the sheet's differ once a repo uses `commands:` or `hand_steps:`.

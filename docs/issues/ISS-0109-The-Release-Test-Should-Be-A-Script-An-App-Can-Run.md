---
type: "[[issue]]"
id: ISS-0109
aliases: ["ISS-0109"]
title: "The release test is a sheet a person follows step by step; it should also be a script an app can run, so a person tests a release in one guided session"
status: open
phase: ""
owner: user:edwin
created: 2026-10-20
updated: 2026-10-20
source: ["Edwin, 2026-10-20, in your-trainer: 'I have no problem going on the bike and testing ... the problem is setting up all the different setups and going through each of these steps separately.'", "Edwin, 2026-10-20: 'I think we could implement something like that for each of the applications, not just the trainer?'", "your-trainer FEAT-0140"]
reported_by: agent
question: "Should release-test.py write a ride script, the owed steps in running order with a machine-readable scenario for each, and should a tool import an app's results file into the ledger?"
severity: medium
component: "scripts"
parent: ""
related: ["[[ISS-0108-The-Release-Gate-Blocks-On-Every-Hand-Run-Check]]"]
tests: []
---

# The release test should also be a script an app can run

## Problem

The release test is a sheet a person reads and follows. Each section starts with setup the person does by hand, such as switching a tier, turning on a mock device or loading a state. Then come numbered steps, and the person marks each one in the cockpit. In your-trainer, Edwin says the setting up and the separate steps are what cost him, not the testing itself.

The procedures already hold most of what an app would need to run them itself:

- numbered steps, each with an action of 20 words or fewer;
- which step needs which (`requires:`);
- timers (`timer_for:`) and values to keep for later (`capture_for:`, `use_capture:`);
- setups, named per platform (`setup_for:`, `setup_platforms:`).

What is missing is a form an app can load, and a way back into the ledger.

## Expected

1. **`release-test.py` writes a ride script** as JSON, next to the sheet. It holds the owed steps and the changed screens, in running order, grouped so the setup changes as rarely as possible. It can be cut to a time target by priority. Each step carries its action, its Expect lines, and its setup names.
2. **A setup name can carry a machine action** that the app maps to its own debug or test controls, such as `tier: FREE`. A setup with no action stays a prompt for the person.
3. **A tool imports an app's results file into the ledger.** Each result gives the check, the step, pass, fail or skip, an optional note, and the evidence files. The cockpit shows the imported results as it shows hand-entered ones.
4. **Each app writes only its runner:** the card that shows one step at a time, and its table of setup actions. your-trainer builds the first one (FEAT-0140), and your-sudoku, the cockpit and Deck can follow.

## Notes

- ISS-0108 cuts how many checks a person owes. This issue makes the ones left cheap to run, and the two work together.
- your-trainer proposes running its runner in the release build, hidden, without changing the purchase tier. The shared format should not assume a debug build.

---
type: "[[reference]]"
title: "Procedure — <the section's name>"
status: active
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
# The `### ` heading in docs/tests/acceptance/RELEASE-TEST.md that this procedure
# tests, word for word. It is the only link between the two files.
section: ""
# Optional when the sheet must retain preparation or filter setup. Positions
# refer to numbered items under Steps, counted across groups, regardless of the
# digits written there.
# requires:
#   4: [3]
# setup_for:
#   trainer: all
#   kickr: [3, 4]
# step_platforms:
#   2: [android]
# action_for:
#   2: {android: "Open the Hub full-width, in split-screen and on the phone.", ios: "Open the Hub sheet on the iPad and the iPhone."}
# setup_platforms:
#   kickr: [android]
# capture_for:
#   3: "Record the watts shown."
# use_capture:
#   4: [3] # Also add 3 to requires for step 4.
# timer_for:
#   4: 60 # Optional timer in seconds; it never records a result.
# readiness_for:
#   4: {kind: preparation, reason: "Bring the power meter to the bench.", issue: "ISS-0123", result: blocked}
related: []
tags: [release-test, procedure]
---

# Procedure — <the section's name>

Copy this file to `docs/tests/acceptance/release-test/<name>.md` and write the script for one section. What a procedure is, what a step is, what a tag is and what the validator refuses are stated once in `tools/instructions/TESTING.md`, "The release test", rule 9. This file shows the shape; it restates none of the rules.

Regenerate it with `tools/skills/release-test-procedure/SKILL.md` when the validator reports that it no longer covers what the release owes.

## Setup

<The state this whole section needs, stated once, and the cheapest way to reach it. If only some retained steps need an item, use named bullets such as `- [trainer] Connect the trainer.` and `setup_for:` above.>

## Steps

<One `### ` heading for each group of steps that start from the same state, with a `Start:` line under it saying what the app and the bench must look like first. Then one numbered item per action: one short line saying what to do. It does not need to name the screen. Under it, one line per check step it tests, holding the tags alone. The page prints the check's own Expect line in its place.>

### Hub layout

Start: the trainer in Smart Trainer, nothing else bound. The Hub is open from the equipment icons.

1. Read the Cadence slot.
   - `TST-0657.1`
2. Open the Hub full-width, in split-screen and on the phone.
   - `TST-0657.2`

### Power from a separate source

Start: the trainer in Smart Trainer, the KICKR in Power Source.

3. Start a ride and read the watts.
   - `TST-0652.1`
4. End the ride, choose the trainer as Power Source, and start another.
   - `TST-0652.8`
   - `TST-0655.2`

<Step 4 is the point of writing a procedure: one action two checks expect something from, tested once and recorded for both.>

## Not covered here

<The checks in this section this procedure does not yet cover, and why. Covering every live check is the aim; covering the owed ones is what the validator requires.>

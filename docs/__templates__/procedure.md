---
type: "[[reference]]"
title: "Procedure — <the sitting's name>"
status: active
owner: unassigned
created: 2026-01-26
updated: 2026-01-26
# The `### ` heading in docs/tests/acceptance/WALK.md that this procedure walks,
# word for word. It is the only link between the two files.
sitting: ""
# Optional when the sheet must retain preparation or filter setup. Positions
# refer to numbered items under Steps, regardless of the digits written there.
# requires:
#   3: [1, 2]
# setup_for:
#   trainer: [1, 2, 3]
# step_platforms:
#   2: [android]
# action_for:
#   2: {android: "Open Profile — Connected.", ios: "Open Settings — Integrations."}
# setup_platforms:
#   trainer: [android]
# state_for:
#   3: "The same ride is running with the trainer connected."
# capture_for:
#   2: "Record the cadence shown before switching sources."
# use_capture:
#   5: [2] # Also add 2 to requires for step 5.
# timer_for:
#   5: 120 # Optional timer in seconds; it never records a verdict.
# readiness_for:
#   5: {kind: preparation, reason: "Bring the power meter to the bench.", issue: "ISS-0123"}
related: []
tags: [walk, procedure]
---

# Procedure — <the sitting's name>

Copy this file to `docs/tests/acceptance/walk/<name>.md` and write the script for one sitting. What a procedure is, what a step is, what a tag is and what the validator refuses are stated once in `tools/instructions/TESTING.md`, "The walk", rule 9. This file shows the shape; it restates none of the rules.

Regenerate it with `tools/skills/walk-procedure/SKILL.md` when the validator reports that it no longer covers what the release owes.

## Setup

<The state this whole sitting needs, stated once, and the cheapest way to reach it. If only some retained steps need an item, use named bullets such as `- [trainer] Connect the trainer.` and `setup_for:` above.>

## Steps

<One numbered item per action. The first line names the screen, by SUR-#### id or by the surface's exact title. Under it, one line per thing to observe: the check's own Expect wording, word for word, then the tags.>

1. **Equipment panel (SUR-0003).** Open Settings > Equipment with the data-only trainer awake.
   - The panel lists the trainer with no power icon. `TST-0648.1`
   - A second slot reads "Add a sensor". `TST-0649.1`
2. **Ride cockpit (SUR-0004).** Start a Power workout on the data-only trainer.
   - The target power is shown and the trainer is not driven. `TST-0648.4`
   - The cadence field stays empty. `TST-0653.2`
3. **Ride cockpit (SUR-0004).** Swap to the drivable trainer and start the same workout.
   - The trainer holds the target power within 5 W. `TST-0648.12` `TST-0649.13` `TST-0656.7`

<Step 3 is the point of writing a procedure: one action three checks each expect the same thing from, walked once and ticked three times. It is only legal because all three notes word that expectation identically — the validator compares each quote against each check it tags.>

## Not covered here

<The checks in this sitting this procedure does not yet cover, and why. Covering every live check is the aim; covering the owed ones is what the validator requires.>

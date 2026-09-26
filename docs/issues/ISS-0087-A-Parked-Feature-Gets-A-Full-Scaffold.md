---
type: "[[issue]]"
id: ISS-0087
aliases: ["ISS-0087"]
title: "A feature nobody will build yet still gets requirements, tasks and an acceptance check, and every later decision has to be applied across all of them"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: "2026-09-26"
source: ["your-trainer session your-trainer-b8, on Edwin's instruction (2026-09-26: 'review where most of the time went', then 'Make it so')"]
reported_by: review
question: ""
severity: medium
component: "tools/skills/feature-scaffold/SKILL.md"
parent: ""
related: ["[[ISS-0027-Terminal-Items-Are-Stranded-In-The-Parking-Lot-Phase]]"]
tasks: ["[[TASK-0174]]"]
tests: ["[[TST-0032-A-Parked-Feature-Needs-Its-Note-Only]]"]
---

# A feature nobody will build yet still gets requirements, tasks and an acceptance check, and every later decision has to be applied across all of them

## Problem

`tools/skills/feature-scaffold/SKILL.md` asks for a first task breakdown and "one acceptance check, by rule" (step 9) whatever the feature's status. So a feature filed for later gets the full set of notes, and each later decision about it must then be applied across all of them.

## Evidence

- your-trainer FEAT-0128, a feature Edwin decided not to build yet (now in a planned future phase), got a feature, a plan, three requirements, eight tasks, a risk and a phase. It took two planner runs: 34 minutes and 73 tool calls, then 21 minutes and 111 tool calls.
- Later decisions had to be applied across up to eleven notes: moving the phase, and turning a read-only recommendation into an option.
- The planner broke the acceptance-check rule on purpose. A check at `active` has no "not walkable yet" state, so it would have joined the release's owed set.

## Proposal (from the report)

A feature filed at `backlog`, or into a planned or future phase, gets the feature note only, with its findings and open questions. Requirements, tasks and the acceptance check are written when its phase starts.

## Fixed, 2026-09-26

TASK-0174, as the report proposed. `feature-scaffold/SKILL.md` gives a feature filed at `backlog` or into a planned phase its feature note only, with Findings and Open questions. Requirements, plan, tasks and the acceptance check are written when its phase starts. A planner run on a scratch copy followed it: one note, 10 tool calls, 78 seconds. TST-0032 tests the validator's side.

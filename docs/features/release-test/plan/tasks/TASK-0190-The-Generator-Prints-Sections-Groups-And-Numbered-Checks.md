---
type: "[[task]]"
id: TASK-0190
aliases: ["TASK-0190"]
title: "The generator prints each section as what changed, setup in three parts, and numbered checks in groups, in both the sheet and the cockpit's JSON"
status: backlog
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0188]]", "[[TASK-0189]]"]
blocks: []
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]"]
tests: []
---

# The generator prints each section as what changed, setup in three parts, and numbered checks in groups, in both the sheet and the cockpit's JSON

This is the new output. For each platform the generator lists the sections with their counts and bench lines. For each section it prints what changed, the setup split three ways, and the checks in groups, numbered from 1.

## Definition of Done
- [ ] Per platform: the sections in order, each with its owed check count and one on-the-bench line built from the order file's `bench:` list.
- [ ] Per section: what changed, then setup, then checks.
- [ ] Setup is split into "On the bench", "Before you start" (numbered) and "Later" (a setup item needed by one printed check, naming that check's number).
- [ ] Each check prints as its section number, one action line, this platform's Expect line and its tag. No expected line starts with "Step N:".
- [ ] A group's start state prints once, and again before the next printed check when checks in between were skipped.
- [ ] A readiness problem prints as one line: the reason, the issue if any, and "Suggested: <result>".
- [ ] A section with no procedure prints one row per owed check, its title as the action line.
- [ ] The Markdown sheet and the JSON payload carry the same sections, groups, numbers and lines, proven by one test that compares them.
- [ ] The JSON payload's shape is documented in TESTING.md or SCHEMAS.md for the cockpit to read.
- [ ] ISS-0086 is set to `fixed`: the only step numbers a tester sees are the printed ones, and generated text refers to them.

## Steps
- [ ] Build the new section model in the generator.
- [ ] Render it to Markdown and to JSON from the same model.
- [ ] Update TESTING.md, "The release test", rules 5 and 9.
- [ ] Regenerate Your Trainer's Equipment section on Android from a copy and compare it with the approved example.

## Notes
- The cockpit draws the page from the JSON: project-os-cockpit FEAT-0155, the release test page in the Tests pane. Agree the payload shape with that item before this task is done.
- The approved example is the Equipment Hub section, Android, v2.2.0. It was a static HTML page Edwin approved on 2026-09-27.

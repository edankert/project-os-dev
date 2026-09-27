---
type: "[[task]]"
id: TASK-0192
aliases: ["TASK-0192"]
title: "The validator reports action lines, expected lines and sections over their word limits, as a warning with a switch to make it an error"
status: backlog
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "M"
due: ""
depends: ["[[TASK-0190]]"]
blocks: []
related: ["[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]"]
tests: []
---

# The validator reports action lines, expected lines and sections over their word limits, as a warning with a switch to make it an error

The length check counts the words a tester sees on the page and reports what is too long.

## Definition of Done
- [ ] `--check` reports each action line over 20 words and each expected line over 25 words, naming the section, the check number and the tag.
- [ ] `--check` reports a section whose printed words exceed its budget.
- [ ] The two limits and the budget are set in one place, and a consumer can override them in its section order file.
- [ ] One switch turns these reports from warnings into errors. It defaults to warning.
- [ ] Tests cover each limit and the switch, and each fails when its guard is removed.

## Steps
- [ ] Count words on the rendered model from TASK-0190, not on the source files.
- [ ] Add the reports and the switch.
- [ ] Document the limits once in TESTING.md.

## Notes
- The section budget's form waits on Edwin (REQ-0036). Until then, set it from the Equipment pilot's measured page.

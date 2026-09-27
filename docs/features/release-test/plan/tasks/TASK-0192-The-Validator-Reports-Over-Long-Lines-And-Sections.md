---
type: "[[task]]"
id: TASK-0192
aliases: ["TASK-0192"]
title: "The validator reports action lines, expected lines and sections over their word limits, as a warning with a switch to make it an error"
status: done
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
tests: ["[[TST-0046-The-Length-Check-Reports-What-Is-Too-Long]]"]
---

# The validator reports action lines, expected lines and sections over their word limits, as a warning with a switch to make it an error

The length check counts the words a tester sees on the page and reports what is too long.

## Definition of Done
- [x] `--check` reports each action line over 20 words and each expected line over 25 words, naming the section, the check number and the tag. project-os 9044d67: `length_findings` on the page model, for example `section 1, "The bench", check 2 (`TST-0401.2` `TST-0402.2`): the action is 22 words, over the limit of 20: "Start the workout ..."`. An expected line names its own tags. TST-0046; mutations: action limit ignored, 3 failures; expected limit ignored, 2.
- [x] `--check` reports a section whose printed words exceed its budget. The budget is `section_base` plus `section_per_check` for each printed check; the words are counted on the rendered section by `printed_words`, without tags, link targets, pictures or markup. Mutations: budget ignored, 1; budget per test note instead of per printed check, 1 unit; tags counted, 1 unit; pictures counted, 1 unit.
- [x] The two limits and the budget are set in one place, and a consumer can override them in its section order file. `LengthLimits` holds the defaults; `length_limits:` in RELEASE-TEST.md's frontmatter overrides any of them, and an unknown key or a limit below 1 fails `--check`. Mutations: override ignored, 3; unknown key accepted, 1; zero accepted, 1.
- [x] One switch turns these reports from warnings into errors. It defaults to warning. `length_limits: {error: true}`, or the default `LengthLimits.error`, which TASK-0196 flips. Mutation: switch ignored, 2.
- [x] Tests cover each limit and the switch, and each fails when its guard is removed. TST-0046: 14 shell assertions and 3 unit tests; ten mutations, each failing.

## Steps
- [x] Count words on the rendered model from TASK-0190, not on the source files.
- [x] Add the reports and the switch.
- [x] Document the limits once in TESTING.md (rule 10, "The length check"; SCHEMAS.md lists `length_limits`).

## Notes
- The section budget's form waits on Edwin (REQ-0036): the pilot sets it. The default is 300 words plus 40 per printed check, which allows the approved example (about 1,000 words for 28 checks) about 1,420. your-trainer TASK-0975 measures its rewritten Equipment section and the default is set from that.
- **Printed checks, not test notes.** The Equipment section has 4 test notes and 28 printed checks; the approved example counts 28. The page's table and header now count printed checks too, with the test notes beside them.
- On a scratch copy of your-trainer before any rewrite: 827 reports over both platforms, and every Android section is over its budget (the Equipment section prints 2,750 words against 1,420). `--check --quiet` prints them as one counted line and still exits 0.

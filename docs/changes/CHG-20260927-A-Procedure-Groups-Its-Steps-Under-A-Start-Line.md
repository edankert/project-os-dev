---
type: "[[change]]"
id: CHG-20260927-A-Procedure-Groups-Its-Steps-Under-A-Start-Line
title: "A release test procedure groups its steps under headings with a Start: line, a step need not name its screen, and readiness_for can name the result to offer"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0189-A-Procedure-Groups-Its-Checks-Under-A-Start-State]]"]
commit: "project-os 73b8d07, 43a293c"
pr: ""
impacts: ["tools/scripts/release-test.py", "tools/scripts/test-release-test.sh", "docs/__templates__/procedure.md", "docs/__templates__/SCHEMAS.md", "docs/__templates__/test.md", "tools/instructions/TESTING.md"]
issues: []
features: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]", "[[TST-0043-A-Procedure-Groups-Its-Steps-Under-A-Start-Line]]"]
---

# A release test procedure groups its steps under headings with a Start: line

## Summary

Someone writing a section's procedure can now put a `### ` heading over each run of steps that start from the same state, and write that state once on a `Start:` line under it. A step no longer has to name its screen: one short action line is enough. `readiness_for:` can name the result the tester is offered, such as `blocked`. A tester sees no new layout yet: the page prints the start as each step's required state, as `state_for:` did.

## Impact

- No screen changed: project-os has no surface notes. The release test page each consumer generates is unchanged until its procedures use groups; then each group's start prints as the state its steps need.

What changed for someone writing or running these files:

- **New procedure form.** Under `## Steps`, a `### ` heading starts a group, and a first line `Start: ...` under it is the group's start state. Steps keep counting across groups. The rule is TESTING.md, "The release test", rule 9, "Groups and their start"; `docs/__templates__/procedure.md` shows two groups.
- **`state_for:` is the older form.** It is still read and printed. `--check` warns about each procedure that has it (one counted line under `--quiet`), and refuses a step that gets a start state from both a `Start:` line and `state_for`.
- **A step need not name its screen.** The remark "step N names no screen" is gone. `action_for` replaces the whole action line when the line has no screen name in bold; before, it refused such a step.
- **`result:` on `readiness_for`.** On a procedure step or on a check, `result:` takes one of the seven stored result values, and `--check` refuses any other. The page prints a declared one as "Suggested result: blocked."
- **Code names**, for project-os-cockpit's bundle: `Group` (title, start, steps), `Procedure.groups`, `Step.group`, `parse_groups` (`parse_steps` still returns the steps alone); readiness dictionaries gain a `result` key.

On a scratch copy of your-trainer the Android and iOS pages are byte for byte what they were. `--check` there warns about 14 procedures that still use `state_for:`.

## Documentation Coverage (All Types Considered)

- features: not-applicable (FEAT-0040 continues)
- requirements: not-applicable (REQ-0033 is advanced at the feature's close-out)
- tasks: updated (TASK-0189)
- issues: not-applicable
- tests: new (TST-0043)
- workflows: not-applicable
- decisions: not-applicable (ADR-0050's amendment of ADR-0045 and ADR-0046 already records it)
- risks: not-applicable (no new dependency, path or setting)
- changes: new
- snapshot: updated

## Follow-ups

- [ ] TASK-0190 prints each group's heading and its start once, and again after skipped checks, and offers `question` for a decision without `result:`.
- [ ] TASK-0194 teaches the procedure skill to write groups and `Start:` lines instead of `state_for:`.

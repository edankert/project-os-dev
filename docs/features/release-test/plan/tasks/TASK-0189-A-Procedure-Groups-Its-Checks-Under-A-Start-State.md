---
type: "[[task]]"
id: TASK-0189
aliases: ["TASK-0189"]
title: "A procedure groups its checks under headings with a start state, and each step is one action line with tags"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "L"
due: ""
depends: ["[[TASK-0187]]"]
blocks: []
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
tests: ["[[TST-0043-A-Procedure-Groups-Its-Steps-Under-A-Start-Line]]"]
---

# A procedure groups its checks under headings with a start state, and each step is one action line with tags

The procedure file changes shape so the generator can print groups. A `### ` heading under `## Steps` starts a group, a `Start:` line under it gives the start state, and each numbered item is one action line followed by tag-only lines.

## Definition of Done
- [x] The generator reads groups, their headings and their `Start:` lines from a procedure. project-os 73b8d07: `parse_groups` returns `Procedure.groups` (title, start, step positions) and each `Step.group`; steps keep counting across groups. The start takes effect at the first of the group's steps that runs on the platform being tested, and prints as that step's required state. TST-0043: not reading headings fails 4 assertions, not reading `Start:` 4, not carrying it 2, applying it only to the group's first step 1.
- [x] `state_for:` is read as before for procedures that have not moved to groups, and the validator warns that it is replaced by `Start:`. `release-test.py --check` prints `WARN [RELEASE-TEST] ... state_for: is replaced by a Start: line`, one counted line under `--quiet`, and the page still prints the `state_for` state. A `Start:` line and a `state_for` entry on the same step are refused as two instructions for one thing. Mutations: warning off, 2 failures; conflict not refused, 1.
- [x] A step's action no longer needs a screen name. The rule that the first line names a surface is removed from the validator and from TESTING.md. The "names no screen" remark is gone from `audit_procedure`, and TESTING.md rule 9, "What a step is", and SCHEMAS.md say the first line is the action. `action_for` now replaces the whole action line when there is no bold screen name to keep, since that rule required one. Mutations: remark put back, 1 failure; `action_for` needing a bold name, 2.
- [x] `readiness_for:` accepts an optional `result:` with one of the seven stored result values, and the validator refuses any other value. On a procedure step and on a check; the values come from the validator's `LEDGER_MARKS`, so there is one list. `--check` refuses `result: maybe` and `result: skipped`, naming the entry and the seven values. The page prints a declared result as "Suggested result: question." Mutations: procedure value not checked, 1 failure; check value not checked, 1; not printed, 2.
- [x] `docs/__templates__/procedure.md` shows a procedure with two groups, a `Start:` line, short actions and tag-only lines. project-os 43a293c: "Hub layout" and "Power from a separate source", from the approved Equipment Hub example; the frontmatter example drops `state_for` and shows `result:`. The template parses into those two groups with the module.
- [x] Tests cover groups, `Start:` lines, the `result:` value and the old `state_for:` warning, and each fails when its guard is removed. 14 new assertions (204 to 218) plus the rewritten screen-name pair; eleven mutations each fail the harness, listed in TST-0043's adequacy.

## Steps
- [x] Extend the procedure parser (`parse_groups`; `parse_steps` still returns the steps alone).
- [x] Update the validator's rules for steps.
- [x] Rewrite the procedure template with the Equipment Hub example's shape.
- [x] Update TESTING.md, "The release test", rule 9: "What a step is", a new "Groups and their start", "Platform and state", "Platform action wording" and "Known readiness problems"; rule 5 and the word list gain group, start state and `result:`.

## Notes
- `requires:`, `setup_for:`, `step_platforms:`, `action_for:`, `capture_for:`, `use_capture:` and `timer_for:` stay as they are (ADR-0050, amendments). `action_for:` changed in one way only: it no longer needs a bold screen name, because the rule that asked for one is gone.
- **What prints is still today's layout.** The page prints each group's start as the "Required state" of its steps, the same line `state_for:` produced. Printing a group heading, the start once per group, and again after skipped checks, is TASK-0190's new output shape. `Procedure.groups` and `Step.group` are there for it.
- **The suggested result prints only when declared.** REQ-0033 says a `kind: decision` without `result:` offers `question`. That default is part of how TASK-0190 lays out a readiness line, so it is not printed here.
- **A group without a `Start:` line is allowed.** The approved example has two ("Connecting devices", "Scanners and Forget"); the state carries on from the group before.
- your-trainer on a scratch copy (Android and iOS, REL-0017): the two sheets are byte for byte the same as before this task. `--check` adds 14 warnings, one per procedure still using `state_for:`. No step there drew the old "names no screen" remark.
- Commits in project-os: 73b8d07 (code and tests), 43a293c (template and instructions).

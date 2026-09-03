---
type: "[[test]]"
id: TST-0007
aliases: ["TST-0007"]
title: "The hooks emit what their contracts now say they emit"
status: draft
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]", "[[TASK-0102]]"]
scope: feature
level: acceptance
entrypoint: ""
command: "bash ../project-os/tools/scripts/test-hooks.sh"
last_run: ""
requirements: []
features: ["[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"]
issues: ["[[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]"]
tasks: ["[[TASK-0102]]", "[[TASK-0103]]"]
artifacts: []
adequacy: ""
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
---

# The hooks emit what their contracts now say they emit

## Purpose

**Draft until [[TASK-0102]] writes the harness this note names.** It is not run before then, so it is never recorded as failing.

Three hooks change behaviour in [[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]] and [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]. All three are shell scripts that read a snapshot and print a message, so all three are directly testable against fixture repos — which is better than the walk an acceptance check would otherwise be.

## Procedure

`tools/scripts/test-hooks.sh` in `~/Dev/repos/project-os`, written by [[TASK-0102]]. Fixture snapshots under a tempdir, never this repo. Cross-repo command for the same reason [[TST-0004]]'s is.

Assertions:

1. **Stop hook, work complete:** focus set, the block reason names setting the status and clearing focus.
2. **Stop hook, mid-flight:** the reason names writing the handoff and stopping, and the loop guard lets the second stop through.
3. **Hint, empty focus:** states the state; does not instruct delegation to the planner.
4. **Hint, multi-item or ambiguous state:** recommends the planner.
5. **Hint, review state:** emits the review sentence. **Any other state:** does not.
6. **Hint size:** the emitted text is under the line bound [[TASK-0103]] sets, so the hint cannot grow into the SessionStart slice.
7. **Document-first gate, the four paths in [[ISS-0003-Document-First-Hook-Fragile-Focus-Parsing]]:** a scratchpad path with no repo above it is allowed, a non-project-os repo path is allowed, a relative path inside the project is denied, an absolute path inside the project is denied.

## Expected results

- Exit 0 once [[TASK-0102]], [[TASK-0103]] and the ISS-0003 fix have landed.
- Exit 1 before then, naming the assertion. That is the correct result today.

## Adequacy (who verifies this test?)

Assertion 5 is the one that can pass vacuously: a hint that emits the review sentence never would satisfy "not in other states" while failing the feature. The inversion to record is deleting the review sentence entirely and confirming assertion 5's first half fails. Fill this section in when the harness is written.

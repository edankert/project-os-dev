---
type: "[[test]]"
id: TST-0006
aliases: ["TST-0006"]
title: "The always-loaded instruction files are under their word budgets"
status: draft
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]", "[[TASK-0098]]"]
scope: feature
level: acceptance
entrypoint: ""
command: "bash -c 'd=../project-os; [ $(wc -w < $d/tools/instructions/LIFECYCLE.md) -lt 800 ] && [ $(wc -w < $d/.cursor/rules/lifecycle.mdc) -lt 830 ]'"
last_run: ""
requirements: ["[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]"]
features: ["[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"]
issues: []
tasks: ["[[TASK-0098]]"]
artifacts: []
adequacy: ""
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
---

# The always-loaded instruction files are under their word budgets

## Purpose

[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]] states one number that a command can settle: LIFECYCLE.md under 800 words. This note executes it, and executes the second assertion that keeps the first honest — the generated Cursor copy must have been regenerated, or the source shrank while every Cursor session still loads the old 1,374 words.

**Draft until [[TASK-0098]] lands the trim.** The command would fail today at 1,343 words, and it is not run before then, so it is never recorded as failing.

The requirement's other two criteria are about shape, not size, and are discharged by the review of the diff. This test does not claim to cover them.

## Procedure

Run from this repo's root. The command is cross-repo for the same reason [[TST-0004]]'s is: the files under test live in the template.

```bash
d=../project-os
wc -w < $d/tools/instructions/LIFECYCLE.md      # target: < 800 (1,343 on 2026-09-03)
wc -w < $d/.cursor/rules/lifecycle.mdc          # target: < 830 (1,374 on 2026-09-03)
```

## Expected results

- Exit 0 once [[TASK-0098]] has landed.
- Exit 1 before then. That is the correct result today, and the gap between 1,343 and 800 is the work.

## Adequacy (who verifies this test?)

The second assertion is the one worth checking: revert `.cursor/rules/lifecycle.mdc` to its pre-trim content with the trimmed source in place, and the command must fail. Without it the test passes on a trim that never reached the file Cursor actually loads. Record the inversion here when the test first runs green.

## What this test deliberately does not check

Whether the shorter file still says everything it needs to. A word count cannot see a deleted rule, which is why the feature's acceptance carries a moved-text table and the close-out carries an independent review pass.

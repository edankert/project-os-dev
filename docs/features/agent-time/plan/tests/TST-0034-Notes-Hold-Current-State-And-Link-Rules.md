---
type: "[[test]]"
id: TST-0034
aliases: ["TST-0034"]
title: "WRITING.md tells a note to hold its current state and to link a rule by name, and the task and feature templates point at it"
status: active
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[TASK-0176]]", "[[TASK-0177]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-writing-rules.sh"
command: "bash ../project-os/tools/scripts/test-writing-rules.sh"
covers: ["[[ISS-0098-Notes-Grow-Into-Diaries]]", "[[ISS-0092-A-Note-Restates-A-Rule-It-Should-Link]]"]
tasks: ["[[TASK-0176]]", "[[TASK-0177]]"]
issues: ["[[ISS-0098-Notes-Grow-Into-Diaries]]", "[[ISS-0092-A-Note-Restates-A-Rule-It-Should-Link]]"]
artifacts: []
evidence: []
adequacy: "2026-09-26, 5 assertions. Mutations in a scratch copy: M1 rule 12 removed, 2 failures; M2 the task template's pointer removed as well, 3. Pristine 5 of 5."
related: []
---

# WRITING.md tells a note to hold its current state and to link a rule by name, and the task and feature templates point at it

## Purpose

ISS-0098 and ISS-0092 are fixed by instruction text, so the test pins the text down: the two rules exist, are numbered in sequence, and the templates an agent copies point at rule 11.

## Procedure

`bash tools/scripts/test-writing-rules.sh` in `~/Dev/repos/project-os`.

## Expected results

- Exit 0: 5 of 5, 2026-09-26.

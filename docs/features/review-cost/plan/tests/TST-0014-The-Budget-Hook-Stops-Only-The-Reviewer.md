---
type: "[[test]]"
id: TST-0014
aliases: ["TST-0014"]
title: "The budget hook stops the reviewer at its budget and leaves everyone else alone"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-review-budget.sh"
command: "bash ../project-os/tools/scripts/test-review-budget.sh"
covers: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
tasks: [TASK-0128, TASK-0129]
issues: []
artifacts: []
evidence: []
adequacy: "Checked by breaking the hook on 2026-09-18: an off-by-one at the budget, removing the note-edit exception, and ignoring the round-two packet each fail exactly the assertion meant for it; the unbroken hook passes all 13. Re-run after the warning moved to call 36 (`db98f46`): 13/13."
related: []
---

# The budget hook stops the reviewer at its budget and leaves everyone else alone

## Purpose
Recorded hook inputs: a main-session call and another subagent's call get no output; the reviewer is warned at call 36, allowed at call 40 and refused at call 41 with an instruction to report; a note edit is still allowed past the budget for ten calls; round two is refused at call 16; a repo can set its own budget; bad input fails open.

## Procedure
`bash tools/scripts/test-review-budget.sh` in `~/Dev/repos/project-os`. The command is cross-repo because every file this work changed lives in the template, the same convention as [[TST-0004]].

---
type: "[[test]]"
id: TST-0015
aliases: ["TST-0015"]
title: "The validator checks review rounds, who reported an issue, and whether an issue waiting on the owner states its question"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
scope: system
level: unit
entrypoint: "../project-os/tools/scripts/test-review-and-issue-fields.sh"
command: "bash ../project-os/tools/scripts/test-review-and-issue-fields.sh"
covers: ["[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]", "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
tasks: [TASK-0129, TASK-0133]
issues: []
artifacts: []
evidence: []
adequacy: "Checked by breaking the validator on 2026-09-18: removing the cutover date, ignoring a filled question, and allowing round 3 each fail the assertions meant for them; the unbroken validator passes all 15."
related: []
---

# The validator checks review rounds, who reported an issue, and whether an issue waiting on the owner states its question

## Purpose
Made-up notes run through validate_review_and_issue_fields: REVIEW-ROUND refuses anything but 1 or 2, as an error; ISSUE-REPORTER and ISSUE-QUESTION fire on new open issues only, not on issues created before 2026-09-19 or on fixed ones, and a filled question silences ISSUE-QUESTION.

## Procedure
`bash tools/scripts/test-review-and-issue-fields.sh` in `~/Dev/repos/project-os`. The command is cross-repo because every file this work changed lives in the template, the same convention as [[TST-0004]].

---
type: "[[change]]"
id: CHG-20260920-The-Review-Budget-Never-Blocks-The-Report
title: "A reviewer past its budget can still hand its report back"
status: merged
created: 2026-09-20
updated: 2026-09-20
owner: user:edwin
related: ["[[TASK-0145-The-Budget-Never-Blocks-The-Report]]", "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]", "[[TASK-0128-A-Hook-Stops-The-Reviewer-At-Its-Budget]]"]
tags: [review, hooks]
---

# A reviewer past its budget can still hand its report back

## What changed

An independent reviewer that spends more than 40 tool calls now returns its findings instead of losing them. Before this, the budget hook denied every call past the limit except a note edit, and the call a subagent uses to deliver its report was among those denied. The reviewer was told to write its report and then refused the only way to send it.

## Who notices

Anyone running a review gate. A long review used to end in silence: the author waited, nothing arrived, and the work had to be re-run from scratch. On 2026-09-20 that happened four times on one packet, losing about 120k tokens of completed review each time.

## Impact

- `tools/adapters/claude-code/hooks/review-budget.py`: a new `is_report` predicate and `REPORT_TOOLS`, checked before the deny and with no grace limit.
- `tools/scripts/test-review-budget.sh`: two assertions, one inside the grace window and one past it. 15 assertions, 0 failures; both new ones fail when the exemption is removed.
- Nothing else about the budget changes: the limit, the warning at call 36, round two's 15 and the note-edit grace are untouched.

## Where it landed

`~/Dev/repos/project-os` and `project-os-dev`. **The other eleven fleet repos still carry the old hook**, so a long review in any of them still loses its report. They take it at the next sync.

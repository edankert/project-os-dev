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

All thirteen fleet repos, 2026-09-20. `~/Dev/repos/project-os` `33f61d1`, `project-os-dev` `b905b88`, then the other eleven: your-trainer `2679465b`, project-os-cockpit `d1f31d6`, your-health `128262a`, your-sudoku `e2330e9`, project-os-deck `9250e44`, articles `6a85dad`, edankert.com `f9a22d7`, obsidian-supernote-sync `5f0c047`, project-os-bench `0e48cde`, your-applications.com `97b5031`, yourtrainer-mcp `9af5d28`.

Each repo's copy was byte-identical to the pre-fix template first, so every sync was a clean fast-forward of two files with nothing to merge. `test-review-budget.sh` was run in each repo after the copy: 15 assertions, 0 failures, thirteen times.

**Five of the eleven held another session's uncommitted work**, and your-health's own repair note records that repo's pre-commit hook sweeping a working `SNAPSHOT.yaml` into a commit on 2026-09-19. So each commit staged exactly the two paths and ran with `core.hooksPath=/dev/null`, and each was checked afterwards to contain two files and no more. Nothing else in any tree was staged, committed or reverted.

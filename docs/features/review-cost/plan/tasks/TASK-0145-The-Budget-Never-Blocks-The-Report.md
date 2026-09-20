---
type: "[[task]]"
id: TASK-0145
aliases: ["TASK-0145"]
title: "The budget stops the review, never the report"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-20
updated: 2026-09-20
source: ["The FEAT-0034 independent review, 2026-09-20: its second reviewer could not deliver a report, four runs running"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Small"
due: ""
depends: []
blocks: []
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[TASK-0128-A-Hook-Stops-The-Reviewer-At-Its-Budget]]"]
tests: ["[[TST-0014]]"]
---

# The budget stops the review, never the report

## Problem

A reviewer that goes past its budget loses everything it found. The hook tells it "Write your report now with what you have" and then refuses the call that delivers the report, so the author waits and nothing arrives.

Seen four times on 2026-09-20, twice with a fresh agent and twice when asked directly for the text. Each run did 30-odd tool calls of real review work and handed back nothing; about 120k tokens went to waste per run. The transcript of the last run shows nine `SubagentHandback` calls and 22 denials.

Reviews that stayed under 40 calls were unaffected, which is why this survived TASK-0128 and TASK-0130: the FEAT-0034 reviewer that delivered used 25 calls, and FEAT-0036's two used 37 and 39.

## Cause

`review-budget.py` allowed exactly one thing past the budget: an `Edit`, `Write` or `MultiEdit` under `docs/`, for `GRACE` further calls. Its docstring recorded the assumption behind that — *"Writing the report itself needs no tool call"* — which is false in Claude Code. A subagent returns its report with a `SubagentHandback` tool call, so the deny branch caught the one call the instruction demanded.

## Definition of Done

- [x] The call that returns a report is never denied, with no grace limit: a reviewer that has spent its grace still owes its report.
- [x] Two assertions in `test-review-budget.sh` cover it, one inside the grace window and one past it.
- [x] Both fail when the exemption is removed and pass when it is restored.
- [x] The docstring says why the exemption exists, so the next person does not remove it as dead weight.
- [x] Nothing else about the budget changes: the limit, the warning point, round two and the note-edit grace are untouched.
- [x] All thirteen fleet repos carry the fix, each with its test run there.

## Verification

`bash tools/scripts/test-review-budget.sh`, 2026-09-20: **15 assertions, 0 failures** (13 before this task).

Both ways, as the rule requires. With the three added lines removed from the hook: `15 assertions, 2 failure(s)` — "the reviewer can still hand its report back past the budget" and "the report still gets out after the grace calls are spent". Restored: 0 failures.

## The fleet sync, 2026-09-20

The fix reached only `project-os` and `project-os-dev` at first, and round one's second reviewer refuted the "same text after the sync" criterion on exactly that: eleven repos had no exemption. All eleven took it the same day, listed in [[CHG-20260920-The-Review-Budget-Never-Blocks-The-Report|the change note]], each verified by running its own `test-review-budget.sh` (15 assertions, 0 failures) and by a re-scan of every copy: 13 OK, 0 stale.

Five of the eleven held another session's uncommitted work, so each commit staged the two paths only and ran with hooks disabled, then was checked to contain two files. This is the hazard your-health recorded on 2026-09-19, when its pre-commit hook swept a working `SNAPSHOT.yaml` into two commits.

## Notes

The fix is three lines in the hook plus a named predicate, `is_report`, so the exemption reads as a rule rather than a special case. `REPORT_TOOLS` is a tuple because a second harness may name the call something else.

**What this does not fix.** The budget still counts the handback, and a reviewer denied 22 times still burns those calls before it gives up. Nothing tells the reviewer that its handback will be allowed, so one that reads the deny message literally may keep trying other calls first. Left alone: the exemption is enough to save the report, and more machinery here would be guessing at a harness this repo does not own.

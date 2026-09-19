---
type: "[[feature]]"
id: FEAT-0036
title: "The backlogs are cleared once"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: 'My main concern is with the your-trainer repo'"]
goal: "Every open issue in the seven fleet repos that have any is checked against today's code, and then fixed, closed as obsolete, or kept with a plain title. Edwin receives one short list of real questions per repo."
requirements: []
tasks: [TASK-0138, TASK-0139, TASK-0140, TASK-0141, TASK-0143]
release: ""
acceptance_exception: "A one-time cleanup of the record. It is checked by the exit criteria of PHASE-0007, not by a product check."
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[ISS-0033-Prune-Deletes-Entries-Whose-Notes-Cannot-Replace-Them]]", "[[ISS-0039-The-Restatement-Reached-Three-Surfaces-Of-Four]]"]
---

# The backlogs are cleared once

## Goal

The open issues no longer say what is true of the code. `your-trainer` has 121 open. 34 of them come from one review on 2026-03-01, and at least one describes code that no longer exists. This feature checks every open issue against today's code once, so the list afterwards can be trusted.

## Scope

**Each open issue ends in exactly one of four states:**

1. **Obsolete.** The code it describes no longer exists or already behaves correctly. Close it as `fixed` or `declined`, with the command that shows this.
2. **Fixed now.** It is a real defect and small. Fix it, with a test that fails without the fix. Several fixes to the same area share one task.
3. **Kept.** It is real but too big to fix now. Rewrite the title and first sentence as what a user would notice, add `reported_by:`, and link it to the feature or standing phase it belongs to.
4. **A question for Edwin.** Write the question, the options and a recommendation, and put it on one list.

**Seven legs, one at a time** (widened by Edwin on 2026-09-18 from the first three). On that date, 290 issues were open (`triage` or `open`) across the seven repos that have any:

| Order | Repo | Open | Older than August |
|---|---|---|---|
| 1 | `your-trainer` | 116 | 74 |
| 2 | `your-health` | 65 | 7 |
| 3 | `project-os-dev` | 37 | 13 |
| 4 | `project-os-cockpit` | 35 | 0 |
| 5 | `your-sudoku` | 17 | 6 |
| 6 | `project-os-deck` | 17 | 0 |
| 7 | `articles` | 3 | 2 |

your-applications.com, edankert.com, yourtrainer-mcp, project-os-bench and obsidian-supernote-sync have none.

**your-trainer goes first and calibrates the method.** Its 34 March review issues (ISS-0070 to ISS-0106) go first. The split across the four end states is recorded, and the method is adjusted before the next leg starts. Each repo's questions reach Edwin as one list when its leg ends.

**What a leg fixes, and what it keeps** (Edwin, 2026-09-18). A real defect is fixed during the cleanup only when the fix is small and in one place, with a test that fails without it. A defect that needs a build on both platforms, a behaviour Edwin would want to see, or more than a small change is **kept**: its title and first sentence say what a user notices, and it is linked to the feature or phase it belongs to, for normal feature work.

Each leg is a task under this feature, here. The repos have no standing phase for record upkeep, and minting a feature in each for a cleanup would be the phase inflation ISS-0077 warns about. What each issue became is recorded in that issue's own note, in its own repo. project-os-dev's leg includes ISS-0033 to ISS-0039 from the eight-round review.

## Acceptance

- Every issue open in the seven repos on 2026-09-18 is in one of the four states, with evidence dated on or after 2026-09-18.
- Edwin has received one list per repo of the questions that remain, each with a recommendation.
- The open count and origin mix are measured again and written into the reference note.

## Links

- Plan: [[features/backlog-clearance/plan/PLAN|PLAN]]

---
type: "[[feature]]"
id: FEAT-0036
title: "The backlogs are cleared once"
status: backlog
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: 'My main concern is with the your-trainer repo'"]
goal: "Every open issue in your-trainer, project-os-cockpit and project-os-dev is checked against today's code and then fixed, closed as obsolete, or kept with a plain title. Edwin receives one short list of real questions."
requirements: []
tasks: []
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

**Three legs, in this order:**

- **`your-trainer`** (121 open). The 34 March review issues go first. They name user-visible defects, such as wrong speed units, duplicate Strava uploads and data left behind when a user is deleted, and are the most likely to be real or obsolete.
- **`project-os-cockpit`** (37 open). ISS-0268, ISS-0307 and ISS-0301 are real bugs with small fixes.
- **`project-os-dev`** (38 open), including ISS-0033 to ISS-0039 from the eight-round review.

Each leg is a task recorded in its own repo, pointing back here.

## Acceptance

- Every issue open in the three repos on 2026-09-18 is in one of the four states, with evidence dated on or after 2026-09-18.
- Edwin has received one list per repo of the questions that remain, each with a recommendation.
- The open count and origin mix are measured again and written into the reference note.

## Links

- Plan: [[features/backlog-clearance/plan/PLAN|PLAN]]

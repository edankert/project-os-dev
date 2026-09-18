---
type: "[[feature]]"
id: FEAT-0034
title: "A review costs what the change is worth"
status: backlog
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: 'the review step/agent after doing an implementation seems to still take way too much effort (time and tokens)'"]
goal: "A feature review covers that feature's diff, follows four fixed steps and stops at about 40 tool calls, so a review takes minutes instead of twenty."
requirements: []
tasks: []
release: ""
acceptance_exception: "A process rule with no product surface. It is checked by measuring the next five reviews against the baseline, as PHASE-0007's exit criteria state."
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere]]"]
---

# A review costs what the change is worth

## Goal

A review after implementation currently takes about 160 turns, 90–100 tool calls and 20 minutes. This feature makes it cover one feature's diff, follow four fixed steps, and stop at a budget. The target is half the tool calls, with the same defects caught.

## Scope

- **One review per feature.** Several small features that close together may share one review. A phase is never reviewed as a whole again. A test reaching `passing` no longer triggers its own review, because the feature review checks its tests.
- **A fixed procedure in `independent-review/SKILL.md`:**
  1. Run the tests once.
  2. Check each acceptance criterion against the diff.
  3. Break the two or three guards the feature depends on most, and confirm a test fails each time.
  4. List anything else seen, with no further digging.
- **A budget.** The reviewer agent file says to stop at about 40 tool calls and report what it has.
- **Round counts are recorded** in the reviewed note ([[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]]), so the cap and the budget can be checked.
- **A model trial.** Run the next three small reviews on Sonnet and compare their findings with an Opus review of the same diff. Keep Sonnet only if it misses nothing that blocked.
- The review prompt a session writes is short: the diff range, the feature note and its acceptance criteria. It does not add open-ended questions of its own.

## Acceptance

- The next five `your-trainer` feature reviews have a median of 50 tool calls or fewer and 12 minutes or less.
- None of them is a phase review, and none runs a third round.
- The reviewer agent file and the skill state the procedure and the budget once, and the cockpit and `your-trainer` carry the same text after the sync.

## Links

- Plan: [[features/review-cost/plan/PLAN|PLAN]]

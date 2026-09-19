---
type: "[[feature]]"
id: FEAT-0035
title: "A finding is fixed before it is filed"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: issues 'not reported by me or written in a way that I can understand ... not fixed as part of the features they belong to and often they are marked as needing my input'"]
goal: "A defect found in a feature's own code is fixed before the feature closes. Only what needs a decision, lies outside the feature, or is too big is filed. Each issue says what a user would notice, and a question for Edwin reaches him in chat with a recommendation."
requirements: []
tasks: [TASK-0132, TASK-0133]
release: ""
acceptance_exception: "A process rule with no product surface. It is checked by what the next five features close with, as PHASE-0007's exit criteria state."
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix]]"]
---

# A finding is fixed before it is filed

## Goal

Today a review's findings, and an agent's own discoveries, become issues at `triage` while the feature closes. Nobody comes back to them. This feature makes the fix part of the feature, and sets a bar for what may still become an issue.

## Scope

- **`QUALITY.md`.** Replace ADR-0028's severity-bar bullet with ADR-0047's rule. A finding about code the feature changed is fixed before the feature closes. A test that cannot fail on the feature's main claim counts as such a finding.
- **`independent-review/SKILL.md`.** Step 5 fixes first and files only under the filing bar. Findings below the bar go in the feature's review section, not in an issue.
- **`LIFECYCLE.md`, "Scope of a change".** The rule stops applying to code the current feature changed.
- **The close-out skill and the cockpit's FEAT-0051 rule** ("fixed or filed"). A validator error the session caused is fixed. Filing is for errors that need a decision ([[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix|ISS-0028]]).
- **The issue template and `issue-intake/SKILL.md`.**
  - A `reported_by:` field, with the value `user:<name>`, `review` or `agent`.
  - A title and first sentence that name what a user would notice, following `WRITING.md`.
  - A `question:` field that must hold a question, its options and a recommendation before an issue may say it waits on the owner.
- **Questions go in chat.** When a sensible default exists, the agent takes it and states it in the close-out summary. Otherwise it asks in the turn that delivers the rest of the work, as `LIFECYCLE.md` "When to pause for the user" already says.
- **A validator warning** for an open issue with no `reported_by:`, and for one that mentions the owner's decision with no `question:`.

## Acceptance

- None of the next five features closed in `your-trainer` leaves open an issue that its own review filed against its own code, unless that issue carries a `question:`. This is measured in [[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]], with the review measurements over the same five features, so this feature closes without waiting for it (2026-09-19).
- Every issue created after the sync has `reported_by:`.
- The rule is stated once, in `QUALITY.md`. The skills link to it rather than restating it.

## Links

- Plan: [[features/fix-before-filing/plan/PLAN|PLAN]]

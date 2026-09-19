---
type: "[[feature]]"
id: FEAT-0035
title: "A finding is fixed before it is filed"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: issues 'not reported by me or written in a way that I can understand ... not fixed as part of the features they belong to and often they are marked as needing my input'"]
goal: "A defect found in a feature's own code is fixed before the feature closes. Only what needs a decision, lies outside the feature, or is too big is filed. Each issue says what a user would notice, and a question for Edwin reaches him in chat with a recommendation."
requirements: []
tasks: [TASK-0132, TASK-0133, TASK-0144]
release: ""
acceptance_exception: "A process rule with no product surface. It is checked by what the next five features close with, as PHASE-0007's exit criteria state."
reviewed_by: ["model:claude-opus-5 (reviewer A)", "model:claude-opus-5 (reviewer B)", "model:claude-opus-5 (round 2)"]
review_date: "2026-09-19"
review_round: 2
review_verdict: approved
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

## Verification

- 2026-09-19, in `~/Dev/repos/project-os` at `01031af`: `for t in tools/scripts/test-*.sh; do bash "$t"; done`, `python3 -B tools/scripts/test-retention.py`, `python3 -B tools/scripts/test-walk-preparation.py`, `python3 tools/scripts/generate-adapters.py --check` and `bash tools/scripts/validate-docs.sh`. Every script passed: 16 shell test scripts with 0 failures, retention 26 assertions, walk preparation OK, all 65 generated artifacts current, validator OK. The same code is synced to all twelve fleet repos, each passing `validate-docs.sh --as-committed`.

## Review

**Round 1, 2026-09-19: changes-requested.** Two clean-context reviewers on one packet (template `3c979ee`, FEAT-0035's files), combined here. Both reached the same verdicts.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Next five your-trainer features close with no self-filed issue without a `question:` | not checked | Measured in TASK-0131; those features have not closed. |
| 2 | Every issue created after the sync has `reported_by:` | holds | All 10 fleet issues created from 2026-09-18 carry it. |
| 3 | The rule is stated once, in `QUALITY.md`; the skills link to it | **refuted** | `independent-review/SKILL.md:79`, `issue-intake/SKILL.md:15` and `close-out/SKILL.md:59` restated the filing bar; the close-out copy had dropped "too large for the session". |
| 4–6 | `QUALITY.md`, the review skill and `LIFECYCLE.md` carry ADR-0047's rule | holds | Diff lines cited by both reviewers. |
| 7a | The close-out skill fixes an error the session caused | holds | `close-out/SKILL.md:59`. |
| 7b | The cockpit's FEAT-0051 rule ("fixed or filed") is changed | **refuted** | project-os-cockpit `CLAUDE.md:137-142` still said it, and `tests/test_coverage_registers.py:366` asserted it. |
| 8a–b | `reported_by:` and plain titles in the template and intake | holds | Template lines 11, 20; intake step 6. |
| 8c, 10 | `question:` and the ISSUE-QUESTION warning | **refuted in part** | The template's own comment "only when it waits on the owner" made every new issue warn: the check read the frontmatter. "working for Edwin" also warned. |
| 9 | Questions go in chat with a recommendation | holds | Skill lines cited. |
| 11 | TST-0015 fails when its behaviour is broken | **refuted in part** | Removing the call in `validate()` and dropping `triage` both left it passing. |
| 12 | TST-0006 fails when its behaviour is broken | holds | Ten words over budget fails it. |

**Fixed before round 2** (template `badc195`, cockpit `0e0fb0c`): the skills link to the filing bar; ISSUE-QUESTION reads the body only and no longer matches "for <name>"; TST-0015 gained a triage case, a real-template case and an end-to-end run, each shown to fail without its fix; the cockpit's `CLAUDE.md` rule and its test follow ADR-0047. Observations not acted on: the ISSUE-QUESTION phrase match will miss some wordings (a heuristic by design, as the validator comment says); `LIFECYCLE.md` is near its word budget.

**Round 2, 2026-09-19: approved.** One reviewer, fix diff only, 10 of 15 calls. Claims 3, 7b, 8c/10 and 11: *fixed*, each with its command; the reviewer broke four guards on a copy and each broke the test. Its one note, that the cockpit's `CLAUDE.md` now restated the filing bar's conditions, was fixed at once (cockpit `ea68d80`). Claim 1 stays with [[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]].

## Links

- Plan: [[features/fix-before-filing/plan/PLAN|PLAN]]

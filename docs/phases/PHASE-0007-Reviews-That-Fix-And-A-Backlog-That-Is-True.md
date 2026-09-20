---
type: "[[phase]]"
id: PHASE-0007
title: "Reviews that fix, and a backlog that is true"
status: active
order: 7
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
goal: "A review costs what the change is worth and its findings are fixed in the feature that caused them, so the open issues in every repo are real, readable, and mostly reported by a person."
features: [FEAT-0034, FEAT-0035, FEAT-0036, FEAT-0037]
requirements: []
tasks: [TASK-0126, TASK-0127, TASK-0128, TASK-0129, TASK-0130, TASK-0131, TASK-0132, TASK-0133, TASK-0134, TASK-0135, TASK-0136, TASK-0137]
issues: [ISS-0028, ISS-0062, ISS-0033, ISS-0034, ISS-0035, ISS-0036, ISS-0037, ISS-0038, ISS-0039]
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]"]
tags: [review, issues, fleet]
---

# Reviews that fix, and a backlog that is true

## Goal

Edwin raised two problems on 2026-09-18. A review after implementation takes too much time and too many tokens. And the repos fill up with issues he did not report, cannot easily read, and that are not fixed in the features they belong to. Many of them wait on him. His main concern is `your-trainer`.

This phase fixes both problems at the rule level, in the template, so every repo gets the fix. It then clears the existing backlogs once, starting with `your-trainer`. The measurements behind it are in [[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT|the 2026-09-18 reference note]]. The rule change is [[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It|ADR-0047]], which is `proposed` until Edwin accepts it.

## Scope

- [[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth|FEAT-0034]]: a review starts from a generated packet holding the diff, gives a verdict on a fixed list of claims, runs only targeted tests, and is stopped by a hook at 40 tool calls. Round two only verifies fixes, with a 15-call limit. Before rollout, the new review is re-run against FEAT-0107's code as it was before the fixes, and must find the defects the old review found. Six tasks, TASK-0126 to TASK-0131.
- [[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed|FEAT-0035]]: a finding in the feature's own code is fixed before the feature closes. What may be filed, how an issue is written, and how a question reaches Edwin all change. This absorbs [[ISS-0028-Close-Out-Has-No-Answer-For-Cannot-Fix|ISS-0028]].
- [[FEAT-0036-The-Backlogs-Are-Cleared-Once|FEAT-0036]]: every open issue in the seven fleet repos that have any (290 on 2026-09-18) is checked against the current code, then fixed, closed as obsolete, kept with a plain title, or put on one list of questions for Edwin. `your-trainer` goes first and calibrates the method. Widened by Edwin on 2026-09-18 from three repos to seven.
- The seven issues left by the eight-round review, ISS-0033 to ISS-0039, are settled as part of this repo's leg of FEAT-0036.

## Out of Scope

- **The cost of rewriting acceptance-check procedures in `your-trainer`.** Since 2026-08-29, 47 general-purpose runs took 439 minutes, more than its 13 reviews (310 minutes). It is real, but it is not review cost, and it belongs to the walk work ([[PHASE-0005-The-Walk-Reads-As-A-Script|PHASE-0005]]).
- The five fleet repos with no open issues. The other nine repos did get the new rules, at the syncs recorded in [[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]].
- Removing independent review. The FEAT-0107 review found real defects; what goes wrong is what happens to its findings afterwards.

## Exit Criteria

- [x] Edwin has accepted or amended ADR-0047. The rule text is in `~/Dev/repos/project-os` and synced to `your-trainer` and `project-os-cockpit`, including the cockpit's `QUALITY.md`, which is two months behind.
- [x] A review costs less than the one it replaces. Measured in [[TASK-0130-Re-Run-The-FEAT-0107-Review-The-New-Way|TASK-0130]]: two reviewers on one packet took 64 tool calls, 10.1M context tokens and 6.2 minutes against a baseline of about 95 calls and about 20 minutes. The plan to confirm this over five live `your-trainer` reviews was cancelled on 2026-09-20; see "The five measured reviews are cancelled" below.
- [x] A feature does not close with an open issue its own review filed against its own code, unless that issue states a product question. The rule is ADR-0047 and `QUALITY.md`'s filing bar, and the validator holds it. It was to be measured over the same five reviews; that measurement went with them.
- [x] Every open issue in the seven repos that had any on 2026-09-18 has been checked against the code on or after that date. Each has a `reported_by:` field and a title that names what a user would notice. The last two without a reporter, your-health ISS-0164 and ISS-0180, were named on 2026-09-20 (your-health `f8a3404`).
- [x] Every open issue waiting on Edwin states its question, the options and a recommendation. They are handed to him as one list, not found one at a time.

## Notes

- **Order.** The rules go first (FEAT-0035, then FEAT-0034), so the cleanup is not refilled by the old rules while it runs. The `your-trainer` leg of FEAT-0036 can start in parallel, because checking an issue against the code does not depend on the new rules.
- **Where the work lands.** Rule files live in `~/Dev/repos/project-os`. This repo holds the record. The cleanup work is done in each repo and recorded there, with a pointer back here.
- **Measuring.** The reference note gives the transcript query. Run it again after five reviews and put the numbers in this note.

## Progress, 2026-09-19

- **FEAT-0035 and FEAT-0037 are done**, each after a two-reviewer round and a round two that approved. FEAT-0034 waits only on [[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]]: the five measured reviews, which also measure FEAT-0035's acceptance. The Sonnet trial is dropped (Edwin, 2026-09-19).
- **The issue check reached all seven repos.** Open issues went from 290 on 2026-09-18 to 154. Every open issue has `reported_by:` except your-health ISS-0164 and ISS-0180, which another session is working on, so the fourth exit criterion stays unticked for those two. Each repo's questions reached Edwin as one list; the last four repos' are in [[TASK-0141-The-Last-Four-Repos-Open-Issues-Are-Checked-Against-The-Code|TASK-0141]].
- **A new rule**: a failing test is fixed, whoever broke it and whenever (ADR-0047 amendment, [[TASK-0144-A-Failing-Test-Is-Fixed-Whoever-Broke-It|TASK-0144]]). The cockpit's suite went from 6 failures to none.
- **Step 4, the small fixes.** your-trainer [[your-trainer#ISS-0484]]: 13 of 15 fixed (your-trainer `060e7ea0`); ISS-0429 (the paywall sentence) and ISS-0248 (the ride screen's font cap) are made and wait for Edwin to see them. Android 1,377 tests and iOS 877 pass, with no failures. your-health [[your-health#ISS-0181]]: 14 of 18 fixed (your-health `b1df1df`); ISS-0152 and ISS-0158 wait for Edwin to see them, and ISS-0132 and ISS-0173 wait for another session's meal work. 2,810 tests pass. Each fix has a test that fails without it.
- **Found on the way**: your-trainer's git hooks were committed without the executable bit, so a fresh clone or worktree never ran them (fixed, `eaf9c304`). your-health's checkout was switched from `food-diary-phases-16-17` to `main` at 18:56 on 2026-09-19 by someone else, so today's syncs and fixes are on `main`.
- **Still to do**: the work orders cockpit ISS-0313 (7), your-sudoku ISS-0117 (5) and project-os-deck ISS-0089 (3) are written and not started. TASK-0131 measures the next five your-trainer reviews.

## Progress, 2026-09-20

**The last three work orders are worked.** Thirteen of their fifteen issues are fixed, each with a test that fails when the fix is taken out; the other two are made and wait for Edwin to look at them. All five repos' small-fix lists are now done, and open issues across the seven repos are down from 290 on 2026-09-18 to 112.

| Repo | Work order | Fixed | Waiting for Edwin | Commits |
|---|---|---|---|---|
| `project-os-cockpit` | [[project-os-cockpit#ISS-0313]] | 6 of 7 | ISS-0301, the write guard | `2c6059a` … `34ba0ce` |
| `your-sudoku` | [[your-sudoku#ISS-0117]] | 4 of 5 | ISS-0092, the loading grid | `0c87512` … `ec0fa2c` |
| `project-os-deck` | [[project-os-deck#ISS-0089]] | 3 of 3 | none | `90cac9b` … `3b859d7` |

- **One of the fifteen was a live defect, not a latent one.** In the cockpit, ticking a checkbox on a page whose task list opens directly after a paragraph wrote to a different row in the file and still answered `{"ok": true}` (ISS-0184). The issue's own withdrawn section had said the counts agreed; they agree only on the file it was tested against.
- **The product id is now the one the requirement registers.** Android sold `premium` and iOS sold `com.yoursudoku.premium`; both now sell `com.yoursudoku.pro`, which [[your-sudoku#REQ-0109]] names, and a CI script compares the two strings on every push (your-sudoku TST-0084). This had to land before TASK-0168 creates the Play Console product, because a product id cannot be renamed afterwards.
- **The cockpit's write guard is wider than its ticket described.** Five write handlers kept a private copy of the body reader and would have kept the hole; all five now go through the guarded reader and gain a size cap they never had. Every client already sent `Content-Type: application/json`, so nothing broke.
- **Deck's smoke run stops taking the keyboard.** On macOS `run-smoke.sh` now hands over to `smoke-in-a-box.sh` instead of calling `app.focus({steal:true})` 24 times. It needs Docker running locally; CI is Linux and unaffected.
- **Left for Edwin to see, across all five repos**: cockpit ISS-0301, your-sudoku ISS-0092, your-trainer ISS-0429 and ISS-0248, your-health ISS-0152 and ISS-0158. Each is fixed in code and held open only until he has looked.
- **Nothing is pushed.** All four repos were already ahead of origin before this work, so the commits are local.

### The five measured reviews are cancelled

**The phase does not need five more reviews to prove its point.** Edwin, 2026-09-20: "we agreed we would have the 2 parallel verification/validation agents instead ... this was reviewed previously and was deemed to be the most suitable solution, no need to re-test." [[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]] is `cancelled` and carries the full reason.

Two reviewers on one packet was chosen in [[TASK-0130-Re-Run-The-FEAT-0107-Review-The-New-Way|TASK-0130]], on four clean runs against a review whose answers were known. The pair found both blocking defects and neither single-reviewer run did, at 64 tool calls, 10.1M context tokens and 6.2 minutes. `QUALITY.md` has stated the rule since 2026-09-18. Running five live reviews would measure the same thing again.

**The review gate is untouched.** A feature reaching `done` still owes a review, and that review is still two reviewers run at once. What ends is the plan to re-measure it.

With this, FEAT-0034 has no outstanding work and its acceptance is met.

---
type: "[[phase]]"
id: PHASE-0007
title: "Reviews that fix, and a backlog that is true"
status: active
order: 7
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
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
- [ ] The next five feature reviews in `your-trainer` have a median of 50 tool calls or fewer and 12 minutes or less. The baseline is about 95 tool calls and about 20 minutes.
- [ ] None of those five features closes with an open issue its own review filed against its own code, unless that issue states a product question.
- [ ] Every open issue in the seven repos that had any on 2026-09-18 has been checked against the code on or after that date. Each has a `reported_by:` field and a title that names what a user would notice.
- [ ] Every open issue waiting on Edwin states its question, the options and a recommendation. They are handed to him as one list, not found one at a time.

## Notes

- **Order.** The rules go first (FEAT-0035, then FEAT-0034), so the cleanup is not refilled by the old rules while it runs. The `your-trainer` leg of FEAT-0036 can start in parallel, because checking an issue against the code does not depend on the new rules.
- **Where the work lands.** Rule files live in `~/Dev/repos/project-os`. This repo holds the record. The cleanup work is done in each repo and recorded there, with a pointer back here.
- **Measuring.** The reference note gives the transcript query. Run it again after five reviews and put the numbers in this note.

---
type: "[[task]]"
id: TASK-0138
aliases: ["TASK-0138"]
title: "your-trainer's open issues are checked against the code"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]", "Edwin, 2026-09-18: 'I agree, please widen'"]
parent: "[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"
effort: "Large"
due: ""
depends: []
blocks: []
related: []
tests: []
---

# your-trainer's open issues are checked against the code

## Definition of Done
- [ ] The 34 March review issues (ISS-0070 to ISS-0106) are each obsolete, fixed, kept or a question, with evidence dated 2026-09-18 or later in the issue's own note. How they split is recorded here, and it calibrates the method.
- [ ] The other open issues, 116 in all on 2026-09-18, are done the same way, grouped by area.
- [ ] Each fix is small and in one place, with a test that fails without it; anything bigger is kept, with a plain title and a link to its feature.
- [ ] Edwin has received one list of the questions that remain, each with a recommendation.
- [ ] The open count and origin mix are measured again.

## Calibration: the 35 March issues, 2026-09-18

Checked by four read-only reviewers working in parallel, about nine issues each. Their evidence was spot-checked for six issues and matched every time. Every edit was made in the main session. Committed as your-trainer `5907995f`.

| End state | Count | Issues |
|---|---|---|
| Already fixed by later work, still marked open | 28 | ISS-0070 to 0089, 0091, 0093 to 0098, 0102 |
| Fixed now, small, with a test that fails without it | 1 | ISS-0092: iOS left a deleted rider's personal bests |
| Kept, real and user-visible, retitled and linked | 1 | ISS-0106: the Android paywall shows made-up prices when products fail to load (PHASE-020) |
| Declined: true, but no user would notice | 4 | ISS-0099, 0101, 0103, 0104 |
| Question for Edwin | 1 | ISS-0090: raise the iOS minimum to 18 for `#Index`? Recommendation: no |

One new issue was found while checking, and filed: ISS-0482, a ride whose Strava upload was interrupted is never uploaded again (iOS).

**What this says about the method.** 80% were stale: already fixed, with the note never updated. Only 2 of 35 were real defects a rider would notice. So the cost is in the checking, not the fixing, and batches of about nine per read-only reviewer work: about 60 seconds and about 60k tokens each. The method stays as it is for the rest of your-trainer's open issues. Before a note is closed on a reviewer's word, its evidence is spot-checked.

## The other 80, 2026-09-18

Eight read-only reviewers checked ten issues each: 256 seconds, about 760k tokens in total. That ran as a Workflow, which Edwin had not asked for by that tool's name. The work and its cost were what eight reviewer agents would have been, and he was told. Evidence was spot-checked on four of the already-fixed issues. Ten table rows were misaligned, because a `|` inside evidence split their cells. Those notes were caught by a scan and rewritten by hand. Committed as your-trainer `50cb082d`.

| End state | Count |
|---|---|
| Already fixed by later work | 16 |
| Declined: nobody would notice | 3 |
| Real, kept, with what a user notices and the feature it belongs to | 29, plus ISS-0399, whose code is fixed but which awaits TASK-0881's simulator check |
| Real and small, fix recorded and not yet made | 17 |
| Question for Edwin, with a recommendation | 14 |

**These differ from the March batch.** Only 20% were stale, against 80% of March's. Newer issues are mostly real, because they were filed recently and against code that has not moved since. So from here the cost is the fixing and the deciding, not the checking. That is what the next legs should expect.

**Where the 17 small fixes belong.** Four fall inside features that are still in progress in another session: ISS-0374 (high: a paying rider drops to FREE when the Play Store errors) and ISS-0411 under FEAT-0104, and ISS-0464 and 0466 under FEAT-0107. Under ADR-0047 they are fixed in those features. ISS-0379 is the cockpit's code, and ISS-0276 is yourtrainer-mcp's. That leaves 11 fixes in your-trainer for the cleanup.

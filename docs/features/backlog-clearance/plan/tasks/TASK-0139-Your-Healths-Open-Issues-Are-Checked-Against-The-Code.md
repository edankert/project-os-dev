---
type: "[[task]]"
id: TASK-0139
aliases: ["TASK-0139"]
title: "your-health's open issues are checked against the code"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-20
source: ["[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]", "Edwin, 2026-09-18: 'first check your-health'"]
parent: "[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"
effort: "Large"
due: ""
depends: []
blocks: []
related: ["[[TASK-0138-Your-Trainers-Open-Issues-Are-Checked-Against-The-Code]]"]
tests: []
---

# your-health's open issues are checked against the code

## Definition of Done
- [x] Each of the 63 open issues is obsolete, fixed, kept, declined or a question, with evidence dated 2026-09-18 or later in its own note. **This leg skipped two**, ISS-0164 and ISS-0180, because another session held uncommitted work on them from 2026-09-13. Both were checked on 2026-09-20 (your-health `521eb34`), after the round-one review, and both are **kept**. See "Closed out" below.
- [x] Small fixes are collected into one work-order issue, [[your-health#ISS-0181]], which grew to eighteen items after Edwin's decisions. Fourteen were fixed on 2026-09-19 (your-health `b1df1df`), each with a test that fails without it.
- [x] Edwin has received one list of questions, each with a recommendation. Eight questions; he took all eight recommendations. See "Decisions and a repair" below.
- [x] The uncommitted work in your-health (21 files, including SNAPSHOT.yaml) stays out of every commit. It leaked twice through the pre-commit hook and was removed in `ab1e790`; see "Repair" below.

## Result, 2026-09-18

Seven read-only reviewers checked nine issues each, as ordinary agents. Their evidence was spot-checked for five issues and matched every time. Committed as your-health `0bdf4af`.

| End state | Count |
|---|---|
| Already done, still marked open | 23 |
| Declined: nobody would notice today | 5 |
| Real, kept, with what a reader notices | 15 |
| Real and small, collected into work order [[your-health#ISS-0181]] | 12 |
| Question for Edwin | 8 |

**37% were stale**, between your-trainer's March batch (80%) and its newer issues (20%). The record trailed the code by about two weeks: several fixes committed on 2026-09-02 still showed as open, backlog or planned.

**Kept with care.** ISS-0170 (high: a meal section set out of order makes a meal reach Health Connect as a near-whole-day record) is kept to be coordinated with TASK-0446, whose uncommitted change to the same code lengthens those spans. ISS-0112 is the template validator's, and is filed here as [[ISS-0070-A-Snapshot-That-Does-Not-Parse-Still-Passes-Validation|ISS-0070]].

**The other session's work stayed out.** your-health had 21 uncommitted files from another session, SNAPSHOT.yaml among them. The committed snapshot was rebuilt in a worktree at HEAD with only this review's notes, and staged from there. Their files are unchanged.

## Decisions and a repair, 2026-09-18

Edwin took all eight recommendations ("take your recommendations"). ISS-0026 and ISS-0130 are declined. ISS-0169, 0049, 0150, 0127, 0047 and 0158 become fixes, added to [[your-health#ISS-0181]], which now has eighteen items. Committed as your-health `7357d39`.

**Repair.** The pre-commit hook in your-health runs `sync-snapshot.py` on the working tree and re-adds `SNAPSHOT.yaml`. So `0bdf4af` and `7357d39` both committed the working snapshot, which still held another session's uncommitted focus, a TASK-0446 entry and two statuses, instead of the snapshot built for them. HEAD then failed `--as-committed` with five errors. `ab1e790` removed those lines, committed from a clean worktree at HEAD so the hook could not pull them in again. The other session's change was restored to its working tree, uncommitted. HEAD now passes the full CI step set. your-applications.com, where the same staging was used, was checked and is clean.

## Closed out, 2026-09-20

The task sat at `doing` with every box unticked while its own Result and Decisions sections described a finished leg. Both independent reviewers of [[FEAT-0036-The-Backlogs-Are-Cleared-Once|FEAT-0036]] found the contradiction on 2026-09-20. The boxes above are now ticked against what the sections already recorded, and the status is `done`.

**What this leg did not do itself.** ISS-0164 and ISS-0180 were not checked while this leg ran, because another session held uncommitted work on both files. That gap was the first thing FEAT-0036's round-one review refuted, and it was closed on 2026-09-20: both are now checked against the code (your-health `521eb34`) and both are **kept**, because each one's fix is written in the working tree, absent from HEAD, and owned by a task that is still `doing` — [[your-health#TASK-0431]] and [[your-health#TASK-0446]].

So the leg's own scope was 61 of 63 issues, and the two it left are accounted for elsewhere rather than forgotten. They stay `open`.


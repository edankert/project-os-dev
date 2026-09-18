---
type: "[[task]]"
id: TASK-0140
aliases: ["TASK-0140"]
title: "project-os-dev's open issues are checked against the template"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]", "Edwin, 2026-09-18: 'yes' (continue with project-os-dev)"]
parent: "[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"
effort: "Large"
due: ""
depends: []
blocks: []
related: ["[[TASK-0138-Your-Trainers-Open-Issues-Are-Checked-Against-The-Code]]", "[[TASK-0139-Your-Healths-Open-Issues-Are-Checked-Against-The-Code]]"]
tests: []
---

# project-os-dev's open issues are checked against the template

## Definition of Done
- [x] Each of the 36 issues open on 2026-09-18 is obsolete, fixed, kept, declined or a question, with evidence in its own note. ISS-0068, 0069 and 0070 are left out: they were filed the same day.
- [x] Small fixes are made in `~/Dev/repos/project-os`, each with a test that fails without it, and synced. This repo's issues are the template's own, so no other repo's session owns them.
- [x] Edwin has received one list of questions, each with a recommendation.
- [x] Edwin's uncommitted edits to ADR-0016 and ADR-0027 stay out of every commit.

## Result, 2026-09-18

All 36 issues were checked by four clean-context agents against the template, and each verdict was checked here before it was applied.

| verdict | count | issues |
| --- | --- | --- |
| already fixed by later work | 9 | ISS-0024, 0026, 0030, 0032, 0033, 0034, 0038, 0039, 0064 |
| fixed today | 13 | ISS-0060 (template a978752); ISS-0020, 0021, 0022, 0025, 0029, 0035, 0037, 0049, 0050, 0054, 0059 (template 3e12cff); ISS-0036 (ADR-0018 corrected here) |
| declined | 2 | ISS-0005, 0023 |
| kept open, with what someone notices | 9 | ISS-0017, 0018, 0019, 0027, 0031, 0040, 0052, 0053 (narrowed), 0067 (goes with TASK-0125) |
| a question for Edwin | 3 | ISS-0063, 0065, 0066 |

Both template commits are synced to the ten fleet repos that take the template's validator. Every code fix has a test that fails without it: each was reverted in a copy and the test run again.

Also fixed on the way: TST-0003 and CHG-20260804 had unescaped quotes in `review_note:`, so their frontmatter did not parse and TST-0003's `approved` verdict was invisible. Edwin's ADR-0016 and ADR-0027 acceptance was committed on his instruction (6a340c1), which made this repo pass `--as-committed` again.


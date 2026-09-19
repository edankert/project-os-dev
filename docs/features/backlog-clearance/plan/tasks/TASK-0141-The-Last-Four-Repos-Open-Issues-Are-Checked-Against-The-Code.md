---
type: "[[task]]"
id: TASK-0141
aliases: ["TASK-0141"]
title: "The last four repos' open issues are checked against the code"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-19
updated: 2026-09-19
source: ["[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]", "Edwin, 2026-09-19: 'Do all 5 steps in the suggested order'"]
parent: "[[FEAT-0036-The-Backlogs-Are-Cleared-Once]]"
effort: "Large"
due: ""
depends: []
blocks: []
related: ["[[TASK-0138-Your-Trainers-Open-Issues-Are-Checked-Against-The-Code]]", "[[TASK-0139-Your-Healths-Open-Issues-Are-Checked-Against-The-Code]]", "[[TASK-0140-Project-Os-Devs-Open-Issues-Are-Checked-Against-The-Template]]"]
tests: []
---

# The last four repos' open issues are checked against the code

## Definition of Done
- [ ] Each of the 72 issues open on 2026-09-19 is obsolete, kept, declined or a question, with evidence dated 2026-09-19 in its own note: project-os-cockpit 35, your-sudoku 17, project-os-deck 17, articles 3.
- [ ] Each open issue that is kept has `reported_by:` and a title and first sentence that say what a user would notice.
- [ ] Small fixes found real are collected into one work-order issue per repo, as your-trainer's ISS-0484 and your-health's ISS-0181 were.
- [ ] Edwin has received one list of the questions from all four repos, each with a recommendation.
- [ ] Uncommitted work from other sessions stays out of every commit. On 2026-09-19 that was articles' evidence-refresh notes.

## Method

The four legs run as one sitting, so Edwin gets one list of questions, not four. Nine read-only checkers work in parallel, about nine issues each, and write their verdicts into the issue notes. Nothing is committed by a checker. Their evidence is spot-checked here before each repo is committed.

Most of these issues were filed in August or later. The earlier legs found 20% of recent issues stale, against 80% of old ones, so most of the cost here is expected to be deciding, not checking.

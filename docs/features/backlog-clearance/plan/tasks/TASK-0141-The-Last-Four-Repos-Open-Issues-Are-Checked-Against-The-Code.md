---
type: "[[task]]"
id: TASK-0141
aliases: ["TASK-0141"]
title: "The last four repos' open issues are checked against the code"
status: done
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
- [x] Each of the 72 issues open on 2026-09-19 is obsolete, kept, declined or a question, with evidence dated 2026-09-19 in its own note: project-os-cockpit 35, your-sudoku 17, project-os-deck 17, articles 3.
- [x] Each open issue that is kept has `reported_by:` and a title and first sentence that say what a user would notice.
- [x] Small fixes found real are collected into one work-order issue per repo, as your-trainer's ISS-0484 and your-health's ISS-0181 were.
- [x] Edwin has received one list of the questions from all four repos, each with a recommendation.
- [x] Uncommitted work from other sessions stays out of every commit. On 2026-09-19 that was articles' evidence-refresh notes.

## Method

The four legs run as one sitting, so Edwin gets one list of questions, not four. Nine read-only checkers work in parallel, about nine issues each, and write their verdicts into the issue notes. Nothing is committed by a checker. Their evidence is spot-checked here before each repo is committed.

Most of these issues were filed in August or later. The earlier legs found 20% of recent issues stale, against 80% of old ones, so most of the cost here is expected to be deciding, not checking.

## Result, 2026-09-19

Nine read-only checkers, about nine issues each. Their evidence was spot-checked on five "already fixed" verdicts and matched every time. One verdict was corrected: cockpit ISS-0260 said no check reports broken frontmatter, but NOTE-FRONTMATTER does.

| Repo | Open | Fixed | Declined | Kept | Question | Commit |
|---|---|---|---|---|---|---|
| project-os-cockpit | 35 | 9 | 2 | 19 | 5 | `d67add8` |
| your-sudoku | 17 | 2 | 3 | 7 | 5 | `8438be9` |
| project-os-deck | 17 | 5 | 3 | 6 | 3 | `44e4f6d` |
| articles | 3 | 1 | 0 | 2 | 0 | branch `iss-check-0919`, `bbe1247` |

Two cockpit issues, ISS-0257 and ISS-0273, were fixed in the template the same day (project-os `01031af`). **Work orders** for the small fixes among the kept: cockpit [[project-os-cockpit#ISS-0313]] (seven), your-sudoku [[your-sudoku#ISS-0117]] (five), project-os-deck [[project-os-deck#ISS-0089]] (three).

**articles is not merged yet.** Another session has an uncommitted `SNAPSHOT.yaml` in articles, and it does not parse. The commit also updates the snapshot, so it waits on branch `iss-check-0919` until that session commits. ISS-0004's note is part of that session's uncommitted work and stays with it.

**Newer issues are mostly real.** 16 of 72 were stale (22%), in line with the 20% for recent issues in your-trainer.

## The questions, handed to Edwin as one list, 2026-09-19

1. cockpit ISS-0236: keep a feature's `platform:` authored, or derive it from releases? Recommend: keep authored, decline.
2. cockpit ISS-0258: should a release derive which checks its changes may break? Recommend: no, record it as a limit in ADR-0040.
3. cockpit ISS-0269: does a retired check still count as covering its feature? Recommend: no, the validator skips it, matching the cockpit.
4. cockpit ISS-0286: how does a one-codebase app avoid owing its suite once per OS? Recommend: an optional `platform:` on a check.
5. cockpit ISS-0309: a procedure quoting a check with no Expect section: refuse, or accept and mark it unverified? Recommend: mark it unverified.
6. your-sudoku ISS-0089: after a finished game, should iPhone keep offering Continue on an older game? Recommend: yes, decline.
7. your-sudoku ISS-0103: should a filled `review_response:` clear the REVIEW error on a passing test? Recommend: yes.
8. your-sudoku ISS-0110: where does a risk record its phase? Recommend: a `phase:` field on the risk template.
9. your-sudoku ISS-0114: does a reinstall refill the five free puzzles, and does a retry cost one? Recommend: no refill, retries free.
10. your-sudoku ISS-0115: may Thursday's daily grade Master? Recommend: yes, keep it free.
11. project-os-deck ISS-0008: is the smoke run enough of a gate for the renderer? Recommend: yes, decline.
12. project-os-deck ISS-0069: where do approve and decline go in Spread and List? Recommend: one line at the top of the reader.
13. project-os-deck ISS-0086: add layers to the outer field, or narrow FEAT-0018's title? Recommend: narrow the title.

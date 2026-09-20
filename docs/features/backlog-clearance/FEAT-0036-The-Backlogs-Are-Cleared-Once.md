---
type: "[[feature]]"
id: FEAT-0036
title: "The backlogs are cleared once"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-20
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: 'My main concern is with the your-trainer repo'"]
goal: "Every open issue in the seven fleet repos that have any is checked against today's code, and then fixed, closed as obsolete, or kept with a plain title. Edwin receives one short list of real questions per repo."
requirements: []
tasks: [TASK-0138, TASK-0139, TASK-0140, TASK-0141, TASK-0143]
release: ""
reviewed_by: ["model:claude-opus-5", "model:claude-opus-5"]
review_date: 2026-09-20
review_round: 1
review_verdict: changes-requested
acceptance_exception: "A one-time cleanup of the record. It is checked by the exit criteria of PHASE-0007, not by a product check."
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[ISS-0033-Prune-Deletes-Entries-Whose-Notes-Cannot-Replace-Them]]", "[[ISS-0039-The-Restatement-Reached-Three-Surfaces-Of-Four]]"]
---

# The backlogs are cleared once

## Goal

The open issues no longer say what is true of the code. `your-trainer` has 121 open. 34 of them come from one review on 2026-03-01, and at least one describes code that no longer exists. This feature checks every open issue against today's code once, so the list afterwards can be trusted.

## Scope

**Each open issue ends in exactly one of four states:**

1. **Obsolete.** The code it describes no longer exists or already behaves correctly. Close it as `fixed` or `declined`, with the command that shows this.
2. **Fixed now.** It is a real defect and small. Fix it, with a test that fails without the fix. Several fixes to the same area share one task.
3. **Kept.** It is real but too big to fix now. Rewrite the title and first sentence as what a user would notice, add `reported_by:`, and link it to the feature or standing phase it belongs to.
4. **A question for Edwin.** Write the question, the options and a recommendation, and put it on one list.

**Seven legs, one at a time** (widened by Edwin on 2026-09-18 from the first three). On that date, 290 issues were open (`triage` or `open`) across the seven repos that have any:

| Order | Repo | Open | Older than August |
|---|---|---|---|
| 1 | `your-trainer` | 116 | 74 |
| 2 | `your-health` | 65 | 7 |
| 3 | `project-os-dev` | 37 | 13 |
| 4 | `project-os-cockpit` | 35 | 0 |
| 5 | `your-sudoku` | 17 | 6 |
| 6 | `project-os-deck` | 17 | 0 |
| 7 | `articles` | 3 | 2 |

your-applications.com, edankert.com, yourtrainer-mcp, project-os-bench and obsidian-supernote-sync have none.

**your-trainer goes first and calibrates the method.** Its 34 March review issues (ISS-0070 to ISS-0106) go first. The split across the four end states is recorded, and the method is adjusted before the next leg starts. Each repo's questions reach Edwin as one list when its leg ends.

**What a leg fixes, and what it keeps** (Edwin, 2026-09-18). A real defect is fixed during the cleanup only when the fix is small and in one place, with a test that fails without it. A defect that needs a build on both platforms, a behaviour Edwin would want to see, or more than a small change is **kept**: its title and first sentence say what a user notices, and it is linked to the feature or phase it belongs to, for normal feature work.

Each leg is a task under this feature, here. The repos have no standing phase for record upkeep, and minting a feature in each for a cleanup would be the phase inflation ISS-0077 warns about. What each issue became is recorded in that issue's own note, in its own repo. project-os-dev's leg includes ISS-0033 to ISS-0039 from the eight-round review.

## Acceptance

- Every issue open in the seven repos on 2026-09-18 is in one of the four states, with evidence dated on or after 2026-09-18.
- Edwin has received one list per repo of the questions that remain, each with a recommendation.
- The open count and origin mix are measured again and written into the reference note.

## Verification

`python3 tools/scripts/run-tests.py`, 2026-09-20: **passing=17 failing=0 unrunnable=0** over 15 commands. `bash tools/scripts/validate-docs.sh` is OK, and `--as-committed` passes.

This feature carries an `acceptance_exception:`: it is a one-time cleanup of the record across seven repos, so no command in this repo can check it. Its evidence is the issue notes in each repo, the per-repo counts recorded in the reference note (290 open on 2026-09-18, 112 on 2026-09-20), and PHASE-0007's exit criteria.

## Review

**Round 1, 2026-09-20. Verdict: `changes-requested`.** Two reviewers on one packet, each in a clean context (`model:claude-opus-5` both). Their reports are combined here: a claim either marked *refuted* with evidence is refuted; where they disagreed on a number, the count was re-run.

| Claim | Combined verdict | Evidence |
|---|---|---|
| Every issue open on 2026-09-18 is in one of the four states, with evidence dated on or after that date | **refuted in part** | Both reviewers took each repo's last commit of 2026-09-17 as a baseline and checked every issue open there. 286 of 289 carry a dated check. Three do not, in two groups, below. |
| Edwin has received one list per repo of the questions that remain | **refuted** | Both found the same thing. your-trainer, your-health and project-os-dev each got their own list. The last four repos got **one combined list of 13 questions** (TASK-0141, whose own wording says so). Every question reached Edwin with a recommendation; the count of lists is what fails. |
| The open count and origin mix are measured again and written into the reference note | holds | Both reproduced the "Measured again, 2026-09-20" section. One matched 112 exactly, per repo and in the mix (62 agent / 31 review / 19 Edwin); the other counted 113 for a transient reason, settled below. |
| No issue was closed by editing its status alone | holds | Independently checked by both, over every baseline-open issue now at a terminal status: 182 and 185 closures counted, **zero** status-only. Each added at least two lines of prose beyond frontmatter. |
| `your-trainer` goes first and calibrates the method | holds | TASK-0138 records the split, and its finding — 80% of the March issues stale against 20% of recent ones — is carried into TASK-0141's method. |
| Kept issues carry `reported_by:` and a title a user would notice | holds | All 112 carry the field. Titles sampled across three repos are user-facing and linked to a feature or phase. Not a census of all 112. |
| cockpit ISS-0301's write guard and your-sudoku ISS-0092's loading view are genuinely in the code | holds | Both reviewers read the committed code; one ran `pytest tests/test_write_content_type.py` → 9 passed. Working trees clean, so this is committed, not staged prose. |
| The packet's full run, `passing=17 failing=0` | **not refuted** — the reported failure was environmental | One reviewer found `test-metric-counts.sh` failing. It passes on the source; the harness had run a 14 September compile from a bytecode cache Apple's Python keeps outside the repo. Recorded as [[ISS-0073-A-Validator-Test-Can-Run-Against-Code-That-Is-Not-The-Source|ISS-0073]], because the hazard runs both ways. |

### The three issues without a dated check

- **your-health ISS-0164 and ISS-0180.** Another session held uncommitted work on them from 2026-09-13, so the leg skipped them. TASK-0139's first box named the exclusion; the feature's acceptance did not, and says *every* issue. Both now carry `reported_by:` (your-health `f8a3404`) and both stay `open`.
- **project-os-cockpit ISS-0310 and ISS-0311.** Genuinely fixed, but by other work on 2026-09-19, and their notes still read `updated: 2026-09-16`. The state is right; the date clause is not.

### What the count disagreement was

One reviewer counted 113 where the note says 112, because your-trainer ISS-0487 was filed that morning and fixed the same day. A recount an hour later gives 113 again, now because ISS-0073 was filed here. **112 stands for 2026-09-20**, and the reference note now says why an open-issue count is true only for the instant it carries.

### Fixed after the review

- TASK-0139 was `doing` with four unticked boxes while its body described a finished leg. Both reviewers caught it. It is `done`, its boxes ticked against what the sections already recorded, and the ISS-0164/ISS-0180 gap is stated in the task rather than hidden by a tick.
- The reference note records what a recount moves, and what the 2026-09-18 baseline does under the same treatment (289 from commits, 290 from the working trees).

### Open, and waiting on the owner

- **The `articles` leg is not in the repo's record.** Its check sits on an unmerged branch `iss-check-0919`, while the repo is checked out on `internal-absorption-thesis` with the same edits uncommitted among another session's twelve modified files. `master` is at 2026-08-04 with no issue notes. Three branches give three answers. Landing it needs a decision about another session's in-flight work, so it is in the close-out summary with options rather than done quietly.
- **Two criteria are written wider than the work**: "one list per repo" and "evidence dated on or after 2026-09-18". The work behind both is sound. Whether to amend the criteria or redo four legs is the owner's call.

## Links

- Plan: [[features/backlog-clearance/plan/PLAN|PLAN]]

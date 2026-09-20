---
type: "[[reference]]"
id: REFERENCE-REVIEW-COST-AND-ISSUE-DEBT
aliases: ["Review cost and issue debt 2026-09-18"]
title: "What a review costs and where the open issues come from, measured in project-os-cockpit and your-trainer on 2026-09-18"
status: active
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
scope: "fleet"
source: ["Edwin, 2026-09-18: 'the review step/agent after doing an implementation seems to still take way too much effort (time and tokens) ... the projects is ending up with lots of issues ... most of them not reported by me or written in a way that I can understand ... but they are still reported and not fixed as part of the features they belong to and often they are marked as needing my input.'", "Edwin, 2026-09-18: 'My main concern is with the your-trainer repo'"]
related: ["[[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True]]", "[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
---

# What a review costs and where the open issues come from

## Purpose

This note holds the measurements behind [[PHASE-0007-Reviews-That-Fix-And-A-Backlog-That-Is-True|PHASE-0007]]. The phase's exit criteria are measured against the numbers here, so they are recorded once, with the commands that produced them.

## How it was measured

- **Review cost** comes from the subagent transcripts under `~/.claude/projects/<repo>/*/subagents/`. Each run has a `.meta.json` naming its agent type and a `.jsonl` transcript. For each run we summed assistant turns, tool calls and output tokens, and took wall-clock time from the first and last timestamp. "Context tokens" is the sum of input, cache-read and cache-write tokens over every turn, so it counts the same context again on each turn.
- **Issue origin** comes from each issue's `source:` frontmatter. A source mentioning a review or an audit counts as `review`. One quoting Edwin counts as `edwin`. An empty source counts as `none`. Anything else counts as `agent`, meaning an agent found it while doing other work.
- **Open** means status `triage`, `open`, `active`, `blocked` or `deferred`.

## Review cost

### The round cap worked

Before [[ADR-0028-A-Review-Gate-Runs-Two-Rounds|ADR-0028]] (2026-09-10), one piece of work could be reviewed six or seven times. In project-os-cockpit, PHASE-036 had seven reviewer runs on 2026-08-18, about 2.5 hours in total. PHASE-037 had seven passes on 2026-08-21, and PHASE-039 had six on 2026-08-20. Since 2026-09-13 every gate in both repos has run once, except FEAT-0107 in your-trainer, which ran twice.

### A single review is still large

| Repo | Run | Turns | Tool calls | Minutes |
|---|---|---|---|---|
| cockpit | PHASE-042 | 225 | 125 | 22 |
| cockpit | PHASE-043 | 156 | 90 | 18 |
| cockpit | PHASE-044 | 166 | 98 | 21 |
| your-trainer | FEAT-0107 | 118 | 70 | 11 |
| your-trainer | FEAT-0108 | 174 | 107 | 20 |
| your-trainer | FEAT-0109 | 161 | 97 | 81 |
| your-trainer | FEAT-0111 | 164 | 94 | 24 |
| your-trainer | FEAT-0123 | 162 | 89 | 19 |

A typical review is about 160 turns and 90–100 tool calls, and re-reads 16–37M tokens of context. On 2026-09-17, your-trainer ran five feature reviews and one second round in a single day. Those six runs took about 2.7 hours.

In your-trainer since 2026-08-29, the 13 reviewer runs took 310 minutes in total.

### Where a review's calls go

In the cockpit's PHASE-044 review, the 98 tool calls were 26 `sed` reads, 21 greps, 21 test-suite runs (13 node, 8 pytest) and 10 git commands. The prompt gave the reviewer five tasks and two commits to check, plus five open questions of the "can this ever go wrong" kind. The skill tells the reviewer to report every finding. Nothing tells it when to stop.

### Reviews are not the largest cost in your-trainer

Since 2026-08-29, your-trainer's general-purpose subagents ran 47 times, for 439 minutes in total. Most of those runs rewrote acceptance-check procedures and headings: "A7 split", "Stale rows", "Extend … procedure", "Merges". The 13 reviews took 310 minutes. That other cost is outside PHASE-0007 and is recorded here so it is not mistaken for review cost.

### The rule that caps rounds never reached the cockpit

The cockpit's `tools/instructions/QUALITY.md` is dated 2026-07-21. It has neither the two-round cap nor the rule that only a behavioural finding blocks. Its `independent-review/SKILL.md`, dated 2026-09-10, sends the reader to that file for both. So the cap there holds only because sessions follow the skill text. your-trainer's `QUALITY.md` is dated 2026-09-10 and has the cap.

## Issues

### your-trainer

482 issues in total. **121 are open**: 73 `open`, 42 `triage` and 6 `deferred`.

| Origin | All | Open |
|---|---|---|
| review | 121 | 55 |
| agent | 180 | 34 |
| none | 141 | 22 |
| edwin | 38 | 10 |

- **34 of the open issues come from one code review on 2026-03-01** (ISS-0070 to ISS-0106). Nobody came back to them in six and a half months. Their titles describe real defects: "ImperialSpeedShowsKmhAsMph", "DuplicateStravaUploadsForUploadingStatus", "TimerTaskDataRaceInDeinit", "UserDeleteLeavesOrphanedData".
- **At least one of them looks obsolete.** ISS-0078 says `ActiveWorkoutView` labels a km/h value "mph". On 2026-09-18, no Swift file under `ios/` contains the string `mph`. The backlog can therefore be wrong in both directions: real bugs are sitting in it unfixed, and fixed or removed code is still listed as broken.
- **A review found that FEAT-0107's main behaviour has no test that can fail, and the finding was filed instead of fixed.** The feature's main behaviour is that the app stops sending control writes to a trainer that only reports data. The reviewer deleted all six guards that stop those writes, and all 1322 Android unit tests still passed. That was filed as ISS-0466. Three more findings on the same feature were filed beside it, all against its own code: ISS-0464, ISS-0465 and ISS-0469. ADR-0028 allows this, because a missing test is not a behavioural finding. FEAT-0107 is still `doing`.
- **September alone added 94 issues**: 33 from reviews, 25 found by agents, 36 from Edwin.
- **16 open issues say in the text that they wait on Edwin**, for example "Edwin's call" or "for Edwin".

### project-os-cockpit

313 issues in total. **37 are open**: 15 from reviews, 11 with no source, 6 found by agents, 5 from Edwin.

Several are real bugs in the feature that caused them:

- **ISS-0268**: the release page lists two features waiting to ship while the navigator says "Nothing unshipped". Open since 2026-08-30.
- **ISS-0307**: every verdict written from the app records `user:edwin`, because the value is hard-coded.
- **ISS-0301**: a page shown inside the cockpit can send write requests to the local server. The cheap fix is in the issue and was never done.

Others were never worth an issue. ISS-0308 is about a duplicated line in a history list, and ends with "deciding which is the point of triage". Titles are often hard to read. ISS-0268's title, "The Platform Scoping Stops At The Derived View", is almost word for word the bad example in `WRITING.md`.

### project-os-dev

38 issues are open. Seven of them, ISS-0033 to ISS-0039, are the findings from the eight-round review that ADR-0028 was written about, and all seven are still open.

## What causes it

Four rules send findings into the backlog instead of into the fix:

1. `independent-review/SKILL.md` step 3 tells the reviewer to report every finding.
2. ADR-0028 lets a gate close with every true finding that does not break behaviour filed at `triage`.
3. `LIFECYCLE.md`, "Scope of a change", says a bug the task did not ask for is filed rather than fixed. Agents apply that even to code they wrote in the same session.
4. The FEAT-0051 close-out rule says every validator error is "fixed or filed".

Nothing brings a `triage` issue back for a decision. "Edwin's call" is the easy way for an agent to close without deciding.

## Measured again, 2026-09-20

The cleanup ([[FEAT-0036-The-Backlogs-Are-Cleared-Once|FEAT-0036]]) checked every issue open on 2026-09-18 against the code, then fixed, closed or rewrote it. Counting the same way as above (`triage` or `open`), the seven repos held **290 issues on 2026-09-18 and hold 112 now**, a fall of 61%.

| Repo | 2026-09-18 | 2026-09-20 |
|---|---|---|
| `your-trainer` | 116 | 46 |
| `your-health` | 65 | 22 |
| `project-os-dev` | 37 | 9 |
| `project-os-cockpit` | 35 | 18 |
| `your-sudoku` | 17 | 9 |
| `project-os-deck` | 17 | 6 |
| `articles` | 3 | 2 |
| **Total** | **290** | **112** |

**Where the remaining 112 come from**, by `reported_by:` rather than by parsing `source:` as the 2026-09-18 pass had to: 62 found by an agent doing other work, 31 from a review, 19 from Edwin. Every one of the 112 now carries the field, so this count is read rather than inferred.

The mix has not changed much, and that is the point to watch. The cleanup emptied the backlog once; whether it stays empty depends on [[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It|ADR-0047]] holding at the next five reviews, which [[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]] measures. A backlog that refills with agent-found issues at the old rate would mean the rule change did not take.

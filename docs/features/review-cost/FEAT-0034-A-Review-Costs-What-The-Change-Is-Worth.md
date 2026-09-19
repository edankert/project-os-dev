---
type: "[[feature]]"
id: FEAT-0034
title: "A review costs what the change is worth"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-19
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: 'the review step/agent after doing an implementation seems to still take way too much effort (time and tokens)'", "Edwin, 2026-09-18: 'I think we need to ground / constrain it more because it does still go on for too long and takes too many tokens'"]
goal: "A feature review starts from a generated packet holding the diff, checks a fixed list of claims, runs only targeted tests, and is stopped by a hook at 40 tool calls. A review then costs about 5-7M context tokens instead of 20-32M, and still finds what the current reviews find."
requirements: []
tasks: [TASK-0126, TASK-0127, TASK-0128, TASK-0129, TASK-0130, TASK-0131]
release: ""
acceptance_exception: "A process rule with no product surface. It is checked by TASK-0130's known-answer re-run and by measuring the next five reviews, as PHASE-0007's exit criteria state."
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[ADR-0028-A-Review-Gate-Runs-Two-Rounds]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere]]"]
---

# A review costs what the change is worth

## Goal

A review after implementation takes about 160 turns and 90–100 tool calls. It re-reads 16–37M tokens of context and runs for about 20 minutes. This feature gives the review a defined starting point, a defined job and a hard stop. The target is about 40 tool calls and 5–7M context tokens per review. A re-run of a past review must show that the defect it found is still found.

## Why a review is long today

Measured over the 12 reviews since 2026-09-12, in `your-trainer` and `project-os-cockpit` ([[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT|reference note]]):

- **30–45 calls go on finding out what changed.** The prompt names folders, not the diff. One `your-trainer` prompt says "reconstruct it from the notes rather than from me".
- **40–65 calls go on open-ended code reading,** because the reviewer is told to report every finding and has no point at which it is finished.
- **No review ever made two tool calls in one turn.** Every turn re-reads the whole context, which grows from about 49k to 200–290k tokens as whole files and full test logs are read in. The cost of a review is roughly turns × average context size.
- **A second round is not smaller.** FEAT-0107's round two made 48 calls, 36 of them before its first test run.

The useful work is a small part of this. FEAT-0107's review found its main defect at calls 34–39: it deleted the write guards and all 1322 Android tests still passed. Calls 1–33 were orientation.

## Scope

The seven parts below are the change. Each names the task that builds it.

1. **A packet, not folders** ([[TASK-0126-The-Review-Packet-Script|TASK-0126]]). `tools/scripts/review-packet.sh FEAT-XXXX` writes one file with:
   - the source diff of the feature's commits, with notes left out;
   - the acceptance criteria, word for word;
   - the tests added or changed;
   - the author's last full test run, as the command and its result count.

   The reviewer's first call reads this file. It is the scope.
2. **A list of claims, each given a verdict** ([[TASK-0127-The-Reviewer-Checks-A-List-Of-Claims|TASK-0127]]). Every acceptance criterion, and every "test X guards this", gets one of three verdicts:
   - *holds*;
   - *refuted*, with the command and its output;
   - *not checked*.

   The review is finished when every claim has a verdict. It may add at most five other observations, with no digging. The author may add up to three named claims. Checks the validator and the docs audit already cover (change-note impact lists, parity matrices) are left out. This replaces "report every finding".
3. **Targeted tests only** (TASK-0127). The packet carries the author's full-suite result. The reviewer runs only the tests covering the changed code. It breaks at most three guards and runs targeted tests after each. It never re-runs the full Gradle, xcodebuild or pytest suite.
4. **A hard limit, enforced by a hook** ([[TASK-0128-A-Hook-Stops-The-Reviewer-At-Its-Budget|TASK-0128]]). A `PreToolUse` hook counts tool calls per `agent_id` when `agent_type` is `independent-reviewer`. At call 30 it warns that 10 calls are left. At call 40 it refuses further calls with "budget reached: write your report now; mark unchecked claims *not checked*". `maxTurns: 100` stays in the agent file as a backstop only, because a subagent that hits `maxTurns` stops without writing a report (Claude Code docs, sub-agents page).
5. **Round two is a smaller job** ([[TASK-0129-Round-Two-Verifies-Fixes-Only|TASK-0129]]). Its packet holds only the fix diff and round one's blocking findings. For each finding it answers *fixed* or *not fixed*. It may raise no new findings, and its limit is 15 calls. The round number is recorded in the note, closing [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]].
6. **Keep the context small** (TASK-0127). Read the line ranges around each changed section, not whole files. Keep only the tail of test output. Make independent reads together in one turn. Claude Code does not document a way to force that last one, so it is an instruction, and TASK-0131 measures whether it holds.
6b. **Two reviewers per packet** (Edwin, 2026-09-18, after the comparison in TASK-0130). Two reviewers run at once and the author combines their reports: a refutation with evidence wins. A single run found the hardest known defect about half the time; two catch it about three times in four. A *holds* verdict cites its evidence, one per part of a claim with several parts. The budget warning is at call 36.
7. **Tune the reviewer's settings** (TASK-0127 and [[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]]). The reviewer agent file gets `effort: medium`. Sonnet is tried on the next three small reviews, and kept only if it misses nothing that blocked.

**Also in scope:**
- **One review per feature.** Several small features closing together may share one packet. A phase is never reviewed as a whole again. A test reaching `passing` no longer triggers a review of its own, because the feature review checks its tests.
- **Proving nothing is lost before rollout** ([[TASK-0130-Re-Run-The-FEAT-0107-Review-The-New-Way|TASK-0130]]). A new-style review is run against FEAT-0107's code as it was before the fixes. It must find that deleting the write guards leaves the tests passing (ISS-0466 in `your-trainer`) within its 40 calls. If it does not, the limits are loosened before rollout.

## Out of Scope

- Which findings are fixed or filed. That is [[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed|FEAT-0035]].
- The subagent's fixed context, about 49k tokens of system prompt, tools and project instructions. `omitClaudeMd` could shrink it, but the reviewer needs the project rules, so it is left alone.

## Acceptance

- TASK-0130's re-run finds the FEAT-0107 guard defect within 40 tool calls. Done: every run found it.
- The next five `your-trainer` feature reviews each run two reviewers. Per review, the pair together stays at 12M context tokens or fewer, each reviewer at 40 tool calls or fewer, and wall-clock time at 12 minutes or less. The baseline is one reviewer at about 95 calls, about 20 minutes and 16–32M tokens. Measured on FEAT-0107's known review: 64 calls, 10.1M tokens and 6.2 minutes for the pair.
- None of those five is a phase review, none runs a third round, and every one starts from a packet.
- The procedure, the packet and the budget are stated once, in `independent-review/SKILL.md`. The agent file and the hook link to it. The cockpit and `your-trainer` carry the same text after the sync.

## Links

- Plan: [[features/review-cost/plan/PLAN|PLAN]]

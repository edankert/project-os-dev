---
type: "[[feature]]"
id: FEAT-0034
title: "A review costs what the change is worth"
status: doing
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-20
source: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]", "Edwin, 2026-09-18: 'the review step/agent after doing an implementation seems to still take way too much effort (time and tokens)'", "Edwin, 2026-09-18: 'I think we need to ground / constrain it more because it does still go on for too long and takes too many tokens'"]
goal: "A feature review starts from a generated packet holding the diff, checks a fixed list of claims, runs only targeted tests, and is stopped by a hook at 40 tool calls. A review then costs about 5-7M context tokens instead of 20-32M, and still finds what the current reviews find."
requirements: []
tasks: [TASK-0126, TASK-0127, TASK-0128, TASK-0129, TASK-0130, TASK-0131, TASK-0145]
release: ""
reviewed_by: ["model:claude-opus-5", "model:claude-opus-5"]
review_date: 2026-09-20
review_round: 1
review_verdict: changes-requested
acceptance_exception: "A process rule with no product surface. It is checked by TASK-0130's known-answer re-run, as PHASE-0007's exit criteria state. The plan to also measure the next five reviews was cancelled on 2026-09-20 (TASK-0131)."
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

1. **A packet, not folders** ([[TASK-0126-The-Review-Packet-Script|TASK-0126]]). `tools/scripts/review-packet.py FEAT-XXXX` writes one file with:
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
4. **A hard limit, enforced by a hook** ([[TASK-0128-A-Hook-Stops-The-Reviewer-At-Its-Budget|TASK-0128]]). A `PreToolUse` hook counts tool calls per `agent_id` when `agent_type` is `independent-reviewer`. At call 36 it warns that 4 calls are left (`budget - max(3, budget//10)`; part 6b below says the same). At call 40 it refuses further calls with "budget reached: write your report now; mark unchecked claims *not checked*". `maxTurns: 100` stays in the agent file as a backstop only, because a subagent that hits `maxTurns` stops without writing a report (Claude Code docs, sub-agents page).
5. **Round two is a smaller job** ([[TASK-0129-Round-Two-Verifies-Fixes-Only|TASK-0129]]). Its packet holds only the fix diff and round one's blocking findings. For each finding it answers *fixed* or *not fixed*. It may raise no new findings, and its limit is 15 calls. The round number is recorded in the note, closing [[ISS-0062-A-Reviews-Round-Count-Is-Recorded-Nowhere|ISS-0062]].
6. **Keep the context small** (TASK-0127). Read the line ranges around each changed section, not whole files. Keep only the tail of test output. Make independent reads together in one turn. Claude Code does not document a way to force that last one, so it is an instruction. TASK-0131 was to measure whether it holds; it was cancelled on 2026-09-20, so this part rests on TASK-0130's runs alone.
6b. **Two reviewers per packet** (Edwin, 2026-09-18, after the comparison in TASK-0130). Two reviewers run at once and the author combines their reports: a refutation with evidence wins. A single run found the hardest known defect about half the time; two catch it about three times in four. A *holds* verdict cites its evidence, one per part of a claim with several parts. The budget warning is at call 36.
7. **Tune the reviewer's settings** (TASK-0127). The reviewer agent file gets `effort: medium`. A Sonnet trial was planned here and dropped on 2026-09-19; the reviewer stays on the model the agent file names.

**Also in scope:**
- **One review per feature.** Several small features closing together may share one packet. A phase is never reviewed as a whole again. A test reaching `passing` no longer triggers a review of its own, because the feature review checks its tests.
- **Proving nothing is lost before rollout** ([[TASK-0130-Re-Run-The-FEAT-0107-Review-The-New-Way|TASK-0130]]). A new-style review is run against FEAT-0107's code as it was before the fixes. It must find that deleting the write guards leaves the tests passing (ISS-0466 in `your-trainer`) within its 40 calls. If it does not, the limits are loosened before rollout.

## Out of Scope

- Which findings are fixed or filed. That is [[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed|FEAT-0035]].
- The subagent's fixed context, about 49k tokens of system prompt, tools and project instructions. `omitClaudeMd` could shrink it, but the reviewer needs the project rules, so it is left alone.

## Acceptance

- TASK-0130's re-run finds the FEAT-0107 guard defect within 40 tool calls. Done: every run found it.
- A review runs two reviewers, and the pair stays at 12M context tokens or fewer, each reviewer at 40 tool calls or fewer, and wall-clock time at 12 minutes or less. **Met by TASK-0130**: the pair on FEAT-0107's known review took 64 calls, 10.1M tokens and 6.2 minutes. The baseline is one reviewer at about 95 calls, about 20 minutes and 16–32M tokens. This was to be confirmed over the next five `your-trainer` reviews; that re-test was cancelled on 2026-09-20 as a repeat of a settled measurement ([[TASK-0131-Roll-Out-And-Measure-Five-Reviews|TASK-0131]]).
- A review is never a phase review, never runs a third round, and always starts from a packet. The rules are in `QUALITY.md` and the review skill, and the validator's checks hold them.
- The procedure, the packet and the budget are stated once, in `independent-review/SKILL.md`. The agent file and the hook link to it. The cockpit and `your-trainer` carry the same text after the sync.

## Verification

`python3 tools/scripts/run-tests.py`, 2026-09-20: **passing=17 failing=0 unrunnable=0** over 15 commands. The checks that cover this feature are TST-0013 (the packet: 24 assertions), TST-0014 (the budget hook: 15 assertions since TASK-0145; 13 when this run was recorded) and TST-0015 (the review and issue fields: end to end). `bash tools/scripts/validate-docs.sh` is OK.

The feature's rule text and scripts live in `~/Dev/repos/project-os` and are synced to the fleet; this repo holds the record and runs the template's harnesses against it.

## Review

**Round 1, 2026-09-20. Verdict: `changes-requested`.** Two reviewers, one packet, clean contexts. The first pair's second reviewer could not deliver a report at all, which became the feature's most serious finding; once that was fixed, a replacement reviewer delivered at 24 tool calls and completed the round.

### The reviewer could not hand its report back

Four runs — two fresh agents, then two direct requests for the text alone — each did 30-odd tool calls of real review work and returned nothing. `review-budget.py` denied every call past 40 except a note edit, and a subagent delivers its report with a `SubagentHandback` call. The hook told the reviewer to write its report and refused the only way to deliver it. The last run's transcript holds nine handback attempts against 22 denials; about 120k tokens of finished review was lost per run.

Fixed in [[TASK-0145-The-Budget-Never-Blocks-The-Report|TASK-0145]] before this feature closes, as ADR-0047 requires of a finding in the feature's own code. `test-review-budget.sh` is 15 assertions, and the two new ones fail without the fix.

This is why the review gate is worth its cost. Three tasks, a known-answer replay and a fleet rollout all passed over it, because every review that had ever run stayed under the budget.

### The reviewer that did report

| Claim | Verdict | Evidence |
|---|---|---|
| A review never runs a third round | holds | `validate-docs.py` raises `REVIEW-ROUND`; the "round 3 is refused" case in `test-review-and-issue-fields.sh` passes. |
| A review is never a phase review, and always starts from a packet — "the validator's checks hold them" | **refuted in part** | The validator holds the round count only. Nothing mechanical refuses a phase review or a review with no packet; both rest on prose in `QUALITY.md` and the agent file. The criterion claims more than the code does. |
| The procedure and the packet are stated once in the skill | holds | `QUALITY.md`, `HOOKS.md` and the agent file all point at the skill rather than restating it. |
| **The budget** is stated once | **refuted** | 40 appears at five non-test sites: the skill, `HOOKS.md` twice, `review-packet.py`, the agent file and `generate-adapters.py`. Changing the budget means editing five places. |
| The cockpit and `your-trainer` carry the same text after the sync | holds | `md5` of `independent-review/SKILL.md` is identical across all 13 fleet repos. |
| The packet carries the source diff, criteria word for word, the linked tests and the author's last run | **refuted for a cross-repo feature; holds in-repo** | See "The packet gap" below. |
| The hook counts per `agent_id` and refuses past 40 | holds | `test-review-budget.sh`, including "call 40 is still allowed" and "call 41 is denied". Live state files written by real sessions confirm it is registered and counting. |
| Scope part 4: "at call 30 it warns that 10 calls are left" | **refuted** | It warns at 36. Part 6b of the same section already said 36; part 4 predated the two-reviewer decision. Corrected 2026-09-20. |
| Round two carries only round one's findings and the diff since, at a budget of 15 | holds | The round-two branch of `review-packet.py`, and three assertions over it. |
| TST-0013, TST-0014 and TST-0015 fail when the behaviour they guard is broken | holds | Each inverted in turn; each failed only its own assertions and was restored. |

### The packet gap

For a feature whose notes and code live in different repos, `review-packet.py` produces no diff at all. From this repo its exclude filter strips everything the commits touched; from the template repo it exits 1 with "no note found". One `--repo-root` feeds both the note lookup and the git calls, and no option bridges them.

The reviewer's sharper point is that the author's workaround *was* the defect: the skill says brief the reviewer with the packet "and nothing more" and forbids handing it folders to explore, and the paragraph naming the other repo is what made the review possible at all. `project-os-dev` is by design the notes repo for template code, so every feature here meets this.

Not fixed in this round: a `--code-root` option and a hard error on an empty diff are a change to the packet's contract, which is the owner's call. It is in the close-out summary with a recommendation.

### Fixed after the review

- TASK-0145, above: the budget no longer blocks the report.
- Scope part 1 said `review-packet.sh`; the script is `review-packet.py`.
- Scope part 4's warning point corrected from 30 to 36.
- Scope part 7 and the `acceptance_exception:` still promised the cancelled Sonnet trial and five measured reviews.

### Round one's second reviewer, once it could report

It refuted a claim the first reviewer had marked *holds*, and the refutation stands:

| Claim | Verdict | Evidence |
|---|---|---|
| The cockpit and `your-trainer` carry the same text after the sync | **refuted** | `SKILL.md`, `QUALITY.md`, `HOOKS.md`, `review-packet.py` and the agent file are byte-identical across all 13 repos, but `review-budget.py` is not. Eleven repos have no `SubagentHandback` exemption; only `project-os` and `project-os-dev` do. Re-run independently: 11 STALE, 2 OK. |

The first reviewer had checked this criterion with an `md5` of `SKILL.md` alone, which is the file the sync always carries. The file that actually enforces the budget was never compared. Both readings were honest; the second asked the better question.

**The consequence was live** until the same day: a review in any of those eleven repos that passed 40 calls still lost its report, the failure this feature's own review had just spent four runs and about 480k tokens demonstrating.

**Fixed 2026-09-20.** All thirteen repos now carry the hook, each verified by running `test-review-budget.sh` there (15 assertions, 0 failures, thirteen times) and by re-scanning every copy for the exemption: 13 OK, 0 stale. The commits are listed in [[CHG-20260920-The-Review-Budget-Never-Blocks-The-Report|the change note]]. The reviewer's verdict stands as written; this records what was done about it.

### Also found, to fix before this feature closes

- **A round-one reviewer can be silently demoted to a 15-call budget.** `ROUND_TWO_PACKET` is matched against the whole `tool_input` JSON of every call, so a `Bash` command that merely mentions a path like `review-packet-FEAT-0001-r2.md` flips the hook into round two, and the flip is sticky for the rest of the run. Not fixed in this round; it is a second change to the same hook and is named here so it is not lost.
- The `PostToolUse` warning fires only when `count == warn_at` exactly, so a single failed state write means the reviewer is never warned at all.
- `test-review-budget.sh` prints "(early warning at call N)" without asserting anything, so a hook that warned on every call would still pass.

### Open, and waiting on the owner

- **"The budget is stated once" is false**, and REQ-0027 says a normative rule is stated once. Either the five sites derive from one, or the criterion stops claiming it. The first is right and is more than a round-one fix.
- **The packet gap** above.
- **A check that the fleet's adapter hooks match the template.** The sync is done, but nothing would have caught the drift: the comparison that declared the fleet identical covered `SKILL.md` and missed the file that enforces the budget. Until an adapter-hook check exists, the same gap reopens at the next hook change.

## Links

- Plan: [[features/review-cost/plan/PLAN|PLAN]]

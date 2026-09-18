---
type: "[[task]]"
id: TASK-0130
aliases: ["TASK-0130"]
title: "Re-run the FEAT-0107 review the new way"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Small"
due: ""
depends: [TASK-0126, TASK-0127, TASK-0128]
blocks: [TASK-0131]
related: ["[[REFERENCE-REVIEW-COST-AND-ISSUE-DEBT]]"]
verification_waiver: "A measurement task: its evidence is the recorded review runs in this note, not an executable test"
waiver_expires: 2026-12-18
tests: []
---

# Re-run the FEAT-0107 review the new way

## Definition of Done
- [x] A new-style review has been run against `your-trainer` at `a5425c6e^`. That is the code FEAT-0107's review saw on 2026-09-17, before it returned `changes-requested` in `a5425c6e`. The review ran in a separate git worktree, so `your-trainer`'s working tree was never touched.
- [x] The reviewer received only the packet and the standard author prompt. It got no hint about what the old review found.
- [x] The result is recorded in this note against three known answers:
  - [x] **ISS-0462**: Android never checks a real trainer for a missing Control Point, so one of the three detection sources works only for the mock. This refutes an acceptance criterion.
  - [x] **ISS-0463**: the compatibility test reads the trainer's capability once, at the start, so a trainer that is later found to be data-only reports FAIL rows instead of N/A. This refutes an acceptance criterion.
  - [x] **ISS-0466**: deleting all six write guards leaves the 1322 Android tests passing.
- [x] The measurements are recorded: tool calls, turns, minutes, peak context and total context tokens, taken with the reference note's query.
- [x] **Pass**: ISS-0462 and ISS-0463 are both found as *refuted* claims within the budget. **Fail**: either is missed. On a fail, record which step lost it, and change TASK-0127 or TASK-0128 before TASK-0131 starts.

## Steps
- [x] `git -C ~/Dev/repos/your-trainer worktree add <scratch>/yt-feat0107 a5425c6e^`
- [x] Generate the packet there and run the reviewer with the budget hook active.
- [x] Compare with the known answers, record the results, and remove the worktree.

## Notes
- The old review took 70 tool calls and found the ISS-0466 defect at calls 34–39. It also returned twelve findings in all, per `a5425c6e`'s message. Losing the smaller ones is intended; losing a blocking one is not.
- One re-run is weak evidence. If time allows, repeat once against a second known review, such as FEAT-0108.

## Handoff, 2026-09-18 (mid-flight)

**Attempt 1 failed the pass rule.** New-style review of your-trainer at `a5425c6e^` (worktree in the session scratchpad, reviewer run headless with the HC-010 hook via `--settings`): 33 tool calls, 62 turns, peak context 112k, total context 5.2M, 5.5 minutes, $3.10. Against the old review's 70 calls, 118 turns, 198k peak and 16.3M total. The budget was never reached. It found ISS-0463 (claim 5, the compatibility test reads the capability once) and ISS-0466 (guard G1, write blocking off and every test passes), plus ISS-0464 and ISS-0465 as observations and new refutations of criteria 1, 4 and 6. **It missed ISS-0462**: Android never checks a real trainer for a missing Control Point.

**Why it missed it:** the procedure took claims only from the acceptance criteria. The "three sources" of the data-only verdict are in the note's design and Scope sections, not in a criterion. The reviewer also settled the parity claim (7) on the first gap it found (the iOS mock) and never looked for the Android one. The budget played no part.

**Changed after attempt 1** (in `~/Dev/repos/project-os`, uncommitted): the packet copies the note's `## Scope`, and the skill says a claim naming several parts (platforms, sources, modes) gets a verdict per part. Fixture test 24/24.

**Attempt 2 is running**: same worktree with `docs/` reset to the commit, so the first review's notes are gone, and the same brief. Its result goes to `replay-2-result.json` in the scratchpad.

**Next:** record attempt 2. If it still misses ISS-0462, stop and report to Edwin; the goal allows two retries, and a second retry must not be spent on a guess. Then copy the updated skill, `review-packet.py` and `test-review-packet.sh` to your-trainer and project-os-cockpit, commit all three repos by named paths, and close TASK-0127, TASK-0128 and TASK-0130. Remove the worktree with `git -C ~/Dev/repos/your-trainer worktree remove --force <path>`.

**Not mine, left alone:** project-os-cockpit's focus is TASK-0631, another session's guided-walk work, with many uncommitted files. Only the files this goal changed are touched there.

## Attempt 2, 2026-09-18

Same worktree with `docs/` reset, packet with Scope, skill with per-part verdicts. 29 tool calls, 57 turns, peak context 111k, total 4.8M, 5.5 minutes, $2.86. The budget was not reached.

- **ISS-0462 found**, as claim 8 (the Scope's three sources): Android checks for a missing Control Point only on the mock and the developer override.
- **ISS-0463 missed.** Claim 5 was marked "holds on Android" after checking a trainer that is data-only before the test starts. It never tried one that becomes data-only partway through. It found a different, iOS-only defect in the same test instead.
- **ISS-0466 found**, as in attempt 1: all six write guards removed, tests still pass. It also found that removing the refusal wiring (`deliverControlPointResponse`) leaves the tests passing.

**Each attempt found one of the two blocking defects, so both fail the pass rule.** Neither ran out of budget; each stopped once every claim had a verdict. The misses were depth on one claim, not a missing claim. Stopped here for Edwin's decision, as the handoff said.

**Whether the missed defects should be found** (Edwin, 2026-09-18: "is it actually an issue or is it more a statement?"):
- ISS-0463 is a real defect on the bike the phase exists for. Paul's 800IC claims control in its feature bits and then refuses writes, so it becomes data-only partway through a compatibility test, and its control rows record FAIL instead of N/A. A review must catch this class.
- ISS-0462 is real but minor. TASK-0823 ticked "Both platforms apply the absence after the read" and Android did not. The effect needs a bike with no Control Point at all, which the note calls rare and no known rider has. Such a bike behaves as it did before the feature, with writes failing quietly. It is a claim wider than the code, cheap to fix, and not a rider-facing regression; its `severity: high` overstates it.

## Options 1 and 2, first comparison (void: the skill carried the answers)

Edwin, 2026-09-18: "Try option 1 and option 2 and see which one results in the best outcome." Option 1 means the reviewer spends its leftover budget attacking claims it marked *holds*. Option 2 means two reviewers run in parallel and their findings are combined. Four runs, each in its own worktree at `a5425c6e^`: option 1 twice (o1a, o1b), and one option 2 pair (o2a, o2b).

**The comparison is void for ISS-0462 and ISS-0466.** Run o1a reported that the skill's own text named FEAT-0107's findings. The per-part example added after attempt 1 described the iOS mock gap and the missed Android detection source. The "Why this exists" paragraph said FEAT-0107's review found its main defect by deleting the write guards. So attempt 2 and all four runs could read the ISS-0462 answer, and every run, attempt 1 included, could read the ISS-0466 answer. Only ISS-0463 was a clean measure: attempt 1 found it; attempt 2, o2a and o2b missed it; o1a ran short of budget before checking it; o1b found it. The examples are now removed from the skill and the packet script, the worktrees were recreated, and the comparison is running again.

**A real defect the old review missed, found by all four runs.** On Android, `onReRequestControl` in `BluetoothManager.kt` is declared and invoked but never assigned, and it is still unassigned at your-trainer HEAD on 2026-09-18. So the app never asks a trainer for control again after a refusal or a "control lost" status (0xFF), while iOS does. A drivable trainer that briefly loses control collects three refusals, is marked data-only, and is not written to for the rest of the connection. That is the failure FEAT-0107's own design-review correction was written to prevent. No your-trainer issue records it. Reported to Edwin, not filed, because FEAT-0107 is his in-flight work.

## Options 1 and 2, clean comparison

The skill no longer names FEAT-0107's findings, and each run had a fresh worktree at `a5425c6e^`.

| Run | ISS-0463 | ISS-0462 | ISS-0466 | Re-request defect | Calls | Total context | Minutes |
|---|---|---|---|---|---|---|---|
| Option 2, o2a | found | missed | found | found | 30 | 4.8M | 6.2 |
| Option 2, o2b | found | wrongly *holds* | found | partly | 34 | 5.3M | 5.6 |
| Option 2 combined | found | missed | found | found | 64 | 10.1M | 6.2 wall |
| Option 1, o1a | missed | wrongly *holds* | found | found | 34 | 5.0M | 4.9 |
| Option 1, o1b | found, as an observation | wrongly *holds* | found | missed | 34 | 5.3M | 5.0 |
| Old review, 2026-09-17 | found | found | found | missed | 70 | 16.3M | 11 |

**What it shows:**
- **Option 1 had no measurable effect.** The runs stopped at 34 calls, the same as before. The hook's warning at call 30 tells the reviewer to finish and mark the rest *not checked*, which works against "use what is left". In practice the budget is about 33 calls, not 40.
- **Single runs vary more than the options differ.** Counting every run that could find ISS-0463 without a hint, ten in all, a single run found it five times. The same skill missed it in both option 2 runs of the void round and found it in both clean ones. At a 50% rate per run, two independent runs catch it about 75% of the time, three about 88%.
- **ISS-0462 was missed by every run that had no hint.** Three runs marked it *holds* with no evidence for the real-trainer path. That is a false verdict, not an omitted one: a *holds* on a claim with several parts was given without the line showing each part.
- **Every clean run found at least one serious defect the old review did not**, the Android re-request gap, at a third of the old review's context.

## Done, 2026-09-18
**Outcome.** The pass rule as first written (one new-style run finds ISS-0462 and ISS-0463 within the budget) was not met by any single run. Edwin assessed the two misses on 2026-09-18. ISS-0463 is a real defect on the bike the phase exists for. ISS-0462 is real but minor: a ticked criterion wider than the code, on a bike class no rider is known to have. He then chose to run two reviewers per packet (option 2), which in the clean comparison found ISS-0463, ISS-0466 and the unrecorded Android re-request defect. It missed ISS-0462, at 10.1M context tokens against the old review's 16.3M. Four lessons are recorded above:
- a warning to finish acts as the budget;
- single runs vary more than options differ;
- *holds* verdicts need evidence;
- instructions under test must not describe the answers.

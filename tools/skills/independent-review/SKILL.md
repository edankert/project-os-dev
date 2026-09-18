---
type: skill
id: SKILL-INDEPENDENT-REVIEW
status: active
owner: group:maintainers
created: 2026-07-05
updated: 2026-09-18
tags: [skills, review, verification]
---

# Skill: Independent review

## Why this exists
A session reviewing its own output shares its commitments: it watched the work being rationalised and inherits the conclusion. **Fresh context is the active ingredient** — a reviewer that never saw the author's reasoning approaches the artifact as a stranger (ADR-0013).

Two kinds of correlation were being conflated. Shared **weights** correlate capability. Shared **context** correlates commitment. This fleet's misses have consistently been the second kind: claims written wider than the code, surviving because everyone arrived already holding the claim.

**A review is also bounded** (ADR-0047). Measured on 2026-09-18, a review with no scope, no procedure and no stopping point ran 90–125 tool calls and about 20 minutes, and spent its first 30–45 calls finding out what had changed. The useful work was a few calls: breaking a guard and running the tests, or checking one claim against one file. So a review starts from a packet, checks a list of claims, and stops at a budget.

## When to use
- At the review gates stated once in `../../instructions/QUALITY.md`, "Independent review (clean-context)": one review per feature reaching `done`, covering its linked tests and requirements. A change note owes no review (ADR-0019).
- Optionally, when a `verification_waiver` is being recorded.

## Independence rules
1. What makes a review independent is stated once in `../../instructions/QUALITY.md`. `reviewed_by` records the model as provenance, not as a compliance token.
2. **Never write the verdict before the reviewer returns it.** `review_verdict` is transcribed from what the review returned. If a close-out needs the field before the review lands, leave it empty.
3. The reviewer gets the packet and the notes, never the author's reasoning. If the change cannot be justified from them, that is a finding about the documentation.
4. The reviewer's job is to **refute**: look for the input or state where a claim is false, and for a test that would still pass if the change were broken.

## The author: start a review

1. **Record the full test run** in the feature note's `## Verification` section: the command, the date and the result count. The reviewer does not re-run the full suite.
2. **Write the packet**:
   ```
   python3 tools/scripts/review-packet.py FEAT-0001 [--claim "…"]…
   ```
   It prints the packet's path. The packet holds the acceptance criteria word for word, the linked tests, the commits whose subject names the feature or its tasks, the source diff with notes and generated files left out, and the full-run result. A diff over 400 lines goes in a companion `.diff` file with an index. Use `--range A..B` when commit subjects do not name the work. A warning over 1,500 lines means: split the review, or accept its size knowingly.
3. **Brief the reviewer with this and nothing more:**
   > Independent review of FEAT-0001, round 1. Your first call reads the packet at `<path>`. Follow `tools/skills/independent-review/SKILL.md`, "The reviewer".

   You may add up to three claims with `--claim`: a behaviour the criteria do not state but the change relies on. Do not add open questions, extra areas to explore, or checks the validator or the docs audit already cover (change-note impact lists, parity matrices, snapshot agreement).
4. **Launch two reviewers at once, on the same packet, each in a clean context** that is not the authoring session: two `independent-reviewer` subagents started in the same turn, two separate Codex or Cursor sessions, or a person (one person is enough on their own). Measured on a known review (project-os-dev TASK-0130), a single run found the hardest defect about half the time; two runs catch it about three times in four, and together they cost less than one unbounded review did. Round two uses one reviewer.

## The reviewer

**Your budget is 40 tool calls in round one and 15 in round two.** In Claude Code a hook enforces it (`../../instructions/HOOKS.md`, HC-010): at call 36 you are told how many are left, and past the budget every call except a note edit is refused. Plan for the budget; do not rely on the refusal. Another reviewer may be working on the same packet at the same time; work on your own and do not look for its notes.

1. **Read the packet.** It is your scope. Read code outside it only when a line in its diff leads there.
2. **List the claims.** Each acceptance criterion, each behaviour the note's Scope says is delivered that no criterion covers, each linked test ("this test fails when the behaviour it guards is broken"), and each author claim. **A claim that names several parts gets a verdict per part**: both platforms, each of three sources, every mode. One gap does not settle the others: a gap found on one platform says nothing about the other, so check each part before moving on.
3. **Break what the feature depends on most.** Pick at most three guards: the lines that, if removed, would let the main behaviour silently fail. Remove each, run the targeted tests, record whether any test failed, and restore it. A guard whose removal leaves the tests passing refutes that test's claim.
4. **Check the remaining claims against the diff.** Give each one *holds*, *refuted* (with the command you ran and what it printed) or *not checked*. **A *holds* cites its evidence too**: the line or the command output that shows it. For a claim with several parts, cite one for each part; a part you did not look at makes the claim *not checked* for that part, never *holds*.
5. **Stop when every claim has a verdict.** Add at most five other observations you noticed on the way, one line each, without investigating them further.

**Keep the context small**, because every turn re-reads all of it:
- Run only the tests that cover the changed code, never the full suite; the packet already carries its result.
- Read the line ranges around each change (`sed -n 'a,bp'`, the packet's index), not whole files.
- Keep only the tail of test output (`| tail -20`).
- Make independent reads in the same turn.

**Report** in this shape, in your final message:

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | <criterion, word for word> | holds / refuted / not checked | <command and output, or the line> |

Then the other observations, then one line on what was independent (fresh context, separate session) and what was not (the model). **Write nothing in the notes and file no issues.** The author combines both reviewers' reports into the note (see "After the review").

## Round two

If round one requested changes, the author fixes them and writes a round-two packet:
```
python3 tools/scripts/review-packet.py FEAT-0001 --round 2 --since <commit round one reviewed>
```
It holds only round one's `## Review` section and the source diff since that commit. The reviewer answers *fixed* or *not fixed* for each refuted claim, with the command that shows it, and raises no new findings. Its budget is 15 calls. **There is no round three:** a disagreement that survives round two is adjudicated, as `../../instructions/QUALITY.md` states.

## After the review: fix, then file what is left
1. **Combine the two reports, then transcribe; never anticipate a verdict.** A claim either reviewer marked *refuted* with evidence is *refuted*. A claim one marked *holds* and the other *not checked* is *holds*. Where they disagree, *holds* against *refuted*, the refutation's command decides: run it. Write one combined `## Review` section, and record `changes-requested` if any claim is *refuted*. List both reviewers in `reviewed_by`.
2. **Fix every finding about code the feature changed before the feature closes**, whether or not it refuted a claim (`../../instructions/QUALITY.md`, "A finding is fixed in the feature that caused it"). A refuted claim also sends the fixes to round two.
3. **File only what the filing bar admits** (`../../instructions/QUALITY.md`, "The filing bar"): the fix needs the owner's decision, the defect lies in code the feature did not change, or the fix is too large for the session. Everything else stays in the note's `## Review` section. An issue opens with what a user would notice (`../issue-intake/SKILL.md`).
4. **Ask the owner, don't file for them.** A question goes in the close-out summary with a recommendation. If a sensible default exists, take it and say so.
5. If `approved`: continue with `../close-out/SKILL.md`.

## What NOT to do
- Do not have the authoring session re-read its own diff: that is self-review.
- Do not skip the review because tests pass; the review exists because author-written tests share the author's blind spots.
- Do not brief the reviewer with folders to explore, a request to "report every finding", or questions beyond three claims. That is what made reviews take 90–125 calls.
- Do not re-run the full suite in the review, and do not review a whole phase.
- Do not run a third round, and do not let the author answer the reviewer in turns.

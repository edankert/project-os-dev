---
type: "[[task]]"
id: TASK-0058
aliases: ["TASK-0058"]
title: "Replace every state-rule restatement with a link across instructions and skills; fixes ISS-0006"
status: done
phase: "[[PHASE-0002-State-Model-Simplification]]"
owner: user:edwin
created: 2026-07-25
updated: 2026-07-25
source: []
parent: "[[FEAT-0014-Single-State-Contract]]"
effort: M
due: ""
depends: [TASK-0057]
blocks: [TASK-0059]
related: [ISS-0006, REQ-0018]
tests: []
---

# Strip the restatements

## Definition of Done

- [ ] `QUALITY.md`, `LIFECYCLE.md`, `STATUSES.md`, `close-out/SKILL.md`, `status-transition/SKILL.md`, `snapshot-sync/SKILL.md` link to the contract instead of restating it.
- [ ] Requirement advancement appears in one file (was four).
- [ ] The deferral procedure appears in one file (was two, near-verbatim).
- [ ] Verification gating appears in one file (was four).
- [ ] [[ISS-0006-Status-Transition-Test-Gates-Requirements|ISS-0006]] is resolved by deletion of the offending sentence.
- [ ] A grep audit is recorded in this note showing zero remaining restatements, with the search terms used.

## Steps

- [ ] Audit: locate every passage that states a status value, a gate, or a transition rule.
- [ ] For each, decide **link** or **delete** — no third option; "shorten it" recreates the problem in miniature.
- [ ] Verify the skills still read as procedures: a skill should say *what to do*, and link for *what is allowed*.
- [ ] Record the grep audit in this note as the completion evidence.

## Notes

**Fix ISS-0006 immediately, separately from this task.** The one-line correction to `status-transition/SKILL.md` is near-zero risk and stops ten repos acting on a reverted rule in the meantime. This task then deletes the sentence entirely. Waiting for the deletion in order to make one fix is a false economy.

**The measure of success is deletion, not tidiness.** 604 lines across eight files describe state; the count should drop materially. If it does not, the restatements were reworded rather than removed and the next amendment will miss one again — which is exactly how ISS-0006 happened, with four files corrected and a fifth left behind.

**Second bug in the same sentence:** `status-transition` also gates `phase` to `done` on linked tests, which no validator check implements. It goes with the rest.

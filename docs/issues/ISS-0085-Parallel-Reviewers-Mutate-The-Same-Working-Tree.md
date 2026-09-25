---
type: "[[issue]]"
id: ISS-0085
aliases: ["ISS-0085"]
title: "Two reviewers breaking guards in the same working tree can corrupt each other's test runs, and a scratch copy can write into the real repo"
status: open
phase: "[[PHASE-999]]"
owner: unassigned
created: 2026-09-24
updated: 2026-09-24
source: ["FEAT-0033 independent review, round 1, 2026-09-24: both reviewers reported it"]
reported_by: review
question: ""
severity: medium
component: "tools/skills/independent-review/SKILL.md"
parent: ""
related: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]", "[[TASK-0130]]"]
tests: []
---

# Two reviewers breaking guards in the same working tree can corrupt each other's test runs, and a scratch copy can write into the real repo

## Problem

The review skill tells each of two parallel reviewers to "break what the feature depends on most": remove a guard, run the tests, restore it. Both reviewers do this in the same working tree. While one has a guard removed, the other's test run sees the broken code and can report a false failure, or a false pass. On FEAT-0033 on 2026-09-24, reviewer B saw `if preparation:` replaced by `if False:` in the template's `walk-sheet.py`, a mutation it had not made.

A reviewer that makes its own scratch copy can also write into the real repo without knowing. Reviewer A's copy of your-trainer held `docs` and `SNAPSHOT.yaml` as symlinks into the real repo. Its test edit to `TST-0019-First-Run.md` probably landed there. The file was clean when checked afterwards, and your-trainer's `git status` shows nothing else.

## Expected

Each reviewer breaks guards only in a copy of its own: a `git worktree` or a real, non-symlinked copy. The skill says so, and says to check that the copy is not linked back into the repo.

## Evidence

- Both round-one reports on FEAT-0033, recorded in its `## Review` section.
- `shasum` of every copy of `walk-sheet.py` after both reviews: all identical to the version under review, so no mutation was left behind.

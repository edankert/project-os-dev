---
type: "[[issue]]"
id: ISS-0067
title: "Git's rename detection can pair a deleted change note with a new one, so the new one never reaches the survey"
status: triage
phase: "[[PHASE-999-Parking-Lot]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["Independent review of PHASE-0005, 2026-09-14 (model:claude-opus-5)"]
severity: low
component: tooling
parent: ""
related: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]", "[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]"]
tests: []
---

# A deleted change note can hide a new one from the survey

## Problem

`walk-sheet.py` finds new change notes with `git diff --diff-filter=A --name-only <tag>..HEAD -- docs/changes`. Git pairs a deleted file with an added one when they are similar enough — the default is 50% — and a pair is a rename, not an addition. So deleting one change note in the same range as adding another can make the new note invisible to the survey, silently.

> [!quote] As reported — 2026-09-14 (model:claude-opus-5, independent review of PHASE-0005)
> **Git's default rename detection can suppress a genuinely new change note.** Deleting a pre-tag note while adding a post-tag one pairs them at 65% similarity, `--diff-filter=A` returns nothing, and the survey prints "No change note names a screen". Requires deleting a change note, which LIFECYCLE forbids.

## Repro

In a fixture repo with a tag, delete a change note that existed at the tag and add a new one with similar frontmatter and Impact shape, then generate a sheet. The new note's screens do not appear and nothing says why.

## Expected

A change note added since the tag is surveyed, whatever else the range contains.

## Actual

It is surveyed unless git decided it is a rename of something deleted.

## Why it is `low`

**It needs somebody to delete a change note**, and `tools/instructions/LIFECYCLE.md` close-out step 5 says a completed note is never deleted — status and links preserve history. So this is reachable only by breaking a rule that exists for other reasons. It is filed rather than fixed because the fix is one flag (`--no-renames`) and the question of whether a *renamed* change note should count as new deserves a sentence in rule 2 either way.

## Next Actions

- [ ] Decide whether a renamed change note is new for survey purposes, then either pass `--no-renames` or say in rule 2 that a rename is not an addition.

---
type: "[[task]]"
id: TASK-0197
aliases: ["TASK-0197"]
title: "A defect an agent finds itself, with a known cause, is fixed in the same session, even outside the work in hand"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["Edwin, 2026-10-14, in project-os-cockpit: 'fix ISS-0320 ... in general why do I need to direct you to fix this, you found this, you prioritized this, you should fix this.'", "Edwin, 2026-10-14: 'Make sure this standing rule is defined in project-os and downstreamed to the enabled projects.'", "Edwin, 2026-10-14: 'Make sure the rule is complete enough and clear enough'", "Edwin, 2026-10-14: 'Can you review the need to create an issue in the first place if it is found and fixed in the same session', then 'yes, commit and sync it'"]
parent: "[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]"
effort: "Small"
due: ""
depends: []
blocks: []
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[TASK-0144-A-Failing-Test-Is-Fixed-Whoever-Broke-It]]"]
verification_waiver: "A rule change; its evidence is the template text and the fleet sync recorded below"
waiver_expires: 2027-01-14
tests: []
---

# A defect you find is one you fix

## What happened

In project-os-cockpit on 2026-10-14, an agent ran an acceptance check of its own feature and found that a `cockpit dispatch` prompt said "Read docs/ first" instead of naming the note's file. It found the cause in a few minutes. The fix was a few lines. It filed ISS-0320 and listed it as "still open" in its summary, because the filing bar lets a defect "in code the feature did not change" become an issue. Edwin then had to say "fix ISS-0320", and asked why he needed to.

## Why the rules produced this

Two rules point the same way:

- `QUALITY.md`, "The filing bar": a finding becomes an `ISS-*` when "the defect is in code the feature did not change".
- `LIFECYCLE.md`, "Scope of a change": "A bug, cleanup or missing abstraction elsewhere is an `ISS-*` or a follow-up in your summary".

Both were written to keep a feature's diff to its own scope (ADR-0047). Neither says the defect should then stay unfixed, but nothing says it should be fixed either, so filing became the end of it. The cost lands on the owner, who has to triage defects the agent already understood.

## The rule

Stated once in `QUALITY.md`, beside the failing-test rule it extends:

- A defect you find yourself, and whose cause you know, is fixed in the same session. You may have found it in a test run, a review, a validator run, or while reading code.
- That holds when the defect is in code the work in hand did not change, when it predates the work, and when someone else wrote it.
- The fix keeps its own scope: a task under the feature that owns the code, written first, and its own commit, apart from the work in hand. A fix that changes behaviour gets its change note.
- It gets no `ISS-*`. The task records the symptom, the cause and the fix; an issue beside it would say the same thing twice. When an `ISS-*` already exists because someone reported the defect, the fix closes it.
- It stays open only for one of four named reasons, and then it gets an `ISS-*` that names the reason, as the summary does: an owner decision, too large or wide for the session, another repository, or a cause still unknown after looking.
- Listing it as open for the owner to direct is not one of the reasons.

Pointers, not restatements, in `LIFECYCLE.md` "Scope of a change", `issue-intake/SKILL.md` and `close-out/SKILL.md`. The filing bar loses "code the feature did not change" as a reason to leave a defect open; such a defect is fixed under a task, with no issue.

Edwin, 2026-10-14, asked whether an issue is needed at all for a defect found and fixed in the same session. It is not, and the rule says so. The cost: a defect that shipped in an earlier release and is fixed this way appears in the next release under its change note, not in its "Issues Fixed" list.

What the rule does not cover: a cleanup or a missing abstraction is not a defect, and still becomes an `ISS-*` or a follow-up.

## Definition of Done

- [x] ADR-0047 records the amendment, as it records TASK-0144's.
- [x] project-os `QUALITY.md`, `LIFECYCLE.md`, `issue-intake/SKILL.md` and `close-out/SKILL.md` carry the rule; project-os's validator passes.
- [x] Every enabled repo (a `.project-os-sync` under `~/Dev/repos/`) is synced to the new template commit and commits only the synced paths; a repo whose `SNAPSHOT.yaml` holds someone else's uncommitted work commits from a separate worktree.
- [x] `validate-fleet.sh` shows no new errors.

## Record, 2026-10-14

- project-os `30e2486` carries the rule in `QUALITY.md`, with pointers from `LIFECYCLE.md`, `close-out/SKILL.md` and `issue-intake/SKILL.md`, and the four regenerated adapter files. Its validator passes, and `generate-adapters.py --check` reports all 67 artifacts current.
- All twelve enabled repos are synced to `30e2486`. Each sync commit holds the same nine files and nothing else: articles `5ed62ab` (on its `internal-absorption-thesis` branch, where its earlier syncs are), edankert.com `4931859`, obsidian-supernote-sync `2c5c600`, project-os-bench `1ebc760`, project-os-cockpit `fa71690`, project-os-deck `59035bc`, project-os-dev `6760eec`, your-applications.com `f18bcf2`, your-health `76badb6`, your-sudoku `b3259eb`, your-trainer `c38475f8`, yourtrainer-mcp `2d46288`.
- articles, project-os-deck, project-os-dev, your-applications.com, your-health and your-sudoku held uncommitted `SNAPSHOT.yaml` changes, so each synced in a separate worktree and fast-forwarded its branch. Their working changes are untouched.
- Nothing is pushed.

---
type: "[[issue]]"
aliases: ["ISS-0082"]
id: ISS-0082
title: "Every gate is a rule telling the agent not to write a field it can write, so the one structural protection project-os uses for statuses is never used for verdicts"
status: deferred
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-09-22
updated: 2026-09-22
source: ["[[Comparable-Systems-Spec-Kit-2026-09-22]] — Spec Kit's reviewer-owned checklists, read 2026-09-22"]
reported_by: agent
question: "Should some fields be reviewer-owned in a way the validator can enforce, rather than by instruction? Options: (a) declare a set of reviewer-owned fields and have the validator refuse a commit where the author changed one; (b) move them out of the authored note into a separate artifact the author does not write, as the release ledger already does for acceptance verdicts; (c) decline, since two reviewers and a transcription rule have not visibly failed yet. Recommendation: (b), because the ledger precedent exists and (a) needs a notion of who committed that the validator does not have."
severity: medium
component: lifecycle-rules
parent: ""
related: ["[[Comparable-Systems-Spec-Kit-2026-09-22]]", "[[ADR-0009-Snapshot-Is-Generated]]", "[[ADR-0010-Test-Status-Stamped-By-Execution]]", "[[ADR-0013-Independence-Is-Clean-Context]]", "[[ISS-0017-Review-Verdicts-Never-Expire]]"]
tests: []
---

# Every gate is a rule telling the agent not to write a field it can write

## Problem

[[ADR-0009-Snapshot-Is-Generated]] makes the argument this repo runs on: the way to stop a field being wrong is to make writing it wrong structurally impossible, not to tell the agent to be careful. Snapshot statuses are derived by a script. Test verdicts are stamped by execution.

Review verdicts are not. `tools/skills/independent-review/SKILL.md` line 26 says "Never write the verdict before the reviewer returns it", and line 77 says "Combine the two reports, then transcribe; never anticipate a verdict". Both are instructions to the author, in a file the author is asked to read, about a field the author writes. An agent that skips those two lines produces a note that passes the validator and looks exactly like a reviewed one.

## Expected

A field that records someone else's judgement is not writable by the party the judgement is about.

## Actual

`review_verdict` and `reviewed_by` are ordinary frontmatter on the feature note. The author writes them. The protection is two sentences of prose and the honesty of the transcription, plus [[ADR-0028-A-Review-Gate-Runs-Two-Rounds]] requiring two reviewers, which raises the cost of a fabricated verdict without making it impossible.

The repo already has the better pattern in one place: acceptance verdicts live in the release ledger rather than on the test note, so the note cannot assert them.

## Evidence

Spec Kit's `templates/checklist-template.md` states the ownership rule on the artifact itself:

> **Review Ownership**: This checklist is a reviewer-owned requirements-quality review artifact. Mark an item `[x]` only when the reviewer determines the requirements-quality criterion is satisfied.
> **Marker Semantics**: `[x]` means the criterion has been reviewed and satisfied for requirements quality. It does not mean implementation work is complete.

and in its notes: "`__SPECKIT_COMMAND_IMPLEMENT__` reads checklist checkbox state as a gate and must not modify markers".

Their enforcement is no better than ours — it is also prose, read by the same model. What is better is the framing: a whole artifact class with one writer and a different reader, rather than a field on a note everyone edits. That framing is what makes a structural fix possible later.

## Next Actions

- [ ] Decide (see `question:` in the frontmatter).
- [ ] Inventory which fields are somebody else's judgement written by the author. `review_verdict` and `reviewed_by` are the obvious pair; the requirement approval in [[ISS-0077-Who-Approves-Requirements]] is a third, and that issue is really the same defect seen from a different file.
- [ ] Check the overlap with [[ISS-0017-Review-Verdicts-Never-Expire]]. A verdict that cannot be self-written and a verdict that expires when the code changes are two halves of making the field mean something.
- [x] Triaged by Edwin on 2026-09-22 and parked in [[PHASE-999-Parking-Lot|PHASE-999]]. Deferred means still wanted: the `question:` above is the decision re-adoption has to make, not one that is waiting on anyone now.

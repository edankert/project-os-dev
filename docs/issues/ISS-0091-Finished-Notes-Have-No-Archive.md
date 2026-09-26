---
type: "[[issue]]"
id: ISS-0091
aliases: ["ISS-0091"]
title: "Finished tasks, issues and change notes stay among the live notes, so every search and validator run wades through them"
status: "open"
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: "2026-09-26"
source: ["your-trainer session your-trainer-b8, on Edwin's instruction (2026-09-26: 'review where most of the time went', then 'Make it so')"]
reported_by: review
question: "How should finished notes be archived? Edwin's proposal: archive finished tasks and one-off issues, and keep the lasting record in phases, features, ADRs and requirements. The your-trainer session's recommendation, not yet answered: archive finished tasks, finished issues, merged change notes and retired checks once the release that shipped them is out; move lasting facts into the feature or an ADR at close-out; move notes to docs/archive/ under the same sub-path, never delete; add a .ignore so search skips it; validate only that links into it resolve. Also: a validator option that prints only warnings for files changed since HEAD."
severity: medium
component: "tools/instructions/LIFECYCLE.md; tools/instructions/SNAPSHOT.md; tools/scripts/validate-docs.py"
parent: ""
related: ["[[ISS-0030-Retention-Is-Policy-Nothing-Performs]]"]
tests: []
---

# Finished tasks, issues and change notes stay among the live notes, so every search and validator run wades through them

## Problem

LIFECYCLE says "the notes are the archive" and "Never delete a completed note", so every finished note stays beside the live ones for good. Searches and validator runs pay for that on every use.

## Evidence

- your-trainer has 3,149 notes. 832 of its 974 tasks and 436 of its 515 issues are finished, and it has 359 change notes.
- A search for one rule returned 57 notes, 27 of them finished tasks, issues and change notes. Each still had to be opened and judged as history.
- The validator prints about 1,100 warnings per run, mostly about old notes.

## Proposal (from the report), not yet answered by Edwin

- Archive finished tasks, finished issues, merged change notes and retired checks. Keep features, phases, ADRs, requirements, risks, releases and active checks where they are.
- Archive only once the release that shipped the item is out, not when its status goes terminal. In the session, an issue and a task closed the day before were both needed, and both were changed.
- At feature close-out, move the lasting facts up: what shipped, and why the non-obvious choices were made, into the feature note or an ADR. In the session, the reason Android checked Strava on app return lived only in a task and an issue.
- Mechanics: move the note to `docs/archive/` under the same sub-path, never delete it; drop it from the snapshot; add a repo `.ignore` so ripgrep and agent search skip the archive by default; the validator checks only that links into the archive resolve and never warns about archived notes; Obsidian name links keep working.
- A smaller step inside the same issue: a validator option that prints only the warnings about files changed since HEAD.

## Relation to ISS-0030

ISS-0030 is about pruning the snapshot. This is about the notes themselves, which the snapshot's retention rule assumes stay put.

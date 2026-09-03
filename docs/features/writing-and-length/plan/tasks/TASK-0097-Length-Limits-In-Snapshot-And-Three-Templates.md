---
type: "[[task]]"
id: TASK-0097
aliases: ["TASK-0097"]
title: "Length limits in SNAPSHOT.md and three templates"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 5.2"]
parent: "[[FEAT-0025-Writing-Rules-For-The-Final-Message-And-Length-Limits]]"
effort: S
depends: []
related: ["[[ADR-0018-What-The-Generator-Owns]]"]
tests: []
---

# Length limits in SNAPSHOT.md and three templates

## Definition of Done
- [x] `SNAPSHOT.md` says a `title` is at most twelve words.
- [x] It says `goal:` and `note:` are at most two sentences each, and that anything longer belongs in the note body.
- [x] It names the destination: the feature or task note's own sections, which is where a reader looking for the detail already goes.
- [x] `change.md`, `issue.md` (Problem) and `feature.md` (Goal) each ask for a summary of two or three sentences, point first.

## Steps
- [x] Write the numbers into `SNAPSHOT.md:63,68-69`.
- [x] Add the one-line instruction to the three templates.

## Notes

`title` is derived from the note by the sync script ([[ADR-0018-What-The-Generator-Owns]]), so a limit written in SNAPSHOT.md is really a limit on note titles. Say that in the text, or the rule looks unenforceable to a reader who knows the field is generated.

Measured on 2026-09-03: the template's `focus.note` is 266 words, this repo's 136, and FEAT-0021's title is 30 words.

Landed as template commit `e4d0688` on 2026-09-03. SNAPSHOT.md says the title limit is a limit on note titles because the sync script derives the field (ADR-0018), as the Notes above asked. `focus.note` is documented for the first time, with the same two-sentence limit; it was in the template snapshot and in every repo's, and in no instruction.

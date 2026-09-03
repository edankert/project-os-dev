---
type: "[[feature]]"
id: FEAT-0025
aliases: ["FEAT-0025"]
title: "Writing rules for the final message, and length limits on notes"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 4.2, 5.1, 5.2"]
goal: "Finish WRITING.md with the four rules the guides state and it does not, including the ban on mannered prose the corpus is currently teaching. Give titles and snapshot fields a stated length, since the snapshot is what every session loads first."
requirements: []
tasks: ["[[TASK-0096]]", "[[TASK-0097]]"]
release: ""
related: ["[[ADR-0018-What-The-Generator-Owns]]", "[[ISS-0030-Retention-Is-Policy-Nothing-Performs]]"]
tests: []
acceptance_exception: "The deliverable is how prose reads, and no command distinguishes a rule that is stated from a rule that is followed. A grep would confirm that WRITING.md contains five new rules, which is not the claim. The discharge is the independent-review pass on the first change note and task notes written after the rules land, reading them against the rules — the walk an acceptance check would ask a person to perform, already owed on those notes by QUALITY.md."
---

# Writing rules for the final message, and length limits on notes

## Goal

WRITING.md answers the 2026-08-31 feedback well for note prose, and stops there. It says nothing about the message a user reads after a long run, and the instruction corpus the model reads before writing is full of the mannered phrasing the guide warns about — "the load-bearing sentence", "a badge that never empties", "a one-way door", "two sentences wearing one hat", the last of those in WRITING.md itself. A model learns the style from the prompt.

The second half is length. `SNAPSHOT.md` defines `title` as "Short human title" and `goal` as a short outcome statement, with no number. The template's own `focus.note` is 266 words, this repo's 136, and FEAT-0021's title is a 30-word sentence. The narrative is worth having; the snapshot field is the wrong container, because the snapshot is the first thing every session reads.

## Scope

| Task | Finding | Files |
|---|---|---|
| [[TASK-0096]] | 5.1, 4.2 | `tools/instructions/WRITING.md`, `AGENTS.md` |
| [[TASK-0097]] | 5.2 | `tools/instructions/SNAPSHOT.md`, `change.md`, `issue.md`, `feature.md` |

## Out of scope

- **Rewriting the existing mannered sentences.** The rule lands here; applying it to the six named files is [[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]], which is rewriting those files anyway.
- **A validator check on title length.** Worth doing, and it needs a counted violation set first ([[ADR-0011-No-Permanent-Warning-Tier]]: a check arriving over undismantled debt is a check that gets disabled). Not this feature.
- **Rewriting the existing long titles and notes.** Same reason: the rule first, the backfill when someone has measured how many there are.

## Acceptance

- [ ] WRITING.md carries the four missing rules and the mannered-prose definition, numbered so nothing is displaced — evidence: the diff
- [ ] `AGENTS.md` "Output expectations" links those rules instead of prescribing a fixed-format preamble — evidence: the diff
- [ ] `SNAPSHOT.md` states a number for `title`, `goal` and `note`, and says where the longer text goes — evidence: the diff
- [ ] Three templates ask for a two-or-three-sentence, point-first summary — evidence: the diff
- [ ] The first notes written after this reads as the rules describe — evidence: the independent-review pass named in `acceptance_exception`

## Risk scan

Run against the LIFECYCLE.md triggers. No new risks: prose and templates only. No `RISK-*` created.

## Links

- Review: [[Prompting-Guide-Review-2026-09-03]]
- Implementation target: `~/Dev/repos/project-os`.

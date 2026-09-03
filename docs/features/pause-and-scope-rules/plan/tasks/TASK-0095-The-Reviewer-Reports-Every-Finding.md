---
type: "[[task]]"
id: TASK-0095
aliases: ["TASK-0095"]
title: "The reviewer reports every finding; the repro filter moves downstream"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 8.1"]
parent: "[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"
effort: S
depends: []
related: ["[[FEAT-0018-External-Independent-Review]]", "[[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]]"]
tests: []
---

# The reviewer reports every finding; the repro filter moves downstream

## Definition of Done
- [x] `independent-review/SKILL.md:47-50` asks the reviewer for every finding, each labelled reproduced or not reproduced.
- [x] The same file says the repro filter applies when findings are transcribed into `ISS-*` notes, which is a separate pass by construction.
- [x] This repo's `tools/scripts/review-external.py` drops "a finding without a repro is not a finding" from the reviewer's output schema and applies it at transcription instead (docstring point 4, and the schema it describes).

## Steps
- [x] Change the skill text first; the runner's docstring cites it.
- [x] Check whether any recorded review verdict depended on the old filter before changing the schema.

## Notes

Two repos, one rule. The instruction to be conservative is followed literally: a reviewer told that an unreproduced finding is not a finding drops the plausible ones itself, and nobody downstream ever sees them. Asking for everything and filtering later costs a longer reviewer output and nothing else.

Sequence after [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]], which edits line 45 of the same file.

Landed as template commit `9b53acb` on 2026-09-03 (skill) and in this repo's close-out commit for FEAT-0024 (`review-external.py`: docstring point 4, the schema gains `reproduced`, the post-run filter is replaced by a label and a count). Checked before changing the schema: no recorded review verdict in `docs/` depends on `dropped_unreproduced`; only TASK-0075 and TASK-0077 mention the runner, as its own history. Noticed and left alone under the scope rule: the runner's docstring header still says QUALITY.md requires a different model family, which ISS-0041 retired; follow-up in the feature's close-out summary.

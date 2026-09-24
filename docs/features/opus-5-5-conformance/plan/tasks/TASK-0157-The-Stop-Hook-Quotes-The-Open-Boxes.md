---
type: "[[task]]"
id: TASK-0157
aliases: ["TASK-0157"]
title: "The close-out Stop hook quotes the open boxes of the task in focus"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[Opus-5-5-Prompting-Guide-Review-2026-09-24]]"]
parent: "[[FEAT-0039-Opus-5-5-Prompting-Guide-Conformance]]"
effort: S
due: ""
depends: []
blocks: []
related: []
tests: ["[[TST-0007]]", "[[TST-0012]]"]
---

# The close-out Stop hook quotes the open boxes of the task in focus

## Definition of Done
- [x] When `focus.task` is set, `close-out-check.sh` reads that task's note (the `file:` of its snapshot item) and quotes up to five unticked `- [ ]` lines from its `## Definition of Done` and `## Steps` sections in the block reason, with a count of any more.
- [x] When every box is ticked, the reason says so and asks for the status to be set and focus cleared.
- [x] When the note cannot be found or read, the reason is the one used today. The hook still blocks and never errors.
- [x] The Codex `dispatch.py` stop handler does the same (ADR-0002).
- [x] HC-006 in `HOOKS.md` states the new block content, and why the hook keeps one continuation.
- [x] `test-hooks.sh` covers the open-boxes, all-ticked and missing-note cases, and `test-codex-adapter.py` covers the Codex case — evidence: seven new TST-0007 assertions (valid JSON, both boxes quoted, ticked boxes and other sections left out, both actions still named, all ticked, more than five, inline snapshot style); the missing-note case is every older Stop assertion, whose fixture has no note. `test_stop_quotes_open_boxes` in the Codex suite. `run-tests.py` 2026-09-24: TST-0007 97 of 97, TST-0012 OK

## Steps
- [x] Add a stdlib-free box extractor to the Stop hook (awk over the note).
- [x] Mirror it in `dispatch.py`.
- [x] Extend both test harnesses, run them, and record a mutation for adequacy on TST-0007.

## Notes
Run against this repo on 2026-09-24 with TASK-0080 in focus, the block read: "focus.task is still TASK-0080, and its note has 6 unticked box(es): \"Hook emits focus, counts and in-flight items; the reminder string is gone.\"; ... and 1 more." The first run printed invalid JSON (the quotes around each box were not escaped) and split one box at its own semicolon; both were fixed before the tests were written, and the JSON assertion exists for that reason.

The guide's pattern for unattended runs is to keep a checklist, check it whenever the model ends a turn, and reply by naming the open items: "Your task list still has open items: migrate the remaining two endpoints and update their tests." The task template already provides the checklist.

The guide also allows two or three automatic continuations before a run is left for review. The hook keeps its single continuation (`stop_hook_active`). The first block asks the agent either to finish or to write a handoff into the note. Writing the handoff is itself a write, so a counter allowing a second block would block exactly the stop the first block asked for. One continuation is within the guide's "two or three" upper bound.

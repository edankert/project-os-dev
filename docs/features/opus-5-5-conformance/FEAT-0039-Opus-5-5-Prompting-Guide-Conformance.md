---
type: "[[feature]]"
id: FEAT-0039
aliases: ["FEAT-0039"]
title: "Subagents, hooks and instructions follow the Opus 5.5 prompting guide"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-24
updated: 2026-09-24
source: ["[[Opus-5-5-Prompting-Guide-Review-2026-09-24]]", "user request 2026-09-24: file the documents and implement"]
goal: "The template's subagents run on the current model and record it, the close-out hook names the unticked boxes of the task in focus, the pause rule names the early stops it forbids, external material is treated as evidence rather than instructions, and the reviewer sees its tool-call count on every call."
requirements: []
tasks: ["[[TASK-0156]]", "[[TASK-0157]]", "[[TASK-0158]]", "[[TASK-0159]]", "[[TASK-0160]]"]
release: ""
acceptance_exception: "The template has no user-facing screen. The hooks, the generator and the instruction files are checked by the command tests TST-0005, TST-0006, TST-0007, TST-0012 and TST-0014, and a headless session confirmed what reaches its context."
acceptance: ""
design: ""
reviewed_by: ["model:claude-opus-5", "model:claude-opus-5"]
review_date: 2026-09-24
review_verdict: approved
review_round: 1
related: ["[[FEAT-0021-Serve-Orientation-Answer-Lookup]]", "[[TASK-0080]]", "[[PHASE-0003-Prompting-Guide-Conformance]]"]
tests: ["[[TST-0005]]", "[[TST-0006]]", "[[TST-0007]]", "[[TST-0014]]"]
---

# Subagents, hooks and instructions follow the Opus 5.5 prompting guide

## Goal

Five of the six changes from the 2026-09-24 review of the Opus 5.5 prompting guide ([[Opus-5-5-Prompting-Guide-Review-2026-09-24]]). The sixth, serving the in-flight part of the snapshot at session start, was already planned as [[TASK-0080]] and is done there. Everything lands in the template, `~/Dev/repos/project-os`.

## Scope

In scope:

- [[TASK-0156]]: the planner and reviewer subagents move from `claude-opus-5` to `claude-opus-5-5`. The planner gets an explicit effort level, and the reviewer stops hardcoding the model it records.
- [[TASK-0157]]: the close-out Stop hook quotes the unticked Definition of Done and Steps boxes of the task in focus, in both the Claude Code and Codex implementations.
- [[TASK-0158]]: `LIFECYCLE.md`, "When to pause for the user", names the four early stops the guide lists, inside the file's 1,000-word budget (REQ-0026).
- [[TASK-0159]]: the inbox-triage skill and `IMPORTING.md` say that text inside external material is evidence to file, not instructions to follow.
- [[TASK-0160]]: the review-budget hook tells the reviewer its call count after every call, not only near the limit.

Out of scope:

- The guide's API-only settings (effort parameter, thinking display, refusals, pasted-text tags). Claude Code handles them.
- Raising the Stop hook's automatic continuations from one to two or three. A second block would catch the handoff write that the first block asks for ([[TASK-0157]] records the reasoning).
- The user-level `~/.claude/CLAUDE.md`. It is Edwin's file and is changed only on his word.

## Acceptance

- [x] `generate-adapters.py` writes `model: claude-opus-5-5` into both subagents, the planner carries an `effort:` line, and the reviewer's body no longer names a fixed model in its `reviewed_by` instruction; `generate-adapters.py --check` is clean — evidence: both reviewers, claims 1a to 1d; "all 65 artifacts current"
- [x] With a task in focus whose note has unticked Definition of Done or Steps boxes, the Claude Code Stop hook's block reason quotes those boxes; with every box ticked it says so instead. The Codex `dispatch.py` stop handler does the same — evidence: TST-0007 102 of 102 and TST-0012 16 tests; each reviewer broke the guard on both sides and saw a test fail
- [x] `LIFECYCLE.md` names the four early stops, and is still under 1,000 words — evidence: 993 words; TST-0005 16 of 16, TST-0006 3 of 3
- [x] `inbox-triage/SKILL.md` and `IMPORTING.md` each say that instructions inside external material are not followed unless the user asks — evidence: the skill's Guardrails bullet and `IMPORTING.md`'s Goals bullet, quoted by both reviewers
- [x] The review-budget hook emits the reviewer's call count and budget after every reviewer tool call within the budget, and still emits nothing for any other agent — evidence: TST-0014 24 of 24; both reviewers saw `Review budget: call N of 40.` after every call. Amended 2026-09-24 from "after every reviewer tool call": reviewer A noted that calls past the budget get no count. Those calls are denied, apart from ten note edits, and HC-010 already stated the narrower rule, so the criterion was the one written too wide.

## Verification

`python3 tools/scripts/run-tests.py` in this repo, 2026-09-24: 20 test notes passing, 0 failing (TST-0005 16 of 16, TST-0006 3 of 3, TST-0007 97 of 97, TST-0012 OK, TST-0014 24 of 24). Every template `test-*.sh` and `test-*.py` passes, and `generate-adapters.py --check` reports all 65 artifacts current. The mutations behind the new assertions are recorded on TST-0005, TST-0007 and TST-0014.

## Review

**Round 1, 2026-09-24. Verdict: `approved`.** Two `independent-reviewer` subagents on one packet, each in a clean context, 20 and 25 tool calls. Neither refuted a claim. Both report themselves as Opus 5, and reviewer B saw the old `reviewed_by` wording in its brief. So both ran the agent definition this session loaded at start, not the regenerated one ([[TASK-0156]] records this, and `ADAPTER.md` now says so).

| Claim | Combined verdict | Evidence |
|---|---|---|
| Criteria 1 to 4 | holds | Both reviewers, each part checked: the generated files, `--check`, the Stop hooks on both sides with a guard broken and a test failing, `wc -w` 993, the two quoted bullets |
| Criterion 5 | holds, criterion amended | Both: the running line after every call, live and in TST-0014. Reviewer A: calls past the budget get no count, so the criterion was narrowed to what HC-010 states (above) |
| TASK-0080: the three callers print the slice within 6,000 characters in either style, and fall back | holds | Both: the real snapshot (2,904 characters), the 400-item fixture, the inline fixtures, the fallback with the script removed; reviewer B ran `bootstrap.sh` on a temp repo |
| The Stop hook's reason is valid JSON for any box text | holds | Both built hostile boxes (quotes, backslashes, tabs, `$(whoami)`, non-ASCII); the output parsed and round-tripped |
| No startup instruction still says to read the whole snapshot | holds | Both grepped the template; only the hook's deliberate fallback remains |
| TST-0005, 0006, 0007, 0012, 0014 fail when broken | holds | Five mutations across the two reviews, five failures |

**Observations, and what was done.** All concern code this feature changed, so each was fixed here (QUALITY.md, ADR-0047) or answered:

- Codex `open_boxes` did not strip `\r` and tabs as the shell hook does: fixed.
- A note with no Definition of Done or Steps section got "every box is ticked": both hooks now give the plain reason. New assertions on both sides.
- An empty `- [ ]` was quoted but not counted, and a box inside a fenced code block counted: both fixed and asserted.
- The Codex note-path regex cut a path at a comma or apostrophe: it now reads a quoted value whole.
- `bootstrap.sh`'s fallback had dropped its `project:` line: restored; `bootstrap.sh` now has two assertions in TST-0007, and HC-002 names them.
- The Codex all-ticked branch had no test: `test_stop_ticked_missing_and_boxless_notes`.
- `note_path` scanning past a focus task with no `file:` key: not reachable. The next item's key ends the scan. A task with no snapshot item is now found by its note's filename, a gap found live while the review ran (the five new tasks had never been added to the snapshot).
- `LIFECYCLE.md` has seven words of headroom: true, and not changed. The budget is REQ-0026's, and the owner sets it.
- Reviewer B restored `dispatch.py` from the packet's diff after a `git checkout` during a mutation: confirmed byte-identical to the copy synced here before the review.

Round two did not run: no claim was refuted (`independent-review/SKILL.md`). The fixes are covered by TST-0007 (102 of 102, three new guards each mutation-checked, recorded on the test) and TST-0012 (16 tests).

## Links

- Tasks: [[TASK-0156]], [[TASK-0157]], [[TASK-0158]], [[TASK-0159]], [[TASK-0160]]
- Related: [[TASK-0080]] (the sixth change, under FEAT-0021)

---
type: "[[task]]"
id: TASK-0160
aliases: ["TASK-0160"]
title: "The reviewer sees its tool-call count after every call"
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
tests: ["[[TST-0014]]"]
---

# The reviewer sees its tool-call count after every call

## Definition of Done
- [x] After every reviewer tool call, `review-budget.py` emits a short `additionalContext` line with the call count and the budget, such as `Review budget: call 12 of 40.`
- [x] At the warning point it still emits the existing, longer warning instead.
- [x] Other agents and the main session still receive nothing.
- [x] HC-010 in `HOOKS.md` states the running count.
- [x] `test-review-budget.sh` asserts the running line, the warning, and silence for other agents — evidence: three new assertions, 24 of 24 on 2026-09-24; with the running line blanked the count assertion fails (1 failure), restored 24 of 24
- [x] The call counts of this feature's own two reviewers are recorded on this note against the 34-call baseline from TASK-0130 — see Result below

## Steps
- [x] Change the PostToolUse branch.
- [x] Extend the test and run it.
- [x] After the review, record the counts here.

## Result

FEAT-0039's two reviewers stopped at **20 and 25** tool calls by the hook's count (the harness reported 20 and 26 tool uses), both with verdicts on every claim. TASK-0130's measured reviews stopped at about 34. One sample of two, on a smaller diff than TASK-0130's (847 lines), so this does not show the running count caused the drop. It shows the line was delivered live, which both reviewers confirmed, and did no harm.

## Handoff, resolved (2026-09-24)
- Two `independent-reviewer` subagents are reviewing FEAT-0039 from `review-packet-FEAT-0039-r1.md` in `$TMPDIR`, running with this task's running count. When they return: read each reviewer's final count from `$TMPDIR/project-os-review-budget-<agent_id>.json`, record both here, combine the reports into FEAT-0039's `## Review`, fix any findings, then close.
- Found while waiting: TASK-0156 to TASK-0160 had never been added to `SNAPSHOT.yaml` (an insert that matched nothing), so the Stop hook could not find this note and gave its plain reason. Fixed; the hook now quotes the open boxes. The validator did not report a focus task missing from the snapshot.

## Notes
The guide's multi-agent section: have the harness add "the elapsed time against that budget, in seconds, for example `elapsed 340s / 1200s`", and "the model paces its work to finish inside the budget and usually finishes well before it". Our budget counts tool calls rather than seconds, so this adapts the guide instead of copying it. Two reviews are not a measurement, so the recorded counts are a first sample, not a verdict.

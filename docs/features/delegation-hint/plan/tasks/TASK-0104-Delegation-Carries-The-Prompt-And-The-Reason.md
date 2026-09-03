---
type: "[[task]]"
id: TASK-0104
aliases: ["TASK-0104"]
title: "Delegation carries the user's prompt verbatim and the reason"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 3.2"]
parent: "[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"
effort: S
depends: []
related: ["[[TASK-0105]]"]
tests: []
---

# Delegation carries the user's prompt verbatim and the reason

## Definition of Done
- [ ] The hint says that a delegation to the planner carries the user's prompt verbatim plus one sentence on what the result enables.
- [ ] The planner prompt in `generate-adapters.py:63-78` says to expect both, and where the verbatim text lands in the note ([[TASK-0105]]'s "As reported" blockquote).
- [ ] The generator is re-run and `.claude/agents/planner.md` committed with it.

## Steps
- [ ] One sentence in each of the two strings.

## Notes

Today the lead paraphrases and the planner classifies the paraphrase. The guides are specific that a model connects a task to the right context when it knows what the output is for, and that this matters most for a long-running agent drawing on several workstreams — which is exactly what a preflight subagent is.

Shares the generator with [[TASK-0091]] and [[TASK-0092]]. Whichever lands last re-runs the generator once.

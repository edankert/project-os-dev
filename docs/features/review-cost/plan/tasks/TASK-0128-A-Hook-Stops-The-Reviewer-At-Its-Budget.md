---
type: "[[task]]"
id: TASK-0128
aliases: ["TASK-0128"]
title: "A hook stops the reviewer at its budget"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Small"
due: ""
depends: [TASK-0127]
blocks: [TASK-0130]
related: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
tests: [TST-0014]
---

# A hook stops the reviewer at its budget

## Definition of Done
- [x] A `PreToolUse` hook in `~/Dev/repos/project-os/tools/adapters/claude-code/hooks/` counts tool calls per `agent_id` when `agent_type` is `independent-reviewer`. It ignores every other session and agent.
- [x] At call 30 it lets the call through and adds the message: "10 tool calls left. Finish the claims you have started; mark the rest *not checked*."
- [x] From call 41 on it refuses the call with: "Budget reached. Write your report now with what you have; mark unchecked claims *not checked*." Writing the report needs no tool call, so the reviewer can still finish.
- [x] Recording the verdict in the note's frontmatter is allowed past the limit, so a stopped review can still record its outcome. This is the only exception.
- [x] The limit defaults to 40 and can be set per repo. Round two uses 15 (TASK-0129).
- [x] The count lives in a file keyed by `agent_id` under the system temp directory, so parallel reviews do not share a count.
- [x] A test feeds the hook recorded inputs: a non-reviewer call, calls 29, 30, 40 and 41, and a verdict edit at 45.
- [x] The hook is wired into the settings the adapter installs, and `HOOKS.md` documents it.

## Steps
- [x] Confirm the hook input fields `agent_id` and `agent_type` on the installed Claude Code version before relying on them. The docs list them (hooks page, checked 2026-09-18).
- [x] Write the hook and its test.
- [x] Wire it into the adapter's settings.

## Notes
- A refused call is a message the reviewer reads, not a crash. The report it then writes is the review.
- The hook is the limit that holds. The skill's prose is what the reviewer plans against.

## Done, 2026-09-18
Implemented in `3c979ee`; the warning moved to call 36 in `db98f46`. **The hook input fields are confirmed on Claude Code 2.1.275**: in all six real reviews run for TASK-0130 the hook counted calls per `agent_id` for `agent_type: independent-reviewer` and ignored every other session. No review reached the limit, and none drew a denial. The warning moved because a warning at call 30 to finish up acted as the real limit: every measured review stopped near call 34.

---
type: "[[task]]"
id: TASK-0102
aliases: ["TASK-0102"]
title: "The close-out Stop hook names the two real actions"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 2.2"]
parent: "[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"
effort: S
depends: []
related: []
tests: ["[[TST-0007]]"]
---

# The close-out Stop hook names the two real actions

## Definition of Done
- [ ] `hooks/close-out-check.sh:52,62` no longer says "acknowledge to continue".
- [ ] The block reason names two actions: if the work is complete, set the status and clear focus now; if you are stopping mid-flight for the user, write the handoff into the task note per `HANDOFF.md` "Before stopping work", then stop.
- [ ] The loop guard still lets the second stop through, so the handoff path terminates.
- [ ] [[TST-0007]] covers both branches.

## Steps
- [ ] Edit the two reason strings.
- [ ] Run the hook with focus set and with focus empty, and read what it prints.

## Notes

An acknowledgement is not an action, so the model either burns a turn writing one or resumes work it had decided to hand off. The hook can afford to be specific because the loop guard already prevents an endless block.

This is also where [[TASK-0093]]'s HANDOFF.md additions get used: the hook is the one place that tells an agent to write a handoff.

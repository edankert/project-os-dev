---
type: "[[task]]"
id: TASK-0158
aliases: ["TASK-0158"]
title: "The pause rule names the four early stops it forbids"
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
tests: ["[[TST-0005]]", "[[TST-0006]]"]
---

# The pause rule names the four early stops it forbids

## Definition of Done
- [x] `LIFECYCLE.md`, "When to pause for the user", names the four stops: a summary that announces the next step instead of taking it; an offer to continue unless the user objects; a list of decisions none of which blocks the work; a report because a milestone is done or the turn has been long.
- [x] It keeps the existing exceptions: a destructive or irreversible action, a real scope change, input only the user can give.
- [x] `LIFECYCLE.md` is under 1,000 words (REQ-0026), and the Cursor bundle is regenerated and under 1,040 — evidence: `wc -w` 993 (999 before); `test-word-budgets.sh` 3 of 3
- [x] TST-0005 and TST-0006 pass — evidence: `run-tests.py` 2026-09-24, TST-0005 16 of 16 (one new assertion: the four stops are named, so a later trim cannot drop them silently), TST-0006 3 of 3

## Steps
- [x] Rewrite the section and trim elsewhere in the file to stay in budget without dropping a rule.
- [x] Regenerate adapters and run both tests.

## Notes
The section grew by 37 words. Paid for, with no rule dropped: "Everything else is your judgment call" (the rule's first sentence already says it); the impact-analysis step's restatement of the pause rule, which it links; the example list after "a document written for a person"; "An item there is an unmade decision, not a record" (the sentence before says the same); and shorter reasons on close-out steps 8 and 9 and the risk scan.

The guide says Opus 5.5 "is responsive to instructions that name the specific kinds of early stop you want it to avoid". It also says to leave its full "keep working" paragraph out of applications where someone is there to answer. This takes only the named stops. The file is at 999 words before this task, so every word added is paid for by a word removed.

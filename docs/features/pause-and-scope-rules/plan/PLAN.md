---
type: "[[plan]]"
title: "Delivery plan — one pause rule, then the six one-sentence rules"
status: done
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"]
implements: ["[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"]
related: ["[[Prompting-Guide-Review-2026-09-03]]"]
---

<!-- Plans deliberately carry no `id:` / `aliases:` — see docs/__templates__/plan.md. -->
# Delivery plan — one pause rule, then the six one-sentence rules

## Where the work lands

Every file lands in `~/Dev/repos/project-os`, except the second half of [[TASK-0095]], which edits this repo's `tools/scripts/review-external.py`.

## Sequence

1. **[[TASK-0090]] first.** The eight stop-points need something to link to. Doing them in the other order produces eight links to a rule that does not exist yet.
2. **[[TASK-0091]]** follows immediately; a rule stated and not deferred to is the ninth phrasing rather than the first.
3. **[[TASK-0092]], [[TASK-0093]], [[TASK-0094]], [[TASK-0095]]** are independent of each other and of the first two. Run them in any order, or together.

## Coordination

- [[TASK-0091]] and [[TASK-0092]] both edit the planner prompt string in `tools/scripts/generate-adapters.py`, and so does [[TASK-0104]] in [[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]. Whichever runs last re-runs the generator and commits the regenerated `.claude/agents/planner.md` with it.
- [[ISS-0041-Four-Files-Still-Require-A-Different-Model-Family]] rewrites `independent-review/SKILL.md` line 45; [[TASK-0095]] rewrites lines 47-50 of the same file. Fix the issue first — it is a one-line change and this task is not.

## Open question carried into the work

[[TASK-0093]]'s HANDOFF.md addition says approaches set aside are recorded in the task note's "Next Actions". That section is named for actions, and a road not taken is not one. Either the section gets a sibling or the rule names a different home; decide in the task rather than in the plan.

---
type: "[[task]]"
id: TASK-0091
aliases: ["TASK-0091"]
title: "Eight stop-points shorten to the decision plus a link"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 2.1"]
parent: "[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"
effort: M
depends: ["[[TASK-0090]]"]
related: []
tests: ["[[TST-0005]]"]
---

# Eight stop-points shorten to the decision plus a link

## Definition of Done
- [ ] Each of these names the decision the user owns and links the LIFECYCLE.md pause rule, and none restates it: `HOOKS.md:56`, `status-transition/SKILL.md:28`, `issue-intake/SKILL.md:25` and `:53`, `feature-scaffold/SKILL.md:50`, `release-prep/SKILL.md:34`, `close-out/SKILL.md` step 1, and the planner prompt in `tools/scripts/generate-adapters.py`.
- [ ] `close-out/SKILL.md` step 1 also carries the blocked-part sentence: complete every other part in full, then say exactly what was left out and why.
- [ ] The generator is re-run and the regenerated `.claude/agents/planner.md` is committed with the change.
- [ ] [[TST-0005]] passes.

## Steps
- [ ] List the eleven stop-points first and confirm the count; the review names eight files and eleven sites.
- [ ] Rewrite each to at most three lines.
- [ ] Grep for any remaining full statement of the rule outside LIFECYCLE.md.

## Notes

The wording differs at every site today: "stop and present resolution options", "warn and require explicit user confirmation", "stop and request explicit user confirmation", "Present the list to the user for decision". Four phrasings of one rule is how a reader learns there are four rules.

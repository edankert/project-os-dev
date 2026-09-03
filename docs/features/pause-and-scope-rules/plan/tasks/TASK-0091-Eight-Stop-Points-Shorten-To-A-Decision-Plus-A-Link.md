---
type: "[[task]]"
id: TASK-0091
aliases: ["TASK-0091"]
title: "Eight stop-points shorten to the decision plus a link"
status: done
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
- [x] Each of these names the decision the user owns and links the LIFECYCLE.md pause rule, and none restates it: `HOOKS.md:56`, `status-transition/SKILL.md:28`, `issue-intake/SKILL.md:25` and `:53`, `feature-scaffold/SKILL.md:50`, `release-prep/SKILL.md:34`, `close-out/SKILL.md` step 1, and the planner prompt in `tools/scripts/generate-adapters.py`.
- [x] `close-out/SKILL.md` step 1 also carries the blocked-part sentence: complete every other part in full, then say exactly what was left out and why.
- [x] The generator is re-run and the regenerated `.claude/agents/planner.md` is committed with the change.
- [x] [[TST-0005]] passes.

## Steps
- [x] List the eleven stop-points first and confirm the count; the review names eight files and eleven sites.
- [x] Rewrite each to at most three lines.
- [x] Grep for any remaining full statement of the rule outside LIFECYCLE.md.

## Notes

The wording differs at every site today: "stop and present resolution options", "warn and require explicit user confirmation", "stop and request explicit user confirmation", "Present the list to the user for decision". Four phrasings of one rule is how a reader learns there are four rules.

Landed as template commits `bb6eb70` and `79e0332` on 2026-09-03. Twelve sites in nine files: `docs/PHASES.md` 65 (found by the review of this feature), LIFECYCLE.md 61 and 72, HOOKS.md 56, status-transition 28, issue-intake 25 and 53, feature-scaffold 50, release-prep 34 and 39, close-out step 1, the planner prompt. The harness is `tools/scripts/test-pause-rule.sh`, 14 assertions after the review round; [[TST-0005]] records its seven inversions.

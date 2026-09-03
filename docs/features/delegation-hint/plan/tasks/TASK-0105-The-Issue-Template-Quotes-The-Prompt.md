---
type: "[[task]]"
id: TASK-0105
aliases: ["TASK-0105"]
title: "The issue template quotes the prompt under 'As reported'"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 7.3"]
parent: "[[FEAT-0027-The-Hint-Serves-Focus-State-Instead-Of-Pushing-Delegation]]"
effort: S
depends: []
related: ["[[TASK-0104]]"]
tests: []
---

# The issue template quotes the prompt under 'As reported'

## Definition of Done
- [x] `docs/__templates__/issue.md` has a blockquote under "Problem" labelled "As reported", for the reporter's own words.
- [x] `ad-hoc-intake/SKILL.md:36` and the issue-intake skill point at it instead of saying "capture the prompt verbatim in the note (Problem/Evidence)" with no format.
- [x] The callout uses the same shape `DECISIONS.md` already uses for a human decision "in the decider's own words", so the corpus has one convention for quotation rather than two.

## Steps
- [x] Add the blockquote to the template.
- [x] Update the two skills to name it.

## Notes

The point is not ceremony. An unmarked verbatim sentence and the agent's paraphrase sit in the same paragraph today, and a later reader cannot tell which is which — which matters most for the sentence a fix will be judged against.

Landed as template commit `8d35297` on 2026-09-03. The callout is `> [!quote] As reported — <date> (<who>)`, the DECISIONS.md decision-record shape with a different callout type, so the corpus has one quotation convention.

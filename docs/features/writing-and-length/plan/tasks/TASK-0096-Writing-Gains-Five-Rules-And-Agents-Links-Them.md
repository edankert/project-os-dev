---
type: "[[task]]"
id: TASK-0096
aliases: ["TASK-0096"]
title: "WRITING.md gains four rules; AGENTS.md links them"
status: done
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 5.1, 4.2"]
parent: "[[FEAT-0025-Writing-Rules-For-The-Final-Message-And-Length-Limits]]"
effort: S
depends: []
related: []
tests: []
---

# WRITING.md gains four rules; AGENTS.md links them

## Definition of Done
- [x] WRITING.md rule 7: mannered prose substitutes metaphor and flourish for direct statement; when a literal phrase is available, use it. Glossed with one of the corpus's own examples.
- [x] Rule 8: the final message after a long run is a re-grounding for a reader who did not watch the work — no working shorthand, no arrow chains, no hyphen-stacked compounds, no labels invented while working.
- [x] Rule 9: keep the message short by dropping details that do not change what the reader does next, not by compressing the ones that do.
- [x] Rule 10: say in one line what you are about to do before starting; close with a recap that stands on its own.
- [x] The distinction between a between-tool-calls line and the final message is stated once, since rules 8 and 10 apply differently to each.
- [x] `AGENTS.md:50-51` "Output expectations" links these rules instead of prescribing a preamble of purpose, active item and intended files.

## Steps
- [x] Number the new rules 7 to 10 and leave 1 to 6 untouched, so existing references still resolve.
- [x] Check that no other file restates the AGENTS.md preamble format before deleting it.

## Notes

The mannered-prose rule and the four communication rules land in one commit because they are the same file and the same subject. Applying rule 7 to the existing corpus is [[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]'s job, not this one.

Named instances to use as examples, all real: `STATUSES.md:151`, `TESTING.md:604` and `:678`, `TAXONOMY.md:427`, `feature-scaffold/SKILL.md:61`, and `WRITING.md:25` itself.

Landed as template commit `e490420` on 2026-09-03. Rules 7 to 10 and a "Two kinds of message" section; rules 1 to 6 keep their numbers. Rule 2's own "two sentences wearing one hat" was rewritten in the same commit and is quoted in rule 7 as the example, one step beyond the task's letter because a rule file should not carry the pattern it bans. Checked before deleting the AGENTS.md preamble: no other file restates it (grep for "intended files" and "active feature/task" over tools/, AGENTS.md, CONTEXT.md, CLAUDE.md, .cursor).

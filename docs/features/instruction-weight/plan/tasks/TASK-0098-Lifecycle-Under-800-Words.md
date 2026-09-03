---
type: "[[task]]"
id: TASK-0098
aliases: ["TASK-0098"]
title: "LIFECYCLE.md under 800 words: rule, reason, link"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 4.1"]
parent: "[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"
effort: M
depends: []
blocks: ["[[TASK-0099]]"]
related: ["[[REQ-0026-Instruction-Files-Carry-Rules-Not-History]]"]
tests: ["[[TST-0006]]"]
---

# LIFECYCLE.md under 800 words: rule, reason, link

## Definition of Done
- [ ] `wc -w tools/instructions/LIFECYCLE.md` is under 800 (1,343 before).
- [ ] Every rule in the file is a normative sentence, one line of reason, and a link to the ADR or issue that settled it.
- [ ] Every anecdote removed appears in an ADR Context section or a change note, listed in the change note's moved-text table.
- [ ] No rule was deleted. The diff shows the same set of obligations, shorter.
- [ ] The generator is re-run and `.cursor/rules/lifecycle.mdc` committed with it.

## Steps
- [ ] Take the before count and record it.
- [ ] Work section by section. The "Mandatory Automated Documentation" and inbox sections are the two longest.
- [ ] Move "a local pass is not a CI pass" and its two anecdotes into the change note or the relevant ADR.
- [ ] Take the after count and put both in the change note.

## Notes

Do this after [[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]] lands. That feature adds three rules to the Execution section, and the budget has to be met with them in place, not before.

This is the file with the highest leverage in the system: `CLAUDE.md` imports it on every Claude Code session in twelve repos, and the Cursor bundle inlines it on every Cursor session.

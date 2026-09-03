---
type: "[[task]]"
id: TASK-0098
aliases: ["TASK-0098"]
title: "LIFECYCLE.md under its word budget: rule, reason, link"
status: done
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

# LIFECYCLE.md under its word budget: rule, reason, link

## Definition of Done
- [x] `wc -w tools/instructions/LIFECYCLE.md` is under its budget (1,343 before; the budget was 800 and is 1,000 after the amendment on REQ-0026; 966 at the trim, 996 after the review round).
- [x] Every rule in the file is a normative sentence, one line of reason, and a link to the ADR or issue that settled it.
- [x] Every anecdote removed appears in an ADR Context section or a change note, listed in the change note's moved-text table.
- [x] No rule was deleted. The diff shows the same set of obligations, shorter.
- [x] The generator is re-run and `.cursor/rules/lifecycle.mdc` committed with it.

## Steps
- [x] Take the before count and record it.
- [x] Work section by section. The "Mandatory Automated Documentation" and inbox sections are the two longest.
- [x] Move "a local pass is not a CI pass" and its two anecdotes into the change note or the relevant ADR.
- [x] Take the after count and put both in the change note.

## Notes

Do this after [[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]] lands. That feature adds three rules to the Execution section, and the budget has to be met with them in place, not before.

This is the file with the highest leverage in the system: `CLAUDE.md` imports it on every Claude Code session in twelve repos, and the Cursor bundle inlines it on every Cursor session.

Landed as template commit `38db9ad` on 2026-09-03. Counts: 1,343 at the review, 1,632 after FEAT-0024, 966 after the trim; the Cursor copy 1,374 to 1,005. The 800 budget was not met and REQ-0026 is amended to 1,000 with the reasoning recorded there; the commit message quotes 1,599 as the pre-trim count, corrected to 1,632 by the FEAT-0024 review. The two gitignore anecdotes are in the change note's moved-text table.

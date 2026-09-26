---
type: "[[task]]"
id: TASK-0175
aliases: ["TASK-0175"]
title: "A walk step cites a check's step and shows the check's current text"
status: done
phase: "[[PHASE-0009]]"
owner: user:edwin
created: 2026-09-26
updated: 2026-09-26
source: ["[[ISS-0088-Editing-A-Check-Breaks-Every-Walk-That-Quotes-It]]", "Edwin, 2026-09-26 (/goal): 'implement and test PHASE-0009 fully ... ISS-091 implement as suggested, ISS-0088 also as suggested.'"]
parent: "[[ISS-0088-Editing-A-Check-Breaks-Every-Walk-That-Quotes-It]]"
effort: M
due: ""
depends: []
blocks: []
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: ["[[TST-0033-A-Reworded-Check-Breaks-No-Tag-Only-Walk]]"]
---

# A walk step cites a check's step and shows the check's current text

## Definition of Done
- [x] An expectation line may be only its tag (`TST-0480.1`); the generator renders the check's current text for it on the sheet and in the payload the cockpit reads. `walk-sheet.py`'s `expand_tag_only` does it in the audit both paths share. A tag prints Expect line N when the check has one Expect line per numbered step, and all its Expect lines otherwise. The cockpit shows it once its bundled copy of `walk-sheet.py` is refreshed.
- [x] A quoted line still works, and a tool rewrites quoted lines to tag-only lines: `tools/scripts/walk-tags.py`, only where the tag prints exactly the quoted words. `--refresh` re-quotes a line whose check was reworded.
- [x] ADR-0045's word-for-word rule is amended by a new ADR (ADR-0049); TESTING.md rule 9 says so, and so do the walk-procedure skill and the procedure template.
- [x] Editing a check no longer breaks a tag-only walk; tested (TST-0033).

## Steps
- [x] Build it in the template, `~/Dev/repos/project-os`.
- [x] Test it, including a mutation that the test catches (TST-0033: five mutations, all caught).

## Converter dry run on your-trainer, 2026-09-26

`walk-tags.py` would rewrite 232 of 956 quoted lines as tags alone. Of the 724 it keeps, 308 quote checks that state no Expect text, which the validator never compares, so rewording those checks breaks nothing already. The other 416 quote one of several Expect lines of a check whose steps and Expect lines do not pair; for those, `--refresh` is the fix when a check is reworded. Nothing was written to your-trainer; its session decides when to run it.

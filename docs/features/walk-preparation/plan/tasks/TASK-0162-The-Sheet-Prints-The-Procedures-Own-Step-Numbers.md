---
type: "[[task]]"
id: TASK-0162
aliases: ["TASK-0162"]
title: "The walk sheet prints each step under its number in the procedure"
status: done
phase: "[[PHASE-999]]"
owner: user:edwin
created: 2026-09-25
updated: 2026-09-25
source: ["[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]", "Edwin, 2026-09-25: 'go for option 1'"]
parent: "[[ISS-0086-Sheet-Step-Numbers-Do-Not-Match-Procedure-Prose]]"
effort: S
due: ""
depends: []
blocks: []
related: ["[[FEAT-0033-A-Walk-Keeps-Required-Preparation]]"]
tests: ["[[TST-0023]]", "[[TST-0011]]"]
---

# The walk sheet prints each step under its number in the procedure

## Definition of Done
- [x] A kept step's heading is `Step N` with N its number in the procedure, marked `(preparation)` where it records no verdict, with no "source step" label — evidence: template `cd50653`; `test_steps_keep_their_procedure_numbers` asserts the headings Step 1 (preparation), Step 2 (preparation), Step 4
- [x] An evidence comparison names its source by the same number — `test_capture_and_timer_are_authored_and_only_requested_when_used` asserts "Compare with evidence from step 1."
- [x] When steps are left out, the sheet says the numbers are the procedure's own and skip.
- [x] TESTING.md rule 9, "What prints", says so in place of "Display positions are consecutive".
- [x] TST-0023 asserts the new headings, and a mutation back to positions fails it (1 failure, in a full copy of the template); 21 of 21. Amended from "TST-0023 and TST-0011": TST-0011's fixture keeps every step, so its position and number are the same and it cannot tell them apart. It still passes, 160 of 160.
- [x] Committed to the template, and not synced to any repo with a walk (project-os-cockpit, your-trainer) until the cockpit's walk page shows the same numbers (the cockpit half of ISS-0086), so the sheet and the page never disagree. project-os-dev took it with the 2026-09-25 PHASE-0003 sync: it has no walk procedures, so no walker sees the two disagree.

## Steps
- [x] Change `render_procedure`.
- [x] Update rule 9 and the preparation harness.
- [ ] Hand the cockpit half to the session that owns project-os-cockpit FEAT-0151.

## Notes
The last step, handing the cockpit half over, is ISS-0086's to finish: the issue carries the handoff text and stays open until the walk page shows the same numbers and both land in one sync. This task's own change is complete.

Option 1 of ISS-0086, chosen by Edwin on 2026-09-25. The cockpit keeps its own progress count ("Step 1 of 4", FEAT-0151 criterion B3) separate from the step number.

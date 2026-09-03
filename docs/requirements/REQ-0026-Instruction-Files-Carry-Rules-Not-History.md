---
type: "[[requirement]]"
id: REQ-0026
aliases: ["REQ-0026"]
title: "An always-loaded instruction file carries rules and reasons, not history"
status: draft
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 4.1"]
priority: medium
scope: "tools/instructions/ in the project-os template, and the adapter outputs generated from those files"
acceptance:
  - "LIFECYCLE.md is under 800 words"
  - "The generated Cursor always-on bundle tracks the trimmed sources"
  - "Every rule in the six trimmed files is a normative sentence, one line of reason, and a link"
  - "Every anecdote removed from an instruction file exists in an ADR or change note"
  - "Provisional: STATUSES.md is under 1,600 words"
  - "Provisional: TESTING.md is under 950 words"
  - "Provisional: QUALITY.md is under 850 words"
  - "Provisional: DECISIONS.md is under 850 words"
implements: "[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"
verifies: []
related: ["[[ADR-0016-Ceremony-Proportionate-To-The-Change]]", "[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs]]"]
tests: ["[[TST-0006]]"]
---

# An always-loaded instruction file carries rules and reasons, not history

## Statement

An instruction file that an agent loads on every session must state its rules, the reason for each, and a link to the decision that took it. The history of how a rule came to be worded that way belongs in the ADR's Context section or in the change note, not in the file that is paid for on every session.

`tools/instructions/README.md:17` already says "avoid narrative prose where possible". This requirement gives that sentence a number to hold it to, on the one file every Claude Code and Cursor session loads.

## Why a requirement and not just a task

The word budget outlives the tasks that first meet it. Without it, LIFECYCLE.md grows back — every future rule arrives with its story attached, and each addition is individually reasonable.

## Acceptance Criteria

- [ ] LIFECYCLE.md is under 800 words — evidence: `wc -w tools/instructions/LIFECYCLE.md` in the template (1,343 on 2026-09-03)
- [ ] The generated Cursor always-on bundle tracks the trimmed sources — evidence: `.cursor/rules/lifecycle.mdc` regenerated and under 830 words (1,374 on 2026-09-03; the four always-on rules totalled 5,711)
- [ ] Every rule in the six trimmed files is a normative sentence, one line of reason, and a link — evidence: the reviewer's reading of the diff at close-out
- [ ] Every anecdote removed from an instruction file exists in an ADR or change note — evidence: the moved-text table in the change note for this feature
- [ ] Provisional: STATUSES.md is under 1,600 words — evidence: `wc -w` (2,772 on 2026-09-03)
- [ ] Provisional: TESTING.md is under 950 words — evidence: `wc -w` (1,608 on 2026-09-03)
- [ ] Provisional: QUALITY.md is under 850 words — evidence: `wc -w` (1,408 on 2026-09-03)
- [ ] Provisional: DECISIONS.md is under 850 words — evidence: `wc -w` (1,381 on 2026-09-03)

## Provisional budgets for the other four files

Added 2026-09-03 at Edwin's request, with his doubt recorded: "suggest word budgets, unsure how useful they are." The four numbers are the LIFECYCLE.md ratio applied to each file: 800 of 1,343 is 60%, and 60% of each current count, rounded down to a round number, gives the budgets above. They are stopping rules for [[TASK-0099]], so the trim knows when it is done, not gates. Two consequences follow:

- Re-set them from the measured ratio once [[TASK-0098]] has landed LIFECYCLE.md. If the honest trim of that file comes out at 700 or at 900 words, the other four budgets move with it, and the change note for TASK-0098 records the new numbers.
- They stay out of the validator. A length check over a fleet with undischarged debt is the shape ADR-0011 forbids arming; [[TST-0006]] may grow assertions for them when TASK-0099 lands, and the criteria are reconciled at close-out if a file cannot honestly meet its number.

## Traceability

- Implements: [[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]
- Verified by: [[TST-0006]] (word budgets), and the independent review pass on the diff for the shape criteria

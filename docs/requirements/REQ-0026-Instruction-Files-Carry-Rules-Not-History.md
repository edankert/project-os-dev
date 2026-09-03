---
type: "[[requirement]]"
id: REQ-0026
aliases: ["REQ-0026"]
title: "An always-loaded instruction file carries rules and reasons, not history"
status: implemented
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] finding 4.1"]
priority: medium
scope: "tools/instructions/ in the project-os template, and the adapter outputs generated from those files"
acceptance:
  - "LIFECYCLE.md is under 1,000 words (amended 2026-09-03 from 800; see Amendments)"
  - "The generated Cursor always-on bundle tracks the trimmed sources"
  - "Every rule in the five trimmed files is a normative sentence; a rule that retired a behaviour or that a validator check enforces names its reason or the check; every measurement moved out is held by the decision the rule cites (amended 2026-09-03 from one-reason-and-a-link on every rule; see Amendments)"
  - "Every anecdote removed from an instruction file exists in an ADR or change note"
  - "STATUSES.md is under 1,700 words (amended 2026-09-03 from the provisional 1,600; see Amendments)"
  - "TESTING.md is under 1,000 words (amended from the provisional 950)"
  - "QUALITY.md is under 950 words (amended from the provisional 850)"
  - "DECISIONS.md is under 1,000 words (amended from the provisional 850)"
implements: "[[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]"
verifies: []
related: ["[[ADR-0016-Ceremony-Proportionate-To-The-Change]]", "[[ISS-0031-Instruction-Prescribes-A-Method-For-Two-Different-Needs]]"]
tests: ["[[TST-0006]]"]
---

# An always-loaded instruction file carries rules and reasons, not history

## Statement

An instruction file that an agent loads on every session must state its rules, and, for a rule that retired a behaviour or that a validator check enforces, the reason or the check name, with a link to the decision that took it. The history of how a rule came to be worded that way belongs in the ADR's Context section or in the change note, not in the file that is paid for on every session. (Amended 2026-09-03 from "the reason for each": a reason on every rule line would double STATUSES.md, which the word budget forbids; see Amendments.)

`tools/instructions/README.md:17` already says "avoid narrative prose where possible". This requirement gives that sentence a number to hold it to, on the one file every Claude Code and Cursor session loads.

## Why a requirement and not just a task

The word budget outlives the tasks that first meet it. Without it, LIFECYCLE.md returns to its old length: every future rule arrives with its story attached, and each addition is individually reasonable.

## Acceptance Criteria

- [x] LIFECYCLE.md is under 1,000 words (amended from 800, see Amendments) — evidence: `wc -w tools/instructions/LIFECYCLE.md` in the template: 966 at commit `38db9ad` on 2026-09-03 (1,343 at the review, 1,632 after FEAT-0024); [[TST-0006]]
- [x] The generated Cursor always-on bundle tracks the trimmed sources — evidence: `.cursor/rules/lifecycle.mdc` regenerated in the same commit, 1,005 words at the trim and 1,034 after the review round (1,374 on the morning of 2026-09-03, 1,663 after FEAT-0024); [[TST-0006]] asserts under 1,040 and that the generator reports it current
- [x] Every rule in the five trimmed files is a normative sentence; a rule that retired a behaviour or that a validator check enforces names its reason or the check; every measurement moved out is held by the decision the rule cites (amended, see Amendments) — evidence: the independent review of 2026-09-03 counted rule lines against reason and link lines (LIFECYCLE 31/4/3, STATUSES 85/4/18, TESTING 26/2/2, QUALITY 25/3/5, DECISIONS 12/4/5) and found the original wording unmet; the seven rules it found dropped are restored in template commit `491afa8`; the moved-text table in CHG-20260903-Instruction-Weight names a destination for every measurement
- [x] Every anecdote removed from an instruction file exists in an ADR or change note — evidence: the moved-text table in the template's CHG-20260903-Instruction-Weight (commit `fa4c228`), sixteen rows, each with a destination
- [x] STATUSES.md is under 1,700 words (amended from 1,600) — evidence: `wc -w` 1,663 at template commit `244f0e6`, 1,672 at `491afa8` after two dropped rules were restored (2,772 on the morning of 2026-09-03)
- [x] TESTING.md is under 1,000 words (amended from 950) — evidence: `wc -w` 961 at `cb92705`, 967 at `491afa8` (1,608)
- [x] QUALITY.md is under 950 words (amended from 850) — evidence: `wc -w` 884 at `e6b33a5`, 902 at `491afa8` after the coverage list and two paths were restored (1,418)
- [x] DECISIONS.md is under 1,000 words (amended from 850) — evidence: `wc -w` 954 at `6acf773`, 973 at `491afa8` after the three ADR-0011 clauses were restored (1,381)

## Amendments

**2026-09-03, LIFECYCLE.md budget 800 to 1,000.** The 800 was set as 60% of the file's 1,343 words on the morning of 2026-09-03. FEAT-0024 then added the pause rule and the scope rule to the same file, 289 words with their reasons, asked for by the same review. The trim in TASK-0098 came out at 966 words, 59% of the 1,632 the file had grown to. (The trim commit's message says 1,599, the count after FEAT-0024's first commit only; the first review round corrected it.) The provisional-budgets section below anticipated this: "re-set them from the measured ratio once TASK-0098 has landed". The budget is re-set to 1,000 and the Cursor copy to 1,040, the source budget plus its 40-word generated header. What was not done: dropping reasons to reach 800, which the feature's out-of-scope list forbids.

**2026-09-03, the shape criterion.** The original third criterion asked for one line of reason and a link on every rule. The independent review counted rule lines against lines carrying a reason or a link and found under a quarter had either, and it is right: the criterion contradicts the word budget, because a reason on each of STATUSES.md's 85 rule lines would double the file. The implementation resolved that in favour of the budget without saying so. The criterion is amended to what was built and is worth keeping: every rule is a normative sentence; a rule that retired a behaviour or that a validator check enforces names its reason or the check; every measurement moved out is held by the decision the rule cites. A reader who wants the reason for an ordinary rule follows the link to the decision; the always-loaded file carries the reasons that stop an agent from re-deriving a retired behaviour. The review also found seven rules the trim had dropped; they are restored in template commit `491afa8`, and the "no rule dropped" claim in the change note is now true.

**2026-09-03, the other four budgets, measured, and the method changed.** STATUSES.md landed at 1,663 against 1,600, TESTING.md at 961 against 950, QUALITY.md at 884 against 850, DECISIONS.md at 954 against 850; after the review restored seven rules they are 1,672, 967, 902 and 973. The method for re-setting them is not the one the LIFECYCLE amendment used. That one re-set from the measured ratio, as this section said it would. This one sets each budget to the next round number above the measured count: 1,700, 1,000, 950, 1,000. For STATUSES, TESTING and QUALITY the two methods agree within rounding (they landed at 60%, 60% and 63%). For DECISIONS.md they do not: the ratio would give about 830 and the file is 973, 70% of its original, an 18% raise over the ratio. The reason is that its two fenced examples and the three-section rule-ADR block are the convention itself and cannot be shortened without changing it. The independent review accepted that reason and asked that the switch of method be stated; it is stated here. Each file was trimmed until the next cut would remove a reason, which the feature's out-of-scope list forbids. The budgets remain stopping rules for the next growth, and Edwin's recorded doubt about their usefulness stands.

## Provisional budgets for the other four files

Added 2026-09-03 at Edwin's request, with his doubt recorded: "suggest word budgets, unsure how useful they are." The four numbers are the LIFECYCLE.md ratio applied to each file: 800 of 1,343 is 60%, and 60% of each current count, rounded down to a round number, gives the budgets above. They are stopping rules for [[TASK-0099]], so the trim knows when it is done, not gates. Two consequences follow:

- Re-set them from the measured ratio once [[TASK-0098]] has landed LIFECYCLE.md. If the honest trim of that file comes out at 700 or at 900 words, the other four budgets move with it, and the change note for TASK-0098 records the new numbers.
- They stay out of the validator. A length check over a fleet that still carries over-budget files would be a warning nobody clears, which ADR-0011 forbids; [[TST-0006]] may grow assertions for them when TASK-0099 lands, and the criteria are reconciled at close-out if a file cannot honestly meet its number.

## Traceability

- Implements: [[FEAT-0026-Trim-The-Instruction-Files-Loaded-Every-Session]]
- Verified by: [[TST-0006]] (word budgets), and the independent review pass on the diff for the shape criteria

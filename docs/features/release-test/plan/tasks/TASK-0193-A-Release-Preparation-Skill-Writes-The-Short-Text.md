---
type: "[[task]]"
id: TASK-0193
aliases: ["TASK-0193"]
title: "A release-preparation skill has an agent write the short text and keeps the edits only when the length check and the validator pass"
status: backlog
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "M"
due: ""
depends: ["[[TASK-0191]]", "[[TASK-0192]]"]
blocks: []
related: ["[[REQ-0036-A-Line-Or-Section-Over-Its-Word-Limit-Is-Reported]]", "[[ADR-0050-The-Walk-Becomes-The-Release-Test-And-Its-Expected-Results-Live-In-The-Checks]]"]
tests: []
---

# A release-preparation skill has an agent write the short text and keeps the edits only when the length check and the validator pass

A new skill, `tools/skills/release-test-prep/SKILL.md`, does the edits ADR-0050's D3 allows, then runs the checks.

## Definition of Done
- [ ] The skill writes the what-changed file for each platform, one short line per change, grouped by section and screen.
- [ ] The skill shortens each Expect line the length check reports, in the test note itself, and keeps its meaning. It splits a line that mixes platforms into `[android]` and `[ios]` lines.
- [ ] The skill shortens each procedure action the length check reports.
- [ ] The skill runs the length check and the validator, and keeps its edits only if both pass.
- [ ] The skill says that a change of meaning in an Expect line is a change to the check and reopens it in the ledger.
- [ ] `tools/skills/release-prep/SKILL.md` calls it before the release test is handed over, and the skills README, CLAUDE.md skill list and generated adapters list it.

## Steps
- [ ] Write the skill from the pattern of the procedure skill (TASK-0194).
- [ ] Wire it into release-prep.
- [ ] Run it on a copy of your-trainer's Equipment section as a dry run.

## Notes
- The agent's edits are reviewed by the owner in the commit, as any other change to a note.

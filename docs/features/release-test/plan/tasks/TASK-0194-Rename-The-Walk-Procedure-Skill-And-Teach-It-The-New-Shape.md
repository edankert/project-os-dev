---
type: "[[task]]"
id: TASK-0194
aliases: ["TASK-0194"]
title: "Rename the walk-procedure skill to release-test-procedure and rewrite it for groups, short actions and tag-only lines"
status: done
phase: "[[PHASE-0010-The-Release-Test-Reads-In-Short-Lines]]"
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
parent: "[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"
effort: "S"
due: ""
depends: ["[[TASK-0187]]", "[[TASK-0189]]"]
blocks: []
related: ["[[REQ-0037-The-Walk-Is-Called-The-Release-Test-Everywhere]]", "[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]"]
tests: []
verification_waiver: "Instruction text in one skill; no executable behaviour changes and no harness can observe whether an agent follows it. Checked by reading it against the procedure template and TESTING.md rule 9; your-trainer TASK-0975 uses it for real to rewrite the Equipment procedure."
waiver_expires: 2026-12-27
---

# Rename the walk-procedure skill to release-test-procedure and rewrite it for groups, short actions and tag-only lines

The skill that writes a section's procedure is renamed and taught the new shape.

## Definition of Done
- [x] `tools/skills/walk-procedure/` is `tools/skills/release-test-procedure/`, with the copies under `.claude/skills/` and `.agents/skills/` regenerated. Moved by TASK-0187; `generate-adapters.py --check` reports all 65 artifacts current after this rewrite.
- [x] The skill writes groups with a heading and a `Start:` line, one short action line per step, and tag-only expectation lines. Checklist steps 3 to 7 (project-os 8309260).
- [x] The skill no longer asks for a screen name on each step, and no longer quotes Expect text. The `SUR-*` input is gone; "What not to do" forbids a screen name, a step number or a quoted Expect line, and says to shorten a long Expect line in the check note.
- [x] The skill runs the length check with `--check` and keeps a procedure only when it passes. Step 9: fix every error and every warning about the procedure, including lines over their word limit, which TASK-0192 adds to `--check`.
- [x] Every link to the old skill path in the template points at the new one. `rg walk-procedure` finds only the migration map, the validator's OLD-NAME check and their tests, which name the old path on purpose.

## Steps
- [x] Rename the folder with `git mv` (TASK-0187).
- [x] Rewrite the steps and the list of things an agent gets wrong.
- [x] Regenerate the adapters (nothing changed in them: they carry the skill's "When to use", which is unchanged).

## Notes
- The folder move itself is part of TASK-0187's rename. This task rewrites what the skill says.
- The two readiness examples in step 8 are the approved Equipment Hub page's checks 18 and 27.

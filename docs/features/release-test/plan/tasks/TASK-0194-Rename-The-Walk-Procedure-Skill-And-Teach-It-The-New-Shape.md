---
type: "[[task]]"
id: TASK-0194
aliases: ["TASK-0194"]
title: "Rename the walk-procedure skill to release-test-procedure and rewrite it for groups, short actions and tag-only lines"
status: backlog
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
---

# Rename the walk-procedure skill to release-test-procedure and rewrite it for groups, short actions and tag-only lines

The skill that writes a section's procedure is renamed and taught the new shape.

## Definition of Done
- [ ] `tools/skills/walk-procedure/` is `tools/skills/release-test-procedure/`, with the copies under `.claude/skills/` and `.agents/skills/` regenerated.
- [ ] The skill writes groups with a heading and a `Start:` line, one short action line per step, and tag-only expectation lines.
- [ ] The skill no longer asks for a screen name on each step, and no longer quotes Expect text.
- [ ] The skill runs the length check with `--check` and keeps a procedure only when it passes.
- [ ] Every link to the old skill path in the template points at the new one.

## Steps
- [ ] Rename the folder with `git mv`.
- [ ] Rewrite the steps and the list of things an agent gets wrong.
- [ ] Regenerate the adapters.

## Notes
- The folder move itself is part of TASK-0187's rename. This task rewrites what the skill says.

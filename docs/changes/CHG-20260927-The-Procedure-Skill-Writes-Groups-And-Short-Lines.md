---
type: "[[change]]"
id: CHG-20260927-The-Procedure-Skill-Writes-Groups-And-Short-Lines
title: "The release-test-procedure skill writes groups with a Start line, one short action per step and tag-only lines"
status: merged
owner: user:edwin
created: 2026-09-27
updated: 2026-09-27
source: ["[[TASK-0194-Rename-The-Walk-Procedure-Skill-And-Teach-It-The-New-Shape]]"]
commit: "project-os 8309260"
pr: ""
impacts: ["tools/skills/release-test-procedure/SKILL.md"]
platforms: []
issues: []
features: ["[[FEAT-0040-The-Release-Test-Reads-In-Short-Lines]]"]
reviewed_by: ""
review_date: ""
review_verdict: ""
related: ["[[REQ-0033-A-Section-Prints-Each-Check-As-One-Action-And-One-Expected-Line]]"]
---

# The procedure skill writes groups and short lines

## Summary

An agent that writes or rewrites a section's procedure now produces the approved shape: steps grouped under `### ` headings with one `Start:` line each, one action line of about 20 words per step, and the tags alone under it. It shortens a long Expect line in the check note rather than quoting it.

## Impact

- No screen changed: it is instruction text for an agent.

What the skill now tells an agent to do differently:

- Write setup as named items with `setup_for:`, so the page can put each under "Before you start" or "Later".
- Group steps by their start state, and write `Start:` instead of `state_for:`.
- Leave the screen name out of the action line; never quote Expect text; never cite a step number.
- Mark what cannot be done with `readiness_for:`, including `result:` where the default is wrong, with the Equipment page's checks 18 and 27 as examples.
- Keep the procedure only when `--check` passes with no warning about it, then generate the section and read it.

## Documentation Coverage (All Types Considered)

- features: not-applicable
- requirements: not-applicable
- tasks: updated (TASK-0194)
- issues: not-applicable
- tests: not-applicable (instruction text; TASK-0194 records a waiver)
- workflows: not-applicable
- decisions: not-applicable
- risks: not-applicable
- changes: new
- snapshot: updated

## Follow-ups

- [ ] your-trainer TASK-0975 rewrites the Equipment procedure with this skill.

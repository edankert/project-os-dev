---
type: "[[task]]"
id: TASK-0133
aliases: ["TASK-0133"]
title: "An issue says who reported it and what it asks"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]", "[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]"]
parent: "[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]"
effort: "Medium"
due: ""
depends: [TASK-0132]
blocks: []
related: []
tests: [TST-0015]
---

# An issue says who reported it and what it asks

## Definition of Done
- [x] The issue template and `SCHEMAS.md` carry two new fields:
  - [x] `reported_by:`, holding `user:<name>`, `review` or `agent`;
  - [x] `question:`, holding the question, its options and a recommendation.
- [x] The template's first line asks for what a user would notice, in plain words.
- [x] `issue-intake/SKILL.md` sets the filing bar and the plain first line. It says a question goes to the owner in chat, and that an issue may wait on the owner only with a `question:`.
- [x] The validator warns on an open issue created on or after the cutover date with no `reported_by:` (`ISSUE-REPORTER`).
- [x] The validator warns on an open issue that says it waits on the owner but has no `question:` (`ISSUE-QUESTION`).
- [x] Both warnings have fixtures in the validator's tests. Issues created before the cutover are not flagged, so the fleet does not light up overnight; FEAT-0036 brings the old ones up to the rule.

## Done, 2026-09-18
Implemented in `3c979ee`. The issue template and `SCHEMAS.md` carry `reported_by:` and `question:`, and the title and first line ask for what a user would notice. The intake skill applies the filing bar first. The validator adds ISSUE-REPORTER (warns until 2026-10-19, then errors) and ISSUE-QUESTION (warns until 2026-12-17), both only for issues created from 2026-09-19. Run over project-os-dev, your-trainer and project-os-cockpit on 2026-09-18, neither fires, as intended.

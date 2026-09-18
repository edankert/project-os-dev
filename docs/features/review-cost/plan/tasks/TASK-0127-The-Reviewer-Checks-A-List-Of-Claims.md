---
type: "[[task]]"
id: TASK-0127
aliases: ["TASK-0127"]
title: "The reviewer checks a list of claims"
status: done
phase: "[[PHASE-0007]]"
owner: user:edwin
created: 2026-09-18
updated: 2026-09-18
source: ["[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"]
parent: "[[FEAT-0034-A-Review-Costs-What-The-Change-Is-Worth]]"
effort: "Medium"
due: ""
depends: [TASK-0126]
blocks: [TASK-0128, TASK-0130]
related: ["[[ADR-0047-A-Finding-Is-Fixed-In-The-Feature-That-Caused-It]]", "[[ADR-0013-Independence-Is-Clean-Context]]"]
tests: [TST-0006, TST-0014]
---

# The reviewer checks a list of claims

## Definition of Done
- [x] `tools/skills/independent-review/SKILL.md` in `~/Dev/repos/project-os` states the procedure once:
  1. Read the packet. It is the scope.
  2. List the claims: each acceptance criterion, each "test X guards this", and up to three from the author.
  3. Give each claim *holds*, *refuted* (with the command and its output) or *not checked*.
  4. Break at most three guards the feature depends on most, and run the targeted tests after each.
  5. Add at most five other observations, with no digging.
  6. Stop when every claim has a verdict.
- [x] Step 3 of the current skill ("ask for every finding") is replaced. ADR-0028's rule that the author never answers the reviewer in turns is kept.
- [x] The skill states the test rule: run only the tests covering the changed code, and never re-run the full suite, because the packet already carries its result.
- [x] The skill states the context rules:
  - [x] read the line ranges around each changed section, not whole files;
  - [x] keep only the tail of test output;
  - [x] make independent reads together in one turn.
- [x] The skill gives a report format: a claims table, the observations, and the verdict. The reviewer writes the verdict into the feature note's frontmatter, and nothing else in the notes.
- [x] The reviewer agent emitted by `generate-adapters.py` carries `effort: medium` and `maxTurns: 100`. Its body points to the skill instead of restating it.
- [x] Checks that belong to the validator or the docs audit (change-note impact lists, parity matrices, snapshot agreement) are listed as out of scope for the reviewer.
- [x] `generate-adapters.py --check` passes.

## Steps
- [x] Rewrite the skill's Checklist and "What NOT to do" sections.
- [x] Update the agent source in the generator and regenerate.
- [x] Add a short author-prompt template to the skill: packet path, feature ID, up to three claims. Nothing else.

## Notes
- `effort` and `maxTurns` are documented subagent frontmatter fields (Claude Code docs, sub-agents page, checked 2026-09-18). A subagent that hits `maxTurns` stops without a report, so the real limit is TASK-0128's hook.

## Done, 2026-09-18
Implemented in `~/Dev/repos/project-os` `3c979ee` and amended in `db98f46` after the measured comparison in [[TASK-0130-Re-Run-The-FEAT-0107-Review-The-New-Way|TASK-0130]]. The skill now states the procedure once:
- the packet is the scope;
- claims come from the criteria, the note's Scope, the linked tests and up to three author claims;
- a claim with several parts gets a verdict per part, and a *holds* cites its evidence;
- at most three guards are broken, and only targeted tests are run;
- **two reviewers run at once on one packet, and the author combines their reports** (Edwin's decision, 2026-09-18). Reviewers write nothing in the notes.

The agent runs at `effort: medium`, with `maxTurns: 100` as a backstop. Synced to your-trainer `5b317fb4` and project-os-cockpit `f120f35`.

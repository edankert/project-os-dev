---
type: "[[task]]"
id: TASK-0127
aliases: ["TASK-0127"]
title: "The reviewer checks a list of claims"
status: backlog
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
tests: []
---

# The reviewer checks a list of claims

## Definition of Done
- [ ] `tools/skills/independent-review/SKILL.md` in `~/Dev/repos/project-os` states the procedure once:
  1. Read the packet. It is the scope.
  2. List the claims: each acceptance criterion, each "test X guards this", and up to three from the author.
  3. Give each claim *holds*, *refuted* (with the command and its output) or *not checked*.
  4. Break at most three guards the feature depends on most, and run the targeted tests after each.
  5. Add at most five other observations, with no digging.
  6. Stop when every claim has a verdict.
- [ ] Step 3 of the current skill ("ask for every finding") is replaced. ADR-0028's rule that the author never answers the reviewer in turns is kept.
- [ ] The skill states the test rule: run only the tests covering the changed code, and never re-run the full suite, because the packet already carries its result.
- [ ] The skill states the context rules:
  - [ ] read the line ranges around each changed section, not whole files;
  - [ ] keep only the tail of test output;
  - [ ] make independent reads together in one turn.
- [ ] The skill gives a report format: a claims table, the observations, and the verdict. The reviewer writes the verdict into the feature note's frontmatter, and nothing else in the notes.
- [ ] The reviewer agent emitted by `generate-adapters.py` carries `effort: medium` and `maxTurns: 100`. Its body points to the skill instead of restating it.
- [ ] Checks that belong to the validator or the docs audit (change-note impact lists, parity matrices, snapshot agreement) are listed as out of scope for the reviewer.
- [ ] `generate-adapters.py --check` passes.

## Steps
- [ ] Rewrite the skill's Checklist and "What NOT to do" sections.
- [ ] Update the agent source in the generator and regenerate.
- [ ] Add a short author-prompt template to the skill: packet path, feature ID, up to three claims. Nothing else.

## Notes
- `effort` and `maxTurns` are documented subagent frontmatter fields (Claude Code docs, sub-agents page, checked 2026-09-18). A subagent that hits `maxTurns` stops without a report, so the real limit is TASK-0128's hook.

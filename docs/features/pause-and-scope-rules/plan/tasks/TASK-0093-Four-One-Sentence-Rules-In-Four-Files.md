---
type: "[[task]]"
id: TASK-0093
aliases: ["TASK-0093"]
title: "Four one-sentence rules: QUALITY, HANDOFF, MARKDOWN, skills README"
status: backlog
phase: "[[PHASE-0003]]"
owner: user:edwin
created: 2026-09-03
updated: 2026-09-03
source: ["[[Prompting-Guide-Review-2026-09-03]] findings 5.3, 7.1, 7.2, 7.4"]
parent: "[[FEAT-0024-One-Pause-Rule-And-The-Scope-Rules-The-Guides-State]]"
effort: S
depends: []
related: ["[[ADR-0017-Claims-About-Working-Software-Are-Derived]]"]
tests: []
---

# Four one-sentence rules: QUALITY, HANDOFF, MARKDOWN, skills README

## Definition of Done
- [ ] `QUALITY.md` "Verification expectations (generic)" says to audit each progress claim against a tool result from this session; report a failing test with its output, and say when a step was skipped (finding 5.3).
- [ ] `HANDOFF.md` "Before stopping work" gains two items: approaches tried and set aside with the reason, and constraints or user decisions in the user's exact words (finding 7.1).
- [ ] `MARKDOWN.md` says to change the lines that change, because rewriting a note to make a small edit drops frontmatter nobody meant to touch — review fields, waivers, `origin:` (finding 7.2).
- [ ] `tools/skills/README.md` says the numbers are for reference and steps that do not depend on each other can be done in one go (finding 7.4).

## Steps
- [ ] Four edits, four files, one commit.
- [ ] Decide where a road not taken lives in the task note; "Next Actions" is named for actions.

## Notes

5.3 is the rule project-os already pays for on the record — criteria ticked only with an evidence pointer, "not landed until CI is green" — applied to the one surface it does not cover, the message the user reads.

7.2 matters here more than in most repos: a note carries `reviewed_by`, `review_verdict`, `verification_waiver` and `origin:`, and a rewrite drops them without failing anything.

---
type: "[[issue]]"
id: ISS-0107
aliases: ["ISS-0107"]
title: "Two of the template's own tests fail since the fix-what-you-find rule: LIFECYCLE.md is over its word budget, and the filing bar's \"40 tool calls\" reads as a restated review budget"
status: open
phase: ""
owner: user:edwin
created: 2026-10-14
updated: 2026-10-14
source: ["Found 2026-10-14 by the session building TASK-0199 in the template, running every tools/scripts/test-*.sh before committing; both fail on a clean checkout of project-os 30e2486"]
reported_by: agent
question: "Which to do for each: cut words from LIFECYCLE.md or raise REQ-0026's 1,000-word budget; and reword QUALITY.md's filing bar or narrow test-review-budget.sh?"
severity: medium
component: "instructions"
parent: ""
related: ["[[TASK-0197]]", "[[FEAT-0035-A-Finding-Is-Fixed-Before-It-Is-Filed]]", "[[REQ-0026]]"]
tests: []
---

# Two template tests fail since the fix-what-you-find rule

## Problem

The template's CI runs every `tools/scripts/test-*.sh` in the template repository, and two of them fail on project-os `30e2486`, the commit of [[TASK-0197]] ("A defect you find is one you fix"). Both failures came in with that commit. Its CI run will be red for this reason, not for anything in the change it made.

1. **`test-word-budgets.sh`: `LIFECYCLE.md` is 1,031 words against a budget of under 1,000**, and the generated `.cursor/rules/lifecycle.mdc` is 1,051 against under 1,040. TASK-0197 added a 29-word sentence to "Scope of a change". The budget is [[REQ-0026]]'s, amended 2026-09-03.
2. **`test-review-budget.sh`, "no other file restates the budget"**: the check looks for the literal text `40 tool calls` anywhere outside the review skill. TASK-0197's filing bar in `QUALITY.md` line 56 says a found defect stays open when the fix "needs more than about 40 tool calls". That is a different rule which happens to use the same number. The check reads it as the review budget restated.

## Why it is filed rather than fixed

QUALITY.md's rule allows a found defect to stay open when the fix needs an owner decision, and both do:

- **Getting `LIFECYCLE.md` under budget means cutting 32 words of rule text** that every session in every repo loads, or raising the budget. Condensing "Scope of a change" alone, keeping every rule and pointing at `QUALITY.md` once, saves 9 words. The finding session tried that and reverted it.
- **The false match can be fixed either side**: reword the filing bar (for example "about forty tool calls"), or make the test match only the review budget's own wording. The first reads like editing prose to satisfy a test; the second weakens a check that exists because a figure once sat in five files.

## Expected

Both scripts pass in the template, and the template's CI goes green.

## Next Actions

- [ ] Edwin decides each question in the frontmatter.
- [ ] Apply the decisions in the template, run `tools/scripts/test-word-budgets.sh` and `tools/scripts/test-review-budget.sh`, and set this issue to `fixed`.

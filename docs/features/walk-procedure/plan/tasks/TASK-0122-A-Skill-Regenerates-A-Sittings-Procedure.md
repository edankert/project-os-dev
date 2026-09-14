---
type: "[[task]]"
id: TASK-0122
aliases: ["TASK-0122"]
title: "A skill regenerates a sitting's procedure with an LLM when its owed checks change, reruns the validator, and keeps the result only when it passes; release-prep points at it"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 6", "Edwin, 2026-09-14: 'an LLM can always be integrated in these solutions'"]
parent: "[[FEAT-0031-A-Sitting-Is-Walked-From-A-Written-Procedure]]"
effort: M
due: ""
depends: ["[[TASK-0120-The-Procedure-Validator]]"]
blocks: ["[[TASK-0123-Downstream-To-The-Consumers-And-The-Cockpit]]"]
related: ["[[TASK-0121-The-Sheet-Prints-The-Owed-Parts-Of-A-Procedure]]"]
tests: []
---

# A skill regenerates a sitting's procedure

## What

When the validator reports that a sitting's procedure no longer covers its owed parts, an agent follows one skill to rewrite it. The skill gives the LLM the sitting's state and bench from WALK.md, each check's Setup, Steps and Expect, and the surface notes. It asks for setup once, a surface on every step, one shared step where checks share an action, and expectation lines that quote each check's Expect text word for word with ASCII tags. Where a check's steps are unheaded prose, the agent numbers them in the check note first, then cites them. It reruns the validator and keeps the procedure only when it passes.

## Definition of Done

- [x] `tools/skills/walk-procedure/SKILL.md` exists (name to match the template's skill list), with inputs, outputs and a checklist, linking TESTING.md "The walk" and restating none of it.
- [x] The checklist says what the agent must not do: invent a step no check has, drop an owed part, or paraphrase an Expect so it asserts something different. It says what to do when two checks' setups conflict: split the sitting in WALK.md, which is the owner's file, and ask.
- [x] `release-prep` and `release-verification` skills gain one step: run the validator for each sitting, and regenerate any procedure it fails before handing over the sheet.
- [x] The adapters are regenerated (`tools/skills/adapter-sync/SKILL.md`) so the new skill reaches `.claude/` and the other tools.

## Notes

- The LLM runs in the agent session. The skill adds no model call to any script.

## What the skill says, and what it refuses

`tools/skills/walk-procedure/SKILL.md`, nine checklist steps and five refusals. The steps that are not obvious:

- **Step 2 numbers a prose-only check's steps in its own note before citing it.** On your-trainer that is 21 of 39 owed checks, so it is the common case rather than a footnote. Editing the check is expected: TESTING.md already says a check is brought to its four headings when somebody walks it.
- **Step 5 merges at the step, not at the expectation.** One action, then one expectation line per check that expects something from it. A line may carry several tags only where every check it names words the expectation identically, because the validator compares the quote against each of them.
- **Step 7 keeps the procedure only when `--check` passes.** An unchecked procedure on a walk sheet is a list of things to do that may not be the things the release owes.

The refusals are the failure modes an LLM writing from check notes actually has: inventing a step no check asks for, dropping an owed part that is awkward to reach, paraphrasing an `## Expect` line (fix the check's wording in its note, then quote the fixed line), widening the sitting to make the script work, and writing a duration.

**Two checks in one sitting whose setups conflict is the owner's call.** `WALK.md` is Edwin's file and splitting a sitting changes the order a release is walked in, so the skill says name the two checks and ask rather than splitting it ([[../../../../tools/instructions/LIFECYCLE.md|LIFECYCLE.md]], "When to pause for the user").

`release-prep` gained step 2a, before the sheet is generated; `release-verification` gained step 3a, before the matrix. Both say a refused procedure is not a release blocker on its own — the sheet falls back to rows — so neither invents a gate the ADR did not ask for.

The skill is registered in `tools/skills/README.md` and the template's `CLAUDE.md`, and the adapters were regenerated: `.claude/skills/walk-procedure/SKILL.md` (tracked, or `generate-adapters --check` reports it UNTRACKED forever) and `.cursor/rules/skills.mdc`.

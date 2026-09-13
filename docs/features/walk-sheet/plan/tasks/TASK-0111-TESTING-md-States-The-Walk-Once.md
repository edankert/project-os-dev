---
type: "[[task]]"
id: TASK-0111
aliases: ["TASK-0111"]
title: "TESTING.md gains 'The walk', the eight rules stated once; SCHEMAS.md and the test template gain the optional after: field; the glossary gains the four terms"
status: done
phase: "[[PHASE-0004]]"
owner: user:edwin
created: 2026-09-13
updated: 2026-09-13
source: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[ADR-0024-A-Normative-Rule-Is-Stated-Once]]"]
parent: "[[FEAT-0029-The-Walk-Sheet]]"
effort: M
due: ""
depends: []
blocks: ["[[TASK-0112-The-WALK-md-Template]]", "[[TASK-0113-The-Generator-And-Its-Fixture-Test]]", "[[TASK-0114-The-Skills-And-Note-Templates-Hand-Over-The-Sheet]]"]
related: ["[[REQ-0027-Every-Normative-Rule-Is-Stated-Once]]", "[[REQ-0028-A-Release-Presents-Its-Owed-Checks-As-A-Walk]]"]
tests: []
---

# The normative text, once

## What

`tools/instructions/TESTING.md` in the template gains one section, "The walk", carrying the eight rules ADR-0029 decides. It is the only place they are stated. The WALK.md template, the generator's docstring, the skill steps and the cockpit's page all link to this section and restate none of it (ADR-0024, REQ-0027). ADR-0029's own Decision section then defers to it.

## Definition of Done

- [x] `~/Dev/repos/project-os/tools/instructions/TESTING.md` has a section "The walk" after "Release gating". It defines the four terms in one line each (walk sheet, sitting, survey, walk order) and states the eight rules from ADR-0029's Decision, each as one short paragraph with its reason. It names the generator by path and WALK.md by path.
- [x] The section says, in one sentence each, why the two earlier attempts are not repeated: no burden inferred from prose and no time estimates (the cockpit's TASK-0449), and no new close-out obligation (the cockpit's ADR-0036).
- [x] `~/Dev/repos/project-os/docs/__templates__/SCHEMAS.md` documents `after: []` on a `[[test]]` at `level: acceptance`: optional, a list of check ids that should have passed before this one is walked, read by the generator for ordering inside a sitting, gating nothing.
- [x] `~/Dev/repos/project-os/docs/__templates__/test.md` carries `after: []` in the acceptance-only block with a one-line comment linking to the section.
- [x] `~/Dev/repos/project-os/docs/GLOSSARY.md` (or the consumer-facing glossary the template ships, whichever exists) gains walk sheet, sitting, survey and walk order, one line each, linking to the section.
- [x] `tools/instructions/TAXONOMY.md` is unchanged: the walk adds no status, mark or kind value.
- [x] `bash tools/scripts/validate-docs.sh` is clean and the docs-audit drift check finds the rules stated in one file.

## Steps

- [x] Draft the section from ADR-0029's eight rules. Keep the rule numbering so the ADR, the skills and the cockpit can cite "TESTING.md, The walk, rule 3".
- [x] Add `after:` to SCHEMAS.md beside `area:` in the acceptance fields, and to test.md.
- [x] Add the glossary lines.
- [x] Amend ADR-0029's Decision opening line to say the section is now the normative text, and leave the eight rules there as the decision record.
- [x] Validate.

## Notes

- Write the section for someone who has never seen a sheet. Name what the walker sees ("the sheet opens with the screens the release changed") before naming the mechanism ("derived from the ledger's invalidation events").
- The section must not say how many minutes a sitting takes or suggest a way to estimate it. Counts of rows are the only quantity a sheet carries.

## Evidence

- `~/Dev/repos/project-os/tools/instructions/TESTING.md` gains "The walk" after "Release gating": what a walker sees first, the four terms one line each, then ADR-0029's eight rules in their original numbering so the ADR, the skills and the cockpit can cite "TESTING.md, The walk, rule 3". Rule 3 carries the reason the inferred-burden attempt is not repeated; rule 8 carries both guard rails, no schedule and no new close-out obligation.
- `docs/__templates__/SCHEMAS.md` documents `after:` beside `area:` in the acceptance fields: optional, a list of check ids, read by the generator for ordering inside a sitting, gating nothing.
- `docs/__templates__/test.md` carries `after: []` in the acceptance-only frontmatter block with a one-line comment pointing at rule 4.
- `docs/GLOSSARY.md` gains walk, walk sheet, sitting, survey and walk order, one line each, pointing at the section.
- `tools/instructions/TAXONOMY.md` is unchanged: the walk adds no status, mark or kind value.
- ADR-0029's Decision opening now names TESTING.md as the normative text and keeps the eight rules as the decision record.
- `bash tools/scripts/validate-docs.sh` is OK in the template.

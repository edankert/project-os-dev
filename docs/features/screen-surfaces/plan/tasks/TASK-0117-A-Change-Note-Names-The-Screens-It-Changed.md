---
type: "[[task]]"
id: TASK-0117
aliases: ["TASK-0117"]
title: "change.md's Impact section lists SUR-* ids with one rider-facing sentence each, and the change-note and close-out skills ask an LLM to draft it from the diff"
status: done
phase: "[[PHASE-0005]]"
owner: user:edwin
created: 2026-09-14
updated: 2026-09-14
source: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]] decision 2"]
parent: "[[FEAT-0030-A-Surface-Is-A-Screen-And-A-Change-Names-Its-Screens]]"
effort: M
due: ""
depends: ["[[TASK-0116-TAXONOMY-States-What-A-Surface-Is]]"]
blocks: ["[[TASK-0118-The-Survey-Comes-From-Change-Notes-And-Captures]]"]
related: ["[[ADR-0029-The-Walk-Sheet-Is-Derived-And-Its-Order-Is-Authored-Once]]", "[[REQ-0029-A-Release-Walk-Reads-As-A-Script]]"]
tests: []
---

# A change note names the screens it changed

## What

Every change note says which screens it changed and, for each, one sentence a rider would understand. Example: "SUR-00xx Equipment panel: a third and fourth slot appear, for a power meter and a cadence sensor." The survey reads nothing else.

The template's `change.md` Impact section today says "affected areas/flows/workflows" in free text. Its optional "Acceptance checks reopened" section names checks, not screens.

## Definition of Done

- [x] `docs/__templates__/change.md`'s Impact section is a list of `[[SUR-####]]` links, each followed by one sentence written for a rider. A change with no screen writes "No screen changed" and why.
- [x] `SCHEMAS.md`'s `change.md` entry describes the shape a parser reads, including the "No screen changed" line.
- [x] `tools/skills/change-note/SKILL.md` and `tools/skills/close-out/SKILL.md` each gain one step: ask an LLM to draft the Impact list from the diff and the repo's surface notes, then check that every id resolves. The rule is stated in TESTING.md (TASK-0118) and the skills link there.
- [x] Decide what happens to the optional "Acceptance checks reopened" section: kept as prose for the ledger's invalidation reason, or removed. Record the answer in the task.
- [x] Decide whether the validator refuses an Impact line naming a `SUR-*` that does not exist. If yes, it errors from day one only when no consumer has a violation (ADR-0011); otherwise it lands with a dated promotion.

## Steps

- [x] Draft the template text and the two skill steps.
- [x] Measure on your-trainer: how many of the 12 change notes since the v2.1.8 tag already have an Impact section, and in what shape. Record the count.

## Notes

- This is a new close-out obligation. ADR-0029 rule 8 and project-os-cockpit ADR-0036 both argued against one. ADR-0045 records why this one is different: the survey's one input is recorded nowhere else. Edwin accepted ADR-0045 decision 2 on 2026-09-14, so this task goes ahead.

## The two decisions this task owed

**1. `## Acceptance checks reopened` is removed from `change.md`.** Nothing reads it once rule 2 stops quoting it, and the reason a check was reopened is already the `reason:` on the ledger's invalidation event, which the ledger refuses to accept without. Two places to write "what this change reopened" is the drift ADR-0032 spent a decision removing. Old change notes keep the section; nothing parses it. `SCHEMAS.md` records the removal with that reason rather than dropping the heading silently.

**2. An Impact line naming a `SUR-*` that no note carries is reported, not refused.** Three reasons, and the third is the one that decided it:

- `validate-docs.py` resolves links in **frontmatter** only. A rule reading one section of one note type's body would be the only body-link rule in the validator.
- The consequence shows on the walk sheet — a screen nobody can open — so the message belongs in front of the walker. The survey prints the id with "No surface note carries this id", and `walk-sheet.py --check` reports it.
- ADR-0011 says a check lands as an error only when no consumer violates it. No consumer has written an Impact list yet, so the violation count is unknown rather than zero, and a sheet line costs nothing while a fleet-wide commit block costs a day.

## What the measurement found

**Twelve change notes in your-trainer since the v2.1.8 tag. Four have an `## Impact` section. None of the four names a screen.** Three list code paths under `**New:**` / `**Changed:**` / `**Retired:**` headings, and the fourth describes documents. Measured 2026-09-14 with `git diff --diff-filter=A --name-only v2.1.8..HEAD -- docs/changes`.

That settles the argument ADR-0045 decision 2 was making. The survey's one input is not recorded anywhere today, in any shape, on the corpus that has the problem — so this is a new obligation rather than a new reading of an old one, and nothing is lost by switching rule 2 over.

One thing the measurement also caught, which is now a rule: **an Impact line that mentions a screen id in passing is not a line about that screen.** `CHG-20260913b` reads "intervals.icu got its own, SUR-0016" inside a sentence about `area:` values, and an unanchored search read it as a screen the release changed. The parser now requires the id to start the list item, which is what `SCHEMAS.md` describes, and the fixture carries that exact sentence shape.

---
type: "[[issue]]"
id: ISS-0088
aliases: ["ISS-0088"]
title: "Editing an acceptance check breaks every walk procedure that quotes its expectation"
status: fixed
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: "2026-09-26"
source: ["your-trainer session your-trainer-b8, on Edwin's instruction (2026-09-26: 'review where most of the time went', then 'Make it so')"]
reported_by: review
question: ""
severity: medium
component: "tools/scripts/walk-sheet.py; tools/instructions/TESTING.md rule 9"
parent: ""
related: ["[[ADR-0045-A-Sitting-Is-Walked-From-A-Written-Procedure]]", "[[ADR-0046-Declared-Preparation-Survives-Walk-Filtering]]"]
tasks: ["[[TASK-0175]]"]
tests: ["[[TST-0033-A-Reworded-Check-Breaks-No-Tag-Only-Walk]]"]
---

# Editing an acceptance check breaks every walk procedure that quotes its expectation

## Problem

`walk-sheet.py --check` requires a procedure step's expectation line to match the check's `## Expect` text word for word (TESTING.md rule 9). So rewriting a check breaks every walk that quotes it, and the fix is a second edit in each procedure.

## Evidence

- In your-trainer, rewriting TST-0480 and TST-0626 broke two walk files: `pro-route-workouts.md` step 133 and `the-paywall-and-the-upgrade-to-pro.md` step 46. That surfaced a third check, TST-0483, which also needed changing.

## Why the rule exists

The quote is deliberate. ADR-0045 (and project-os-cockpit ADR-0041) made a tick recorded from a procedure step stand as a verdict on the check itself, and that holds only if the walker saw the check's own words. Any change must keep that property.

## Proposal (from the report)

Walks cite the step (`TST-0480.1`) and the walk page renders the check's current text. Alternatively, the step's expectation text is generated from the check.

## Fixed, 2026-09-26

TASK-0175 and ADR-0049, as the report proposed. A walk step may cite a check's step by its tag alone, and the sheet and the cockpit print the check's current Expect words for it, so rewording a check breaks no such walk. Quoted lines keep working. `walk-tags.py` rewrites them as tags where that prints the same words, and `--refresh` re-quotes one whose check was reworded. The tick still stands as a verdict on the check's own words. TST-0033 tests it.

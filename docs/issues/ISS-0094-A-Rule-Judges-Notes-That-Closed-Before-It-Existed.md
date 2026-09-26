---
type: "[[issue]]"
id: ISS-0094
aliases: ["ISS-0094"]
title: "A validator rule added today warns about notes that were finished before the rule existed"
status: open
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: medium
component: "tools/scripts/validate-docs.py"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: []
---

# A validator rule added today warns about notes that were finished before the rule existed

## Problem

About 315 of your-trainer's 1,139 validator findings come from rules introduced after the notes they judge had closed: VERIFY-ACCEPTANCE 130, REQ-BOXES 118, FEATURE-REQ 30, FEATURE-UNCOVERED 26, REVIEW-STALE 11. Nobody will go back and fix a closed note to satisfy a later rule, so every run prints them and every reader learns to skim past them.

## Expected

Each content rule carries the date it arrived (the validator already dates each rule in `PROMOTIONS`). A note that was already finished before that date is not judged by it. Structural checks (links resolve, ids unique, frontmatter parses, counters) still cover every note. A `--changed` view prints only the findings about files changed since HEAD, with a count for the rest (the smaller step already in ISS-0091).

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.

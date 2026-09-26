---
type: "[[issue]]"
id: ISS-0098
aliases: ["ISS-0098"]
title: "Notes grow dated history sections that every later reader has to get through"
status: open
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: 2026-09-26
source: ["ADR-0048 (proposed), from Edwin's question on 2026-09-26 and the your-trainer time review"]
reported_by: agent
question: ""
severity: low
component: "tools/instructions/WRITING.md; note templates"
parent: ""
related: ["[[ADR-0048-Old-Tickets-Are-Records-And-Every-Fact-Is-Written-Once]]"]
tests: []
---

# Notes grow dated history sections that every later reader has to get through

## Problem

Notes accumulate dated narrative: TASK-0125 has four dated sections of history, and your-trainer FEAT-0122's "Implementation evidence, 2026-09-16" runs to about forty paragraphs. Every later agent reads all of it to find the current state.

## Expected

A note holds its current state, as REQ-0026 requires of instruction files. The history of how it got there goes into change notes and commit messages. A standing record keeps a short dated decision log at most.

## Decided

ADR-0048 was accepted with option 4 on 2026-09-26: tickets freeze at release, a tool writes the supersession back-pointer into the old note, and editing a frozen ticket is a warning.

---
type: "[[issue]]"
id: ISS-0092
aliases: ["ISS-0092"]
title: "A note that depends on a project rule restates it instead of linking to it by name"
status: "open"
phase: "[[PHASE-0009]]"
owner: unassigned
created: 2026-09-26
updated: "2026-09-26"
source: ["your-trainer session your-trainer-b8, on Edwin's instruction (2026-09-26: 'review where most of the time went', then 'Make it so')"]
reported_by: review
question: ""
severity: low
component: "tools/instructions/WRITING.md"
parent: ""
related: []
tests: []
---

# A note that depends on a project rule restates it instead of linking to it by name

## Problem

Notes that depend on a project rule copy the rule's wording instead of linking to where it is stated. When the rule changes, every copy is now wrong, and a search for the rule returns the copies alongside the source.

## Evidence

- your-trainer filed its own cleanup of this as its ISS-0515.

## Proposal (from the report, offered as "consider")

One line in `tools/instructions/WRITING.md`: a note that depends on a project rule links to it by name instead of restating it.
